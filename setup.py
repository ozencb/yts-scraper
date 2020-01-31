from setuptools import setup

setup(  name='YTS Scraper',
        author='Ozencb',
        version='0.2',
        description='A command-line tool to for downloading .torrent files from YTS',
        packages=['ytsscraper'],
        install_requires=['requests', 'argparse', 'progressbar2'],
        entry_points={'console_scripts': 'yts-scraper = ytsscraper.main:main'},
        license=open('LICENSE').read()
    )