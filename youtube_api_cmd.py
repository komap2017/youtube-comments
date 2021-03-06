"""
-*- coding: utf-8 -*-
========================
Python YouTube API
========================

Developed by: Chirag Rathod (Srce Cde)
Email: chiragr83@gmail.com

========================
"""
from __future__ import print_function, division, with_statement, absolute_import, unicode_literals
import compatible
import json
import sys
import argparse
from urllib import *
from io import open
import sqlite3

compatible.import_int()
from urllib.parse import urlparse, parse_qs
# from urllib.request import urlopen
import requests

YOUTUBE_COMMENT_URL = 'https://www.googleapis.com/youtube/v3/commentThreads'
YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

NEXT_PAGE_TOKEN = 'nextPageToken'


def get_video_comment():
    parser = argparse.ArgumentParser()
    mxRes = 20
    vid = str()
    parser.add_argument("--c", help="calls comment function by keyword function", action='store_true')
    parser.add_argument("--max", help="number of comments to return")
    parser.add_argument("--videourl", help="Required URL for which comments to return")
    parser.add_argument("--key", help="Required API key")

    args = parser.parse_args()

    if not args.max:
        args.max = mxRes

    if not args.videourl:
        exit("Please specify video URL using the --videourl=parameter.")

    if not args.key:
        exit("Please specify API key using the --key=parameter.")

    try:
        video_id = urlparse(str(args.videourl))
        q = parse_qs(video_id.query)
        vid = q["v"][0]

    except:
        print("Invalid YouTube URL")

    parms = {
        'part': 'snippet,replies',
        'maxResults': args.max,
        'videoId': vid,
        'textFormat': 'plainText',
        'key': args.key
    }

    try:

        matches = open_url(YOUTUBE_COMMENT_URL, parms)
        i = 2
        mat = json.loads(matches)
        next_page_token = mat.get(NEXT_PAGE_TOKEN)
        print("\nPage : 1")
        print("------------------------------------------------------------------")
        load_comments(mat, video_id=vid)

        while next_page_token:
            parms.update({'pageToken': next_page_token})
            matches = open_url(YOUTUBE_COMMENT_URL, parms)
            mat = json.loads(matches)
            next_page_token = mat.get(NEXT_PAGE_TOKEN)
            print("\nPage : ", i)
            print("------------------------------------------------------------------")

            load_comments(mat, video_id=vid)

            i += 1
    except KeyboardInterrupt:
        print("User Aborted the Operation")

    except Exception as e:
        raise e
        print("Cannot Open URL or Fetch comments at a moment")


def open_url(url, parms):
    return requests.get(url, parms).text
    # f = urlopen(url + '?' + urlencode(parms))
    # data = f.read()
    # f.close()
    # matches = data.decode("utf-8")
    # return matches


def load_comments(mat, output=True, to_file='comments.txt', video_id=None):
    conn = sqlite3.connect("youtube.sqlite")

    # conn.execute("""CREATE TABLE IF NOT EXISTS comments()""")
    # return
    def get_snippet(obj):
        return obj['snippet']

    def show(com_author, com_text, date, rating, url, v_id):
        if output:
            sql = ''' INSERT INTO comments(author,comment,date,channel,video_id,rating)
                      VALUES(?,?,?,?,?, ?) '''
            task = (com_author, com_text, date, url, v_id, rating)
            conn.execute(sql, task)
            task = map(str, task)
            t = ' - '.join(task)
            print(t)

    def get_all(snippet):
        def get_key(key):
            return snippet[key]

        keys = ['authorDisplayName', 'textDisplay', 'publishedAt', 'likeCount', 'authorChannelUrl']
        res = list(map(get_key, keys))
        res.append(video_id)
        return res

    for item in mat["items"]:
        item_snippet = get_snippet(item)
        comment = item_snippet["topLevelComment"]
        comment_snippet = get_snippet(comment)
        show(*get_all(comment_snippet))
        if 'replies' in item.keys():
            for reply in item['replies']['comments']:
                reply_snippet = get_snippet(reply)
                show(*get_all(reply_snippet))
        conn.commit()
    conn.close()


class YouTubeApi:
    def load_search_res(self, search_response):
        videos, channels, playlists = [], [], []
        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                videos.append("{} ({})".format(search_result["snippet"]["title"],
                                               search_result["id"]["videoId"]))
            elif search_result["id"]["kind"] == "youtube#channel":
                channels.append("{} ({})".format(search_result["snippet"]["title"],
                                                 search_result["id"]["channelId"]))
            elif search_result["id"]["kind"] == "youtube#playlist":
                playlists.append("{} ({})".format(search_result["snippet"]["title"],
                                                  search_result["id"]["playlistId"]))

        print("Videos:\n", "\n".join(videos), "\n")
        print("Channels:\n", "\n".join(channels), "\n")
        print("Playlists:\n", "\n".join(playlists), "\n")

    def search_keyword(self):
        parser = argparse.ArgumentParser()
        mxRes = 20
        parser.add_argument("--s", help="calls the search by keyword function", action='store_true')
        parser.add_argument("--r", help="define country code for search results for specific country", default="IN")
        parser.add_argument("--search", help="Search Term", default="Srce Cde")
        parser.add_argument("--max", help="number of results to return")
        parser.add_argument("--key", help="Required API key")

        args = parser.parse_args()

        if not args.max:
            args.max = mxRes

        if not args.key:
            exit("Please specify API key using the --key= parameter.")

        parms = {
            'q': args.search,
            'part': 'id,snippet',
            'maxResults': args.max,
            'regionCode': args.r,
            'key': args.key
        }

        try:
            matches = self.openURL(YOUTUBE_SEARCH_URL, parms)

            search_response = json.loads(matches)
            i = 2

            nextPageToken = search_response.get("nextPageToken")

            print("\nPage : 1 --- Region : {}".format(args.r))
            print("------------------------------------------------------------------")
            self.load_search_res(search_response)

            while nextPageToken:
                parms.update({'pageToken': nextPageToken})
                matches = self.openURL(YOUTUBE_SEARCH_URL, parms)

                search_response = json.loads(matches)
                nextPageToken = search_response.get("nextPageToken")
                print("Page : {} --- Region : {}".format(i, args.r))
                print("------------------------------------------------------------------")

                self.load_search_res(search_response)

                i += 1

        except KeyboardInterrupt:
            print("User Aborted the Operation")

        except:
            print("Cannot Open URL or Fetch comments at a moment")

    def load_channel_vid(self, search_response):
        videos = []
        for search_result in search_response.get("items", []):
            if search_result["id"]["kind"] == "youtube#video":
                videos.append("{} ({})".format(search_result["snippet"]["title"],
                                               search_result["id"]["videoId"]))

        print("###Videos:###\n", "\n".join(videos), "\n")

    def channel_videos(self):
        parser = argparse.ArgumentParser()
        mxRes = 20
        parser.add_argument("--sc", help="calls the search by channel by keyword function", action='store_true')
        parser.add_argument("--channelid", help="Search Term", default="Srce Cde")
        parser.add_argument("--max", help="number of results to return")
        parser.add_argument("--key", help="Required API key")

        args = parser.parse_args()

        if not args.max:
            args.max = mxRes

        if not args.channelid:
            exit("Please specify channelid using the --channelid= parameter.")

        if not args.key:
            exit("Please specify API key using the --key= parameter.")

        parms = {
            'part': 'id,snippet',
            'channelId': args.channelid,
            'maxResults': args.max,
            'key': args.key
        }

        try:
            matches = self.openURL(YOUTUBE_SEARCH_URL, parms)

            search_response = json.loads(matches)

            i = 2

            nextPageToken = search_response.get("nextPageToken")
            print("\nPage : 1")
            print("------------------------------------------------------------------")

            self.load_channel_vid(search_response)

            while nextPageToken:
                parms.update({'pageToken': nextPageToken})
                matches = self.openURL(YOUTUBE_SEARCH_URL, parms)

                search_response = json.loads(matches)
                nextPageToken = search_response.get("nextPageToken")
                print("Page : ", i)
                print("------------------------------------------------------------------")

                self.load_channel_vid(search_response)

                i += 1

        except KeyboardInterrupt:
            print("User Aborted the Operation")

        except:
            print("Cannot Open URL or Fetch comments at a moment")


def main():
    y = YouTubeApi()

    if str(sys.argv[1]) == "--s":
        y.search_keyword()
    elif str(sys.argv[1]) == "--c":
        get_video_comment()
    elif str(sys.argv[1]) == "--sc":
        y.channel_videos()
    else:
        print(
            "Invalid Arguments\nAdd --s for searching video by keyword after the filename\nAdd --c to list comments after the filename\nAdd --sc to list vidoes based on channel id")


if __name__ == '__main__':
    main()
