import json
import requests
import argparse
import os
import sys
import math
import string

def download_torrent(bin_content, movie_name, type, directory, rating, genre, categorize):
    if categorize == "rating":
        os.makedirs((directory + "/" + str(math.ceil(rating))), exist_ok=True)
        directory += ("/" + str(math.ceil(rating)))
    elif categorize == "genre":
        os.makedirs((directory + "/" + str(genre)), exist_ok=True)
        directory += ("/" + str(genre))
    elif categorize == "rating-genre":
        os.makedirs((directory + "/" + str(math.ceil(rating)) + "/" + genre), exist_ok=True)
        directory += ("/" + str(math.ceil(rating)) + "/" + genre)
    elif categorize == "genre-rating":
        os.makedirs((directory + "/" + str(genre) + "/" + str(math.ceil(rating))), exist_ok=True)
        directory += ("/" + str(genre) + "/" + str(math.ceil(rating)))
    
    path = os.path.join(directory, movie_name + " " + type + ".torrent")

    if os.path.isfile(path):
        print (movie_name + ": File already exists. Skipping.")
    else:
        print("Downloading " + movie_name + " " + type)
    
    with open(path, 'wb') as f:
        f.write(bin_content)

def filter_torrents(quality, torrent, title_long, directory, movie_rating, movie_genre, categorize):
    if quality == "all" or quality == "1080p":
        if torrent.get('quality') == "1080p":
            download_torrent((requests.get(torrent.get('url'))).content, title_long, torrent.get('quality'), directory, movie_rating, movie_genre, categorize)
    if quality == "all" or quality == "720p":
        if torrent.get('quality') == "720p":
            download_torrent((requests.get(torrent.get('url'))).content, title_long, torrent.get('quality'), directory, movie_rating, movie_genre, categorize)
    if quality == "all" or quality == "3d":
        if torrent.get('quality') == "3D":
            download_torrent((requests.get(torrent.get('url'))).content, title_long, torrent.get('quality'), directory, movie_rating, movie_genre, categorize)

def main():
    quality_options=["all", "720p", "1080p", "3d"]
    genre_options=["all", "action", "adventure", "animation", "biography", "comedy", "crime", "documentary", "drama", "family", "fantasy", "film-noir", "game-show", "history", "horror", "music", "musical", "mystery", "news", "reality-tv", "romance", "sci-fi", "sport", "talk-show", "thriller", "war", "western"]
    rating_options=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    sortby_options=["title", "year", "rating", "peers", "seeds", "download_count", "like_count", "date_added"]
    category_options=["none", "rating", "genre", "genre-rating", "rating-genre"]
    
    desc = "A command-line tool to for downloading .torrent files from YTS"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-d", "--domain", help='Enter a YTS domain like "am" or "lt".', dest='domain', required=True)
    parser.add_argument("-o", "--output", help="Output Directory", dest='output', required=False)
    parser.add_argument("-q", "--quality", help='Movie Quality. Valid arguments are: "all", "720p", "1080p", "3d"', dest='quality', required=False)
    parser.add_argument("-g", "--genre", help='Movie Genre. Valid arguments are: "all", "action", "adventure", "animation", "biography", "comedy", "crime", "documentary", "drama", "family", "fantasy", "film-noir", "game-show", "history", "horror", "music", "musical", "mystery", "news", "reality-tv", "romance", "sci-fi", "sport", "talk-show", "thriller", "war", "western"', dest='genre', required=False)
    parser.add_argument("-r", "--rating", help="Minimum rating score. Integer between 0-10", dest='rating', required=False)
    parser.add_argument("-s", "--sort-by", help='Sorting options. Valid arguments are: "title", "year", "rating", "peers", "seeds", "download_count", "like_count", "date_added"', dest='sort_by', required=False)
    parser.add_argument("-c", "--categorize-by", help='Creates a folder structure. Valid arguments are: "rating", "genre", "rating-genre", "genre-rating"', dest='categorize_by', required=False)

    args=parser.parse_args()
    domain = args.domain
    directory_arg = args.output
    directory = os.path.curdir
    quality = args.quality
    genre = args.genre
    minimum_rating = args.rating
    sort_by = args.sort_by
    categorize = args.categorize_by
    
    if not domain:
        print("Please enter YTS domain.\nExiting...")
        exit(0)

    if directory_arg:
        os.makedirs(str(directory_arg), exist_ok=True)
        directory = str(os.path.curdir) + "/" + str(directory_arg)
    elif not directory_arg:
        os.makedirs('Torrents', exist_ok=True)
        directory = os.path.curdir + "/Torrents"
    
    if not quality in quality_options and quality:
        print('You entered an invalid quality option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)
    if not quality:
        print('You have not entered a quality option. Downloading all available qualities.')
        quality = "all"

    if not genre in genre_options and genre:
        print('You entered an invalid genre option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)
    if not genre:
        print('You have not entered a genre option. Downloading all available genres.')
        genre = "all"

    if not minimum_rating in rating_options and minimum_rating:
        print('You entered an invalid rating option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)
    if not minimum_rating:
        print('You have not entered a rating option. Downloading all available ratings.')
        minimum_rating = "1"

    if not sort_by in sortby_options and sort_by:
        print('You entered an invalid sort option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)
    if not sort_by:
        print('You have not entered a sort option. Downloading by alphabetical order.')
        sort_by = "title"

    if not categorize in category_options and categorize:
        print('You entered an invalid categorizing option. Type "--help" to see a list of valid options.\nExiting...')
        exit(0)

    limit = 50
    url = "https://yts." + domain + "/api/v2/list_movies.json?" + "quality=" + quality + "&genre=" + genre + "&minimum_rating=" + minimum_rating + "&sort_by=" + sort_by + "&order_by=asc" + "&limit=" + str(limit) + "&page="
    url_response = requests.get(url)
    page_data = json.loads(url_response.content)
    page_count = math.ceil(page_data["data"]["movie_count"]/limit)
    count = 0
    movie_count = 0

    for page in range(1, page_count):
        count += 1
        api_url = url + str(page)

        response = requests.get(api_url).json()
        data = response.get("data")
        movies = data.get("movies")

        if not movies:
            print("Could not find any movies on this page")
            exit(0)
        
        for movie in movies:
            movie_count += 1
            title_long = movie.get('title_long').translate({ord(i):None for i in '/\:*?"<>|'})
            movie_rating = movie.get('rating')
            movie_genres = movie.get('genres')
            torrents = movie.get('torrents')

            if not torrents:
                print('Could not find any torrents for this movie')

            if categorize and categorize != "rating":
                for movie_genre in movie_genres:
                    for torrent in torrents:
                        filter_torrents(quality, torrent, title_long, directory, movie_rating, movie_genre, categorize)
            else:
                for torrent in torrents:
                    filter_torrents(quality, torrent, title_long, directory, movie_rating, None, categorize)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
            print('\nKeypress Detected.')
            print('\nExiting...')
            exit(0)