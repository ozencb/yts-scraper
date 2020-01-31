import argparse
import traceback
from ytsscraper.scraper import Scraper


def main():
    desc = "A command-line tool to for downloading .torrent files from YTS"
    
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-o", "--output",
                        help='Output Directory',
                        dest='output',
                        type=str.lower,
                        required=False)
    
    parser.add_argument("-q", "--quality",
                        help='Movie Quality. Valid arguments are: "all", "720p", "1080p", "3d"',
                        dest='quality',
                        type=str.lower,
                        required=False,
                        choices=['all', '720p', '1080p', '3d'],
                        default='1080p',
                        const='1080p',
                        nargs='?')
    
    parser.add_argument("-g", "--genre",
                        help='Movie Genre. Valid arguments are: "all", "action", "adventure", "animation", "biography", "comedy", "crime", "documentary", "drama", "family", "fantasy", "film-noir", "game-show", "history", "horror", "music", "musical", "mystery", "news", "reality-tv", "romance", "sci-fi", "sport", "talk-show", "thriller", "war", "western"',
                        dest='genre',
                        type=str.lower,
                        required=False,
                        choices=['all', 'action', 'adventure', 'animation', 'biography', 'comedy', 'crime', 'documentary', 'drama', 'family', 'fantasy', 'film-noir', 'game-show', 'history', 'horror', 'music', 'musical', 'mystery', 'news', 'reality-tv', 'romance', 'sci-fi', 'sport', 'talk-show', 'thriller', 'war', 'western'],
                        default='all',
                        const='all',
                        nargs='?')
    
    parser.add_argument("-r", "--rating",
                        help='Minimum rating score. Integer between 0-10',
                        dest='rating',
                        type=str.lower,
                        required=False,
                        choices=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
                        default='0',
                        const='0',
                        nargs='?')
    
    parser.add_argument("-s", "--sort-by",
                        help='Sorting options. Valid arguments are: "title", "year", "rating", "latest", "peers", "seeds", "download_count", "like_count", "date_added"',
                        dest='sort_by',
                        type=str.lower,
                        required=False,
                        choices=['title', 'year', 'rating', 'latest', 'peers', 'seeds', 'download_count', 'like_count', 'date_added'],
                        default='latest',
                        const='latest',
                        nargs='?')
    
    parser.add_argument("-c", "--categorize-by",
                        help='Creates a folder structure. Valid arguments are: "rating", "genre", "rating-genre", "genre-rating"',
                        dest='categorize_by',
                        type=str.lower,
                        required=False,
                        choices=['none', 'rating', 'genre', 'genre-rating', 'rating-genre'],
                        default='rating',
                        const='rating',
                        nargs='?')
    
    parser.add_argument("-p", "--page",
                        help='Enter an integer to skip ahead number of pages',
                        dest='page',
                        type=int,
                        required=False,
                        default=1,
                        const=1,
                        nargs='?')

    args = parser.parse_args()
    scraper = Scraper(args)
    scraper.download()
    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
            print('\nKeypress Detected.\nExiting...')
    except Exception:
        traceback.print_exc()
    exit(0)