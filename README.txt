====================
gocept.rdbmanagement
====================

This is a zc.buildout recipe that helps managing schema updates on relational
databases.

It currently only supports PostgreSQL.

Defining a managed database
===========================

A managed database has to be created (CREATEDB) outside of this recipe. The
recipe only takes care of initialising an existing database and upgrading the
schema subsequently.

Part definitions look like::

    [managed_db]
    recipe = gocept.rdbmanagement
    dbname = mydatabase
    eggs = projectegg
    schema = projectegg.schemadir

    host = localhost
    user = username
    password = apassword  # XXX not implemented, not given

Where

    dbname
        is the name of the PostgreSQL database to work with

    eggs
        is a list of egg requirements that should be activated before looking
        up the schema directory resource path

    schema
        is a setuptools resource path that is a `managed schema directory`

Managed schema directories
==========================

A schema directory contains a set of SQL and Python files that are used to
manage the schema for a database. A typical directory looks like this::

    $ ls schemadir
    __init__.py
    init.sql
    precondition3.py
    update1.sql
    update2.sql
    update3.sql

Notice: A managed schema directory has to be a Python package.

init.sql
--------

 * Creates the schema beginning from an empty database.

 * After init.sql the current generation will be set to the highest generation
   number as available from the update scripts. Therefore the init.sql always
   creates a current database schema and no updates will be run.

updateX.sql
-----------

 * Update scripts MUST start with a BEGIN statement and end with a COMMIT
   statement.

 * Update script X will be run from a database at generation X-1.

preconditionX.py
----------------

 * Script must contain a function called ``precondition`` which takes one
   parameter which is an open DB-API2-connection to the database.

 * Precondition script X will be run on a database at generation X-1.

 * Precondition script X has to raise an exception to indicate that the
   database MUST not be updated to generation X.
