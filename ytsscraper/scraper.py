import json
import requests
import os
import sys
import math
import string
import time
import progressbar

class Scraper:
    existing_file_counter = 0
    skip_exit_condition = False
    
    def __init__(self, args):
        self.args = args
        return
    
    def __validate_args(self):
        args = self.args

        if args.output:
            os.makedirs(str(args.output), exist_ok=True)
            directory = str(os.path.curdir) + "/" + str(args.output)
        elif not args.output and not args.categorize_by:
            os.makedirs('Torrents', exist_ok=True)
            directory = os.path.curdir + "/Torrents"
        elif not args.output and args.categorize_by:
            os.makedirs(str(args.categorize_by).title(), exist_ok=True)
            directory = os.path.curdir + "/" + str(args.categorize_by)
                    
        if args.sort_by == "latest":
            self.sort_by = "date_added"
            self.order = "desc"

        self.directory = directory
        self.quality = args.quality
        self.genre = args.genre
        self.minimum_rating = args.rating
        self.categorize = args.categorize_by
        self.page_arg = args.page

    def __initialize_progress_bar(self):
        progressbar.streams.wrap_stderr()
        WRAP_STDERR= True
        progressbar.streams.flush()
        
        widgets = ['[', progressbar.Timer(), ' - ', progressbar.ETA(), '] ',progressbar.Bar()]
        self.bar = progressbar.ProgressBar(max_value=self.movie_count, redirect_stdout=True, widgets=widgets)
        self.progress = 1

    def __get_movie_info(self):
        self.limit = 50
        concat_url = "https://yts.am/api/v2/list_movies.json?" + "quality=" + self.quality + "&genre=" + self.genre + "&minimum_rating=" + self.minimum_rating + "&sort_by=" + self.sort_by + "&order_by=" + self.order + "&limit=" + str(self.limit) + "&page="
        
        try:
            data = requests.get(concat_url).json()
        except json.decoder.JSONDecodeError:
            print("Could not decode JSON")

        if data["status"] != "ok" or not data:
            print("Could not get a response.\nExiting...")
            exit(0)
        
        self.movie_count = data["data"]["movie_count"]
        self.concat_url = concat_url
           
    def __initialize_download(self):
        categorize = self.categorize
        page_start = int(self.page_arg)
        movie_count = self.movie_count
        url = self.concat_url
        page_count = math.trunc(movie_count / self.limit) + 1
        counter = 0
        movie_counter = 0

        print("Initializing download with these parameters:")
        print("\t\nDirectory:\t%s\t\nQuality:\t%s\t\nMovie Genre:\t%s\t\nMinimum Rating:\t%s\t\nCategorization:\t%s\t\nStarting page:\t%s\n" % (self.directory, self.quality, self.genre, self.minimum_rating, self.categorize, self.page_arg))

        if (movie_count <= 0):
            print("Could not find any movies with given parameters")
            exit(0)
        else:
            print("Query was successful.\nFound " + str(movie_count) + " movies. Download starting...\n")
        
        for page in range(page_start, page_count):
            counter += 1
            api_url = url + str(page)

            page_response = requests.get(api_url).json()
            movies = page_response["data"]["movies"]
            if not movies:
                print("Could not find any movies on this page.\n")     
            
            for movie in movies:
                if not movie:
                    print("Could not find the movie. Skipping...\n")
                    continue
                
                movie_counter += 1
                title_long = movie['title_long'].translate({ord(i):None for i in '/\:*?"<>|'})
                movie_rating = movie['rating']
                movie_genres = movie['genres']
                torrents = movie['torrents']

                if categorize and categorize != "rating":
                    for movie_genre in movie_genres:
                        for torrent in torrents:
                            self.__filter_torrents(torrent, title_long, movie_rating, movie_genre)
                    
                else:
                    for torrent in torrents:
                        self.__filter_torrents(torrent, title_long, movie_rating, None)
                    
        print("Download finished.")

    def __filter_torrents(self, torrent, title_long, movie_rating, movie_genre):
        quality = self.quality
        directory = self.directory
        
        if torrent == None:
            print("Could not find any torrents for " + title_long + ". Skipping...\n")
            return

        if quality == "all" or quality == "1080p":
            if torrent['quality'] == "1080p":
                self.__download_torrent((requests.get(torrent['url'])).content, title_long, torrent['quality'], directory, movie_rating, movie_genre)
        if quality == "all" or quality == "720p":
            if torrent['quality'] == "720p":
                self.__download_torrent((requests.get(torrent['url'])).content, title_long, torrent['quality'], directory, movie_rating, movie_genre)
        if quality == "all" or quality == "3d":
            if torrent['quality'] == "3D":
                self.__download_torrent((requests.get(torrent['url'])).content, title_long, torrent['quality'], directory, movie_rating, movie_genre)

    def __download_torrent(self, bin_content, movie_name, type, directory, rating, genre): 
        categorize = self.categorize
        
        if self.existing_file_counter > 10 and not self.skip_exit_condition:
            print("Found 10 existing files in a row. Do you want to keep downloading? Y/N")
            exit_answer = input()

            if exit_answer.lower() == "n":
                print("Exiting...")
                exit()
            elif exit_answer.lower() == "y":
                print("Continuing...")
                self.existing_file_counter = 0
                self.skip_exit_condition = True
            else:
                print('Invalid input. Enter "Y" or "N".')

        if categorize == "rating":
            os.makedirs((directory + "/" + str(math.trunc(rating))) + "+", exist_ok=True)
            directory += ("/" + str(math.trunc(rating)) + "+")
        elif categorize == "genre":
            os.makedirs((directory + "/" + str(genre)), exist_ok=True)
            directory += ("/" + str(genre))
        elif categorize == "rating-genre":
            os.makedirs((directory + "/" + str(math.trunc(rating)) + "+/" + genre), exist_ok=True)
            directory += ("/" + str(math.trunc(rating)) + "+/" + genre)
        elif categorize == "genre-rating":
            os.makedirs((directory + "/" + str(genre) + "/" + str(math.trunc(rating))) + "+", exist_ok=True)
            directory += ("/" + str(genre) + "/" + str(math.trunc(rating)) + "+")
        
        path = os.path.join(directory, movie_name + " " + type + ".torrent")
        self.bar.update(self.progress)

        if os.path.isfile(path):
            print(movie_name + ": File already exists. Skipping...")
            self.progress += 1
            self.existing_file_counter += 1
            return
        else:
            print("Downloading " + movie_name + " " + type)
            with open(path, 'wb') as f:
                f.write(bin_content)
            self.progress += 1
            self.existing_file_counter = 0
            return

    def download(self):
        self.__validate_args()
        self.__get_movie_info()
        self.__initialize_progress_bar()
        self.__initialize_download()