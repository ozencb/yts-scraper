from setuptools import setup, find_packages

setup(  name='YTS Scraper',
        author='Ozencb',
        version='0.1.1',
        description='A command-line tool to for downloading .torrent files from YTS',
        packages=find_packages(),
        install_requires=['requests', 'argparse', 'tqdm'],
        entry_points={'console_scripts': 'yts-scraper = yts_scraper.main:main'},
        license=open('LICENSE').read(),
        keywords=['yts', 'yify', 'scraper', 'media', 'download', 'downloader', 'torrent']
    )