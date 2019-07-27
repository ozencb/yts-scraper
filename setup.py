from setuptools import setup, find_packages

setup(  name="YTS Scraper",
        version="0.1",
        packages=find_packages(),
        install_requires=[  'requests',
                            'argparse'],
        entry_points={'console_scripts': ['yts-scraper = src.scraper:main']},
        author="Ozencb",
        description="A command-line tool to for downloading .torrent files from YTS",
        license=open('LICENSE').read()
    )