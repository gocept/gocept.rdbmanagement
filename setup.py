from setuptools import setup, find_packages

name = 'gocept.rdbmanagement'

setup(
    name=name,
    version='trunk',
    author='gocept',
    author_email='mail@gocept.com',
    url='https://svn.gocept.com/repos/gocept/' + name,
    description="""Recipe for managing RDB schemas
""",
    keywords = "buildout rdb",
    classifiers = ["Framework :: Buildout"],
    packages=find_packages('.'),
    package_dir = {'': '.'},
    include_package_data = True,
    zip_safe=False,
    license='ZPL',
    install_requires=[
        'zc.buildout',
        'setuptools',
        'psycopg2==2.0.5.1',
        'zc.recipe.egg'],
    entry_points={
        'zc.buildout': [
             'default = %s.recipe:Recipe' % name,
             ]
        },
    )
