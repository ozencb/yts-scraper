import json
import requests
import os
import sys
import math
import string
import time
from tqdm import tqdm

class Scraper:
    # Constructor
    def __init__(self, args):
        self.args = args
        return

    
    # Argument validation
    def __validate_args(self):
        args = self.args

        # Set output directory
        if args.output:
            os.makedirs(args.output, exist_ok=True)
            directory = os.path.curdir + '/' + args.output
        else:
            os.makedirs(args.categorize_by.title(), exist_ok=True)
            directory = os.path.curdir + '/' + args.categorize_by.title()

        # Args for downloading in reverse chronological order     
        if args.sort_by == 'latest':
            self.sort_by = 'date_added'
            self.order_by = 'desc'

        self.directory = directory
        self.quality = '3D' if (args.quality == '3d') else args.quality # Check 3D arg casing 
        self.genre = args.genre
        self.minimum_rating = args.rating
        self.categorize = args.categorize_by
        self.page_arg = args.page

    # Connect to API and extract initial data
    def __get_api_data(self):
        # YTS API has a limit of 50 entries
        self.limit = 50
        
        # Formatted URL string
        url = 'https://yts.am/api/v2/list_movies.json?quality={quality}&genre={genre}&minimum_rating={minimum_rating}&sort_by={sort_by}&order_by={order_by}&limit={limit}&page='.format(
            quality = self.quality, 
            genre = self.genre, 
            minimum_rating = self.minimum_rating, 
            sort_by = self.sort_by, 
            order_by = self.order_by, 
            limit = self.limit
        ) 
        
        # Exception handling for connection errors
        try:
            r = requests.get(url,timeout=5)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print("HTTP Error:",errh)
            exit(0)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:",errc)
            exit(0)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:",errt)
            exit(0)
        except requests.exceptions.RequestException as err:
            print("There was an error.",err)
            exit(0)

        # Exception handling for JSON decoding errors
        try:
            data = r.json()
        except json.decoder.JSONDecodeError:
            print("Could not decode JSON")

        
        # Adjust movie count according to starting page
        movie_count = data['data']['movie_count'] if (self.page_arg == 1) else ((data['data']['movie_count']) - ((self.page_arg - 1) * self.limit))
        
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

        # Calculate page count and make sure that it doesn't get the value of 1 to prevent range(1, 1)
        page_count = 2 if ((math.trunc(self.movie_count / self.limit) + 1) == 1) else (math.trunc(self.movie_count / self.limit) + 1)

        range_ = range(int(self.page_arg), page_count)


        print("Initializing download with these parameters:")
        print("\t\nDirectory:\t%s\t\nQuality:\t%s\t\nMovie Genre:\t%s\t\nMinimum Rating:\t%s\t\nCategorization:\t%s\t\nStarting page:\t%s\n" % 
            (self.directory, self.quality, self.genre, self.minimum_rating, self.categorize, self.page_arg))


        if (self.movie_count <= 0):
            print("Could not find any movies with given parameters")
            exit(0)
        else:
            print("Query was successful.\nFound %d movies. Download starting...\n" % (self.movie_count))
        
        # Iterate through and tdqm progress bar
        with tqdm(total=self.movie_count, position=0, leave=True, desc='Downloading', unit='Files') as pbar:
            for page in tqdm((range_), total=self.movie_count, position=0, leave=True):
                url = self.url + str(page)

                # Send request to API
                page_response = requests.get(url).json()
                
                movies = page_response['data']['movies']
                
                # Movies found on current page
                if not movies:
                    print("Could not find any movies on this page.\n")     
                
                # Iterate through each movie on current page
                for movie in movies:
                    self.__filter_torrents(movie)
                    # Update progress bar
                    pbar.update()
                    
        tqdm.write("Download finished.")
        pbar.close()

    # Determine which .torrent files to download
    def __filter_torrents(self, movie):
        movie_id = str(movie['id'])
        movie_rating = movie['rating']
        movie_genres = movie['genres']

        # Every torrent option for current movie
        torrents = movie['torrents']
        # Remove illegal file/directory characters
        movie_name = movie['title_long'].translate({ord(i):None for i in '/\:*?"<>|'})

        # Used to multiple download messages for multi-folder categorization
        is_download_successful = False

        if movie_id in self.downloaded_movie_ids:
            return

        # In case movie has no available torrents
        if torrents == None:
            tqdm.write("Could not find any torrents for " + movie_name + ". Skipping...")
            return
        
        # Iterate through available torrent files
        for torrent in torrents:
            quality = torrent['quality']
            if self.categorize and self.categorize != 'rating':
                if self.quality == 'all' or self.quality == quality:
                    bin_content = (requests.get(torrent['url'])).content
                    
                    for genre in movie_genres:
                        path = self.__build_path(movie_name, movie_rating, quality, genre)
                        is_download_successful = self.__download_file(bin_content, path, movie_name, movie_id)
            else:
                if self.quality == 'all' or self.quality == quality:
                    bin_content = (requests.get(torrent['url'])).content
                    path = self.__build_path(movie_name, movie_rating, quality, None)
                    is_download_successful = self.__download_file(bin_content, path, movie_name, movie_id)
            
            if is_download_successful and self.quality == 'all' or self.quality == quality:
                tqdm.write("Downloaded " + movie_name + " " + quality.upper())


    # Creates a file path for each download 
    def __build_path(self, movie_name, rating, quality, movie_genre):
        directory = self.directory

        if self.categorize == 'rating':
            os.makedirs((directory + '/' + str(math.trunc(rating))) + '+', exist_ok=True)
            directory += ('/' + str(math.trunc(rating)) + '+')
        elif self.categorize == 'genre':
            os.makedirs((directory + '/' + str(movie_genre)), exist_ok=True)
            directory += ('/' + str(movie_genre))
        elif self.categorize == 'rating-genre':
            os.makedirs((directory + '/' + str(math.trunc(rating)) + '+/' + movie_genre), exist_ok=True)
            directory += ('/' + str(math.trunc(rating)) + '+/' + movie_genre)
        elif self.categorize == 'genre-rating':
            os.makedirs((directory + '/' + str(movie_genre) + '/' + str(math.trunc(rating))) + '+', exist_ok=True)
            directory += ('/' + str(movie_genre) + '/' + str(math.trunc(rating)) + '+')
        
        return os.path.join(directory, movie_name + ' ' + quality + '.torrent')

    # Write binary content to .torrent file
    def __download_file(self, bin_content, path, movie_name, movie_id):
        if self.existing_file_counter > 10 and not self.skip_exit_condition:
            self.__prompt_existing_files()

        if os.path.isfile(path):
            tqdm.write(movie_name + ": File already exists. Skipping...")
            self.existing_file_counter += 1
            return False
        else:
            with open(path, 'wb') as f:
                f.write(bin_content)
            self.downloaded_movie_ids.append(movie_id)
            self.existing_file_counter = 0
            return True
    
    # Is triggered when the script hits 10 consecutive existing files
    def __prompt_existing_files(self):
        tqdm.write("Found 10 existing files in a row. Do you want to keep downloading? Y/N")
        exit_answer = input()

        if exit_answer.lower() == 'n':
            tqdm.write("Exiting...")
            exit()
        elif exit_answer.lower() == 'y':
            tqdm.write("Continuing...")
            self.existing_file_counter = 0
            self.skip_exit_condition = True
        else:
            tqdm.write('Invalid input. Enter "Y" or "N".')

    def download(self):
        self.__validate_args()
        self.__get_api_data()
        self.__initialize_download()