DeepIntoYouTubemodBot
=====================

Moderation Bot for /r/DeepIntoyouTube

# Intro

This simple bot runs on python 2.7. It requires the gdata and praw libraries. It was written for use on windows, but the code should be portable to linux without change.

This script pulls the newest 100 submissions and checks the URL against YouTube data to see if the video has been uploaded in less than 4.7 months or has been viewed more than 200,000 times and removes them if they meet thatcriteria. 

* http://www.reddit.com/r/DeepIntoYouTube/
* https://praw.readthedocs.org/en/v2.1.16/
* https://developers.google.com/gdata/articles/python_client_lib

# Installation

1. Install the gdata and praw python libraries.
2. Download the `modbot.py` to a directory of your chosing
3. Modify `modbot.py` and set the following variables
  * `yt_service.developer_key`
  * `yt_service.email`
  * `yt_service.password`
  * `yt_service.source`
  * `praw.Reddit`
  * `r.get_subreddit`

# Execution

1. Execute `python modbot.py`
2. Enter your reddit username
3. Enter your reddit password
4. Sit back and watch the output

To stop execution, kill the process or press `Ctrl+C`
