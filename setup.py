from setuptools import setup, find_packages

setup(  name='YTS Scraper',
        author='Ozencb',
        version='0.1.1',
        description='A command-line tool to for downloading .torrent files from YTS',
        packages=find_packages(),
        install_requires=['requests', 'argparse', 'progressbar2'],
        entry_points={'console_scripts': 'yts-scraper = ytsscraper.main:main'},
        license=open('LICENSE').read()
    )