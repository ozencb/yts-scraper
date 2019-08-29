import json
import requests
import argparse
import os
import sys
import math
import string
import time
import progressbar

bar = None
progress = 1
movie_count = None
existing_file_counter = 0
skip_exit_condition = False


def download_torrent(bin_content, movie_name, type, directory, rating, genre, categorize): 
    global existing_file_counter
    global progress
    global bar
    global skip_exit_condition

    
    if existing_file_counter > 10 and not skip_exit_condition:
        print("Found 10 existing files in a row. Do you want to keep downloading? Y/N")
        exit_answer = input()

        if exit_answer.lower() == "n":
            print("Exiting...")
            exit()
        elif exit_answer.lower() == "y":
            print("Continuing...")
            existing_file_counter = 0
            skip_exit_condition = True
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
    bar.update(progress)

    if os.path.isfile(path):
        print(movie_name + ": File already exists. Skipping...")
        progress += 1
        existing_file_counter += 1
        return
    else:
        print("Downloading " + movie_name + " " + type)
        with open(path, 'wb') as f:
            f.write(bin_content)
        progress += 1
        existing_file_counter = 0
        return


def filter_torrents(quality, torrent, title_long, directory, movie_rating, movie_genre, categorize):
    if torrent == None:
        print("Could not find any torrents for " + title_long + ". Skipping...\n")
        return

    if quality == "all" or quality == "1080p":
        if torrent['quality'] == "1080p":
            download_torrent((requests.get(torrent['url'])).content, title_long, torrent['quality'], directory, movie_rating, movie_genre, categorize)
    if quality == "all" or quality == "720p":
        if torrent['quality'] == "720p":
            download_torrent((requests.get(torrent['url'])).content, title_long, torrent['quality'], directory, movie_rating, movie_genre, categorize)
    if quality == "all" or quality == "3d":
        if torrent['quality'] == "3D":
            download_torrent((requests.get(torrent['url'])).content, title_long, torrent['quality'], directory, movie_rating, movie_genre, categorize)


def main():
    progressbar.streams.wrap_stderr()
    WRAP_STDERR= True
    progressbar.streams.flush()

    global bar
    global movie_count
        
    quality_options=["all", "720p", "1080p", "3d"]
    genre_options=["all", "action", "adventure", "animation", "biography", "comedy", "crime", "documentary", "drama", "family", "fantasy", "film-noir", "game-show", "history", "horror", "music", "musical", "mystery", "news", "reality-tv", "romance", "sci-fi", "sport", "talk-show", "thriller", "war", "western"]
    rating_options=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    sortby_options=["title", "year", "rating", "latest", "peers", "seeds", "download_count", "like_count", "date_added"]
    category_options=["none", "rating", "genre", "genre-rating", "rating-genre"]
    
    desc = "A command-line tool to for downloading .torrent files from YTS"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-o", "--output", help='Output Directory', dest='output', required=False)
    parser.add_argument("-q", "--quality", help='Movie Quality. Valid arguments are: "all", "720p", "1080p", "3d"', dest='quality', required=False)
    parser.add_argument("-g", "--genre", help='Movie Genre. Valid arguments are: "all", "action", "adventure", "animation", "biography", "comedy", "crime", "documentary", "drama", "family", "fantasy", "film-noir", "game-show", "history", "horror", "music", "musical", "mystery", "news", "reality-tv", "romance", "sci-fi", "sport", "talk-show", "thriller", "war", "western"', dest='genre', required=False)
    parser.add_argument("-r", "--rating", help='Minimum rating score. Integer between 0-10', dest='rating', required=False)
    parser.add_argument("-s", "--sort-by", help='Sorting options. Valid arguments are: "title", "year", "rating", "latest", "peers", "seeds", "download_count", "like_count", "date_added"', dest='sort_by', required=False)
    parser.add_argument("-c", "--categorize-by", help='Creates a folder structure. Valid arguments are: "rating", "genre", "rating-genre", "genre-rating"', dest='categorize_by', required=False)
    parser.add_argument("-p", "--page", help='Enter an integer to skip ahead pages', dest='page', required=False)

    args=parser.parse_args()
    directory_arg = args.output
    directory = os.path.curdir
    quality = args.quality
    genre = args.genre
    minimum_rating = args.rating
    sort_by = args.sort_by
    categorize = args.categorize_by
    page_arg = args.page
    order = "asc"
    limit = 50

    
    if directory_arg:
        os.makedirs(str(directory_arg), exist_ok=True)
        directory = str(os.path.curdir) + "/" + str(directory_arg)
    elif not directory_arg and not categorize:
        os.makedirs('Torrents', exist_ok=True)
        directory = os.path.curdir + "/Torrents"
    elif not directory_arg and categorize:
        os.makedirs(str(categorize).title(), exist_ok=True)
        directory = os.path.curdir + "/" + str(categorize)
    
    
    if not quality in quality_options and quality:
        print('Invalid quality option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)
    if not quality:
        print('No quality argument was given. Downloading all available qualities by default.')
        quality = "all"

    
    if not genre in genre_options and genre:
        print('Invalid genre option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)
    if not genre:
        print('No genre argument was given. Downloading all available genres by default.')
        genre = "all"

    
    if not minimum_rating in rating_options and minimum_rating:
        print('Invalid rating option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)
    if not minimum_rating:
        print('No rating argument was given. Downloading all available ratings by default.')
        minimum_rating = "1"

    
    if not sort_by in sortby_options and sort_by:
        print('Invalid sorting option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)
    if not sort_by:
        print('No sorting argument was given. Downloading in alphabetical order by default.')
        sort_by = "title"
    if sort_by == "latest":
        sort_by = "date_added"
        order = "desc"

    
    if not categorize in category_options and categorize:
        print('Invalid categorizing option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)

    
    if not page_arg:
        print('No page argument was given. Starting from page 1.')
        page_arg = 1

    

    concat_url = "https://yts.am/api/v2/list_movies.json?" + "quality=" + quality + "&genre=" + genre + "&minimum_rating=" + minimum_rating + "&sort_by=" + sort_by + "&order_by=" + order + "&limit=" + str(limit) + "&page="
    data = requests.get(concat_url).json()
    
    if data["status"] != "ok" or not data:
        print("Could not get a response.\nExiting...")
        exit(0)

    page_start = int(page_arg)
    movie_count = data["data"]["movie_count"]
    page_count = math.trunc(movie_count / limit)
    counter = 0
    movie_counter = 0

    print("Query was successful.\nFound " + str(movie_count) + " movies. Download starting...\n")

    widgets = ['[', progressbar.Timer(), ' - ', progressbar.ETA(), '] ',progressbar.Bar()]
    bar = progressbar.ProgressBar(max_value=movie_count, redirect_stdout=True, widgets=widgets)

    for page in range(page_start, page_count):
        counter += 1
        api_url = concat_url + str(page)

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
                        filter_torrents(quality, torrent, title_long, directory, movie_rating, movie_genre, categorize)
                
            else:
                for torrent in torrents:
                    filter_torrents(quality, torrent, title_long, directory, movie_rating, None, categorize)
                    
        print("Download finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
            print('\nKeypress Detected.')
            print('\nExiting...')
            exit(0)