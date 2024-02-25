from setuptools import setup, find_packages
import sys
import subprocess

def have_mysql_client_lib():
    "check for mysql or mariadb libraries in the same way mysqlclient checks"
    for pkg in ("mysqlclient", "mariadb", "libmariadb"):
        if subprocess.run(["pkg-config", "--exists", pkg]).returncode == 0:
            return True
    return False

requirements = [
    'pipettor',
    'biopython',
    'apsw',
    'deprecation',
    'unidecode',
    'flake8',
    'pyBigWig',
]

if have_mysql_client_lib():
    requirements.append('mysqlclient')
else:
    print("Warning: mysql or mariadb libraries are not found, mysql functionality will not be available", file=sys.stderr)



setup(
    name = 'pycbio',
    version = '1.0.0',
    license = "BSD3",
    url = 'https://github.com/diekhans/pycbio.git',
    author = 'Mark Diekhans',
    author_email = 'markd@ucsc.edu',
    description = 'My personal genomics bioinformatics toolkit',
    zip_safe = True,
    install_requires = requirements,
    package_dir = {'': 'lib'},
    packages = find_packages(where='lib'),
    scripts = [
        'bin/agpToPsl',
        'bin/bedToCdsBed',
        'bin/clusterGenesSelect',
        'bin/clusterGenesStats',
        'bin/csvToTsv',
        'bin/emblToFasta',
        'bin/gbffGenesToGenePred',
        'bin/geneCheckStats',
        'bin/genePredFlatten',
        'bin/genePredSelect',
        'bin/jsonDumpKeyStructure',
        'bin/ncbiAssemblyReportConvert',
        'bin/ncbiGbFetch',
        'bin/profStats',
        'bin/pslLoadSqlLite',
        'bin/tsvSelectById',
        'bin/vennChart',
    ]
)
