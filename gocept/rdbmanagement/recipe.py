import os
import pkg_resources
import psycopg2
import psycopg2.extensions
import re
import subprocess
import zc.recipe.egg


GENERATION_TABLE = "_generation"


class Recipe(object):
    """Recipe to install and update relational database schemas.

    Configuration options:

      dbname ... database name
      host ... hostname
      schema ... setuptools resource path of schema generations
      eggs ... list of eggs that are required for the schema path

    """

    def __init__(self, buildout, name, options):
        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'], name)
        self.options = options
        self.buildout = buildout
        self.name = name
        self.schema = options['schema']
        username = options.get('user')
        self.password = options.get('password')
        self.dsn = "dbname=%(dbname)s host=%(host)s" % options
        if self.password:
            self.dsn += ' password=%s' % self.password
        self.psql_options = ["-h", options['host']]

        if username:
            self.dsn += " user=%s" % username
            self.psql_options.extend(['-U', username])

        self.psql_options.append(options['dbname'])

    def install(self):
        installed = [self.ensure_dir(self.options['location'])]
        self.configure_password()
        # Use the egg recipe to make sure we have the right eggs available
        # and activate the eggs in the `global` working set.
        egg = zc.recipe.egg.Egg(self.buildout, self.name, self.options)
        distributions, ws = egg.working_set()
        for dist in ws:
            pkg_resources.working_set.add(dist)

        # CAUTION: self.conn is everywhere expected to be a psycopg2 connection
        self.conn = psycopg2.connect(self.dsn)

        table_names = self.get_table_names()
        has_generation_table = GENERATION_TABLE in table_names
        if has_generation_table:
            table_names.remove(GENERATION_TABLE)
            current_generation = self.get_current_generation()
            assert table_names, "No application tables found."
            self.update_schema(current_generation)
        else:
            if table_names:
                self.install_generation_table()
                self.update_schema(0)
            else:
                assert pkg_resources.resource_exists(self.schema, 'init.sql'),\
                    'Initial generation script init.sql not found.'
                ret_code = self.call_psql(pkg_resources.resource_filename(
                    self.schema, 'init.sql'))

                assert ret_code == 0, 'Initial generation failed.'
                self.install_generation_table()
                self.update_generation(self.get_newest_generation())
        return installed

    def update(self):
        return self.install()

    def update_schema(self, current_generation):
        next_generation = current_generation + 1
        while pkg_resources.resource_exists(
                self.schema, 'update%s.sql' % next_generation):
            precondition_mod = 'precondition%s' % next_generation
            if pkg_resources.resource_exists(
                    self.schema, precondition_mod + ".py"):
                mod = __import__(
                    '%s.%s' % (self.schema, precondition_mod), globals(),
                    locals(), [precondition_mod])
                mod.precondition(self.conn)
                if self.conn.status == \
                        psycopg2.extensions.STATUS_IN_TRANSACTION:
                    # abort the transaction of the precondition script
                    self.conn.rollback()
            ret_code = self.call_psql(
                pkg_resources.resource_filename(
                    self.schema, 'update%s.sql' % next_generation))
            assert ret_code == 0, ('Update generation %s failed.' %
                                   next_generation)
            self.update_generation(next_generation)
            self.conn.commit()
            next_generation += 1

    def call_psql(self, filename):
        ret_code = subprocess.call(
            ["psql", "-f", filename, "-v", "ON_ERROR_STOP=true"] +
            self.psql_options)
        return ret_code

    def get_table_names(self):
        """Get a list of the tables in the database."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT c.relname as name
            FROM pg_catalog.pg_class c
                 LEFT JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r','')
                  AND n.nspname NOT IN ('pg_catalog', 'pg_toast')
                  AND pg_catalog.pg_table_is_visible(c.oid)
            ORDER BY name""")
        table_names = [x[0] for x in cur.fetchall()]
        cur.close()
        return table_names

    def get_current_generation(self):
        cur = self.conn.cursor()
        cur.execute("SELECT generation FROM %s" % GENERATION_TABLE)
        generation = cur.fetchall()
        assert len(generation) > 0, 'Empty generation table'
        assert len(generation) < 2, 'More than one row in generations table.'
        cur.close()
        return generation[0][0]

    def update_generation(self, new):
        cur = self.conn.cursor()
        cur.execute("UPDATE %s SET generation = %s" % (GENERATION_TABLE, new))
        cur.close()
        self.conn.commit()

    def get_newest_generation(self):
        max_generation = 0
        for filename in pkg_resources.resource_listdir(self.schema, '.'):
            match = re.match(r'^update([0-9]+)\.sql$', filename)
            if match is None:
                continue
            generation = int(match.groups()[0])
            if generation > max_generation:
                max_generation = generation
        return max_generation

    def install_generation_table(self):
        cur = self.conn.cursor()
        cur.execute("CREATE TABLE %s (generation INTEGER)" % GENERATION_TABLE)
        cur.execute("INSERT INTO %s VALUES (0)" % GENERATION_TABLE)
        cur.close()
        self.conn.commit()

    def configure_password(self):
        if not self.password:
            return
        path = os.path.join(self.options['location'], 'pgpass')
        with open(path, 'w') as f:
            f.write('*:*:*:*:{}'.format(self.password))
            os.environ['PGPASSFILE'] = path
            os.chmod(path, 0o600)

    def ensure_dir(self, path):
        if os.path.exists(path):
            assert os.path.isdir(path)
        else:
            os.mkdir(path)
        return path
