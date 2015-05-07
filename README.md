DeepIntoYouTubeModBot
=====================

Moderation Bot for /r/DeepIntoYouTube

# Intro

This simple bot runs on python 2.7. It requires the google-api-python-client and praw libraries. It was written for use on windows, but the code should be portable to linux without change.

This script repeats a loop where it pulls the newest 100 submissions and checks the URL against YouTube data to see if the video has been uploaded in less than 4.7 months or has been viewed more than 100,000 times and removes them if they meet that criteria. 

* http://www.reddit.com/r/DeepIntoYouTube/
* https://praw.readthedocs.org/en/v2.1.21/
* https://developers.google.com/api-client-library/python/apis/youtube/v3

This is verified working with Python 2.7.5, PRAW 2.1.21, and google-api-python-client 1.4.0 on CentOS 7.0.

# Installation

1. Install openssl-devel, python-devel, and libffi-devel OS packages.
2. Install the google-api-python-client and praw python libraries.
  * `pip install google-api-python-client; pip install praw; pip install pyopenssl ndg-httpsclient pyasn1`
2. Download the `modbot.py` `modbot.conf` and to a directory of your chosing
3. Modify `modbot.conf` to suit your needs

# Execution

1. Execute `python modbot.py`
2. Ignore the UserWarning...
4. Sit back and watch the output

To stop execution, kill the process or press `Ctrl+C`

# Checks

1. Checks if video is a valid YouTube and peoperly fomated URL
2. Checks if video is in the top 100 all time submissions
3. Checks if video has already been posted in past 3 months
4. Checks if the video has over 100,000 views
5. Checks if the video has been uploaded in the past 4.7 months
6. Checks if the video is form a banned YouTube channel
