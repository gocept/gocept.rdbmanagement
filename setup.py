from setuptools import setup, find_packages

name = 'gocept.rdbmanagement'

setup(
    name=name,
    version='1.1',
    author='Michael Howitz',
    author_email='mail@gocept.com',
    url='http://pypi.python.org/pypi/' + name,
    description="""Recipe for managing RDB schemas""",
    long_description=(
        open('README.rst').read()
        + '\n\n' +
        open('CHANGES.rst').read()
    ),
    keywords="buildout rdb",
    classifiers=[
        "Framework :: Buildout",
        "Development Status :: 3 - Alpha",
        "Topic :: Database",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    packages=find_packages('.'),
    package_dir={'': '.'},
    include_package_data=True,
    zip_safe=False,
    license='ZPL 2.1',
    install_requires=[
        'zc.buildout',
        'setuptools',
        'psycopg2>=2.0.6',
        'zc.recipe.egg'],
    entry_points={
        'zc.buildout': [
            'default = %s.recipe:Recipe' % name,
        ]
    },
)
