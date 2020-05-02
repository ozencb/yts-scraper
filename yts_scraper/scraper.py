import os
import sys
import math
import json
import csv
from concurrent.futures.thread import ThreadPoolExecutor
import requests
from tqdm import tqdm
from fake_useragent import UserAgent

class Scraper:
    """
    Scraper class.

    Must be initialized with args from argparser
    """
    # Constructor
    def __init__(self, args):
        self.output = args.output
        self.genre = args.genre
        self.minimum_rating = args.rating
        self.quality = '3D' if (args.quality == '3d') else args.quality
        self.categorize = args.categorize_by
        self.sort_by = args.sort_by
        self.year_limit = args.year_limit
        self.page_arg = args.page
        self.poster = args.background
        self.imdb_id = args.imdb_id
        self.multiprocess = args.multiprocess
        self.csv_only = args.csv_only

        self.movie_count = None
        self.url = None
        self.existing_file_counter = None
        self.skip_exit_condition = None
        self.downloaded_movie_ids = None
        self.pbar = None


        # Set output directory
        if args.output:
            if not args.csv_only:
                os.makedirs(self.output, exist_ok=True)
            self.directory = os.path.join(os.path.curdir, self.output)
        else:
            if not args.csv_only:
                os.makedirs(self.categorize.title(), exist_ok=True)
            self.directory = os.path.join(os.path.curdir, self.categorize.title())


        # Args for downloading in reverse chronological order
        if args.sort_by == 'latest':
            self.sort_by = 'date_added'
            self.order_by = 'desc'
        else:
            self.order_by = 'asc'


        # YTS API has a limit of 50 entries
        self.limit = 50


    # Connect to API and extract initial data
    def __get_api_data(self):
        # Formatted URL string
        url = '''https://yts.mx/api/v2/list_movies.json?
                 quality={quality}&
                 genre={genre}&
                 minimum_rating={minimum_rating}&
                 sort_by={sort_by}&
                 order_by={order_by}&
                 limit={limit}&
                 page='''.format(
                     quality=self.quality,
                     genre=self.genre,
                     minimum_rating=self.minimum_rating,
                     sort_by=self.sort_by,
                     order_by=self.order_by,
                     limit=self.limit
                 )

        # Generate random user agent header
        try:
            user_agent = UserAgent()
            headers = {'User-Agent': user_agent.random}
        except:
            print('Error occurred during fake user agent generation.')

        # Exception handling for connection errors
        try:
            req = requests.get(url, timeout=5, verify=True, headers=headers)
            req.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print('HTTP Error:', errh)
            sys.exit(0)
        except requests.exceptions.ConnectionError as errc:
            print('Error Connecting:', errc)
            sys.exit(0)
        except requests.exceptions.Timeout as errt:
            print('Timeout Error:', errt)
            sys.exit(0)
        except requests.exceptions.RequestException as err:
            print('There was an error.', err)
            sys.exit(0)

        # Exception handling for JSON decoding errors
        try:
            data = req.json()
        except json.decoder.JSONDecodeError:
            print('Could not decode JSON')


        # Adjust movie count according to starting page
        if self.page_arg == 1:
            movie_count = data['data']['movie_count']
        else:
            movie_count = (data['data']['movie_count']) - ((self.page_arg - 1) * self.limit)

        self.movie_count = movie_count
        self.url = url

    def __initialize_download(self):
        # Used for exit/continue prompt that's triggered after 10 existing files
        self.existing_file_counter = 0
        self.skip_exit_condition = False

        # YTS API sometimes returns duplicate objects and
        # the script tries to download the movie more than once.
        # IDs of downloaded movie is stored in this array
        # to check if it's been downloaded before
        self.downloaded_movie_ids = []

        # Calculate page count and make sure that it doesn't
        # get the value of 1 to prevent range(1, 1)
        if math.trunc(self.movie_count / self.limit) + 1 == 1:
            page_count = 2
        else:
            page_count = math.trunc(self.movie_count / self.limit) + 1

        range_ = range(int(self.page_arg), page_count)


        print('Initializing download with these parameters:\n')
        print('Directory:\t{}\nQuality:\t{}\nMovie Genre:\t{}\nMinimum Rating:\t{}\nCategorization:\t{}\nMinimum Year:\t{}\nStarting page:\t{}\nMovie posters:\t{}\nAppend IMDb ID:\t{}\nMultiprocess:\t{}\n'
              .format(
                  self.directory,
                  self.quality,
                  self.genre,
                  self.minimum_rating,
                  self.categorize,
                  self.year_limit,
                  self.page_arg,
                  str(self.poster),
                  str(self.imdb_id),
                  str(self.multiprocess)
                  )
             )

        if self.movie_count <= 0:
            print('Could not find any movies with given parameters')
            sys.exit(0)
        else:
            print('Query was successful.')
            print('Found {} movies. Download starting...\n'.format(self.movie_count))

        # Create progress bar
        self.pbar = tqdm(
            total=self.movie_count,
            position=0,
            leave=True,
            desc='Downloading',
            unit='Files'
            )

        # Multiprocess executor
        # Setting max_workers to None makes executor utilize CPU number * 5 at most
        executor = ThreadPoolExecutor(max_workers=None)

        for page in range_:
            url = '{}{}'.format(self.url, str(page))

            # Generate random user agent header
            try:
                user_agent = UserAgent()
                headers = {'User-Agent': user_agent.random}
            except:
                print('Error occurred during fake user agent generation.')

            # Send request to API
            page_response = requests.get(url, timeout=5, verify=True, headers=headers).json()

            movies = page_response['data']['movies']

            # Movies found on current page
            if not movies:
                print('Could not find any movies on this page.\n')

            if self.multiprocess:
                # Wrap tqdm around executor to update pbar with every process
                tqdm(
                    executor.map(self.__filter_torrents, movies),
                    total=self.movie_count,
                    position=0,
                    leave=True
                    )

            else:
                for movie in movies:
                    self.__filter_torrents(movie)

        self.pbar.close()
        print('Download finished.')


    # Determine which .torrent files to download
    def __filter_torrents(self, movie):
        movie_id = str(movie['id'])
        movie_rating = movie['rating']
        movie_genres = movie['genres']
        movie_name_short = movie['title']
        imdb_id = movie['imdb_code']
        year = movie['year']
        language = movie['language']
        yts_url = movie['url']

        if year < self.year_limit:
            return

        # Every torrent option for current movie
        torrents = movie['torrents']
        # Remove illegal file/directory characters
        movie_name = movie['title_long'].translate({ord(i):None for i in "'/\:*?<>|"})

        # Used to multiple download messages for multi-folder categorization
        is_download_successful = False

        if movie_id in self.downloaded_movie_ids:
            return

        # In case movie has no available torrents
        if torrents is None:
            tqdm.write('Could not find any torrents for {}. Skipping...'.format(movie_name))
            return

        bin_content_img = (requests.get(movie['large_cover_image'])).content if self.poster else None

        # Iterate through available torrent files
        for torrent in torrents:
            quality = torrent['quality']
            torrent_url = torrent['url']
            if self.categorize and self.categorize != 'rating':
                if self.quality == 'all' or self.quality == quality:
                    bin_content_tor = (requests.get(torrent['url'])).content

                    for genre in movie_genres:
                        path = self.__build_path(movie_name, movie_rating, quality, genre, imdb_id)
                        is_download_successful = self.__download_file(bin_content_tor, bin_content_img, path, movie_name, movie_id)
            else:
                if self.quality == 'all' or self.quality == quality:
                    self.__log_csv(movie_id, movie_name_short, year, language, movie_rating, quality, yts_url, torrent_url)
                    bin_content_tor = (requests.get(torrent_url)).content
                    path = self.__build_path(movie_name, movie_rating, quality, None, imdb_id)
                    is_download_successful = self.__download_file(bin_content_tor, bin_content_img, path, movie_name, movie_id)

            if is_download_successful and self.quality == 'all' or self.quality == quality:
                tqdm.write('Downloaded {} {}'.format(movie_name, quality.upper()))
                self.pbar.update()


    # Creates a file path for each download
    def __build_path(self, movie_name, rating, quality, movie_genre, imdb_id):
        if self.csv_only:
            return

        directory = self.directory

        if self.categorize == 'rating':
            directory += '/' + str(math.trunc(rating)) + '+'
        elif self.categorize == 'genre':
            directory += '/' + str(movie_genre)
        elif self.categorize == 'rating-genre':
            directory += '/' + str(math.trunc(rating)) + '+/' + movie_genre
        elif self.categorize == 'genre-rating':
            directory += '/' + str(movie_genre) + '/' + str(math.trunc(rating)) + '+'

        if self.poster:
            directory += '/' + movie_name

        os.makedirs(directory, exist_ok=True)

        if self.imdb_id:
            filename = '{} {} - {}'.format(movie_name, quality, imdb_id)
        else:
            filename = '{} {}'.format(movie_name, quality)

        path = os.path.join(directory, filename)
        return path

    # Write binary content to .torrent file
    def __download_file(self, bin_content_tor, bin_content_img, path, movie_name, movie_id):
        if self.csv_only:
            return

        if self.existing_file_counter > 10 and not self.skip_exit_condition:
            self.__prompt_existing_files()

        if os.path.isfile(path):
            tqdm.write('{}: File already exists. Skipping...'.format(movie_name))
            self.existing_file_counter += 1
            return False

        with open(path + '.torrent', 'wb') as torrent:
            torrent.write(bin_content_tor)
        if self.poster:
            with open(path + '.jpg', 'wb') as torrent:
                torrent.write(bin_content_img)

        self.downloaded_movie_ids.append(movie_id)
        self.existing_file_counter = 0
        return True

    def __log_csv(self, id, name, year, language, rating, quality, yts_url, torrent_url):
        path = os.path.join(os.path.curdir, 'YTS-Scraper.csv')
        csv_exists = os.path.isfile(path)

        with open(path, mode='a') as csv_file:
            headers = ['YTS ID', 'Movie Title', 'Year', 'Language', 'Rating', 'Quality', 'YTS URL', 'Torrent URL']
            writer = csv.DictWriter(csv_file, delimiter=',', lineterminator='\n', quotechar='"', quoting=csv.QUOTE_ALL, fieldnames=headers)

            if not csv_exists:
                writer.writeheader()

            writer.writerow({'YTS ID': id,
                             'Movie Title': name,
                             'Year': year,
                             'Language': language,
                             'Rating': rating,
                             'Quality': quality,
                             'YTS URL': yts_url,
                             'Torrent URL': torrent_url
                            })



    # Is triggered when the script hits 10 consecutive existing files
    def __prompt_existing_files(self):
        tqdm.write('Found 10 existing files in a row. Do you want to keep downloading? Y/N')
        exit_answer = input()

        if exit_answer.lower() == 'n':
            tqdm.write('Exiting...')
            sys.exit(0)
        elif exit_answer.lower() == 'y':
            tqdm.write('Continuing...')
            self.existing_file_counter = 0
            self.skip_exit_condition = True
        else:
            tqdm.write('Invalid input. Enter "Y" or "N".')

    def download(self):
        self.__get_api_data()
        self.__initialize_download()
