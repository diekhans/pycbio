from setuptools import setup, find_packages

requirements = [
    'pipettor>=0.5.0',
    'numpy',
    'biopython',
    'mysqlclient',
    'apsw',
    'deprecation',
    'flake8',
    'pyBigWig',
]

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
