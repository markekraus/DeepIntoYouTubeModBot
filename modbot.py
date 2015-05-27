#!/usr/bin/env python

"""
/r/DeepIntoYouTube ModBot
Written by Mark Kraus /u/markekraus
https://github.com/markekraus/DeepIntoYouTubeModBot
"""

## Import Modules - Start
import signal
import sys
import os
import urllib3.contrib.pyopenssl
# Set urllib3 to use PyOpenSSL to disable InsecurePlatformWarning
urllib3.contrib.pyopenssl.inject_into_urllib3() 
import praw
import time
import string
import re
from apiclient.discovery import build
from datetime import datetime
from pprint import pprint
from urlparse import urlparse
from urlparse import parse_qs
## Import Modules - End

## Constants - Start
# This is the name of the modbot config file
MODBOT_SETTINGS_FILE = 'modbot.conf'
# Enable or Disable Debugging
DEBUG = True
# Enable or Disable Comments and Submission Removals to Reddit
R_COMMIT = False
## Constants - End

## Global Variable Initializations - Start

## Global Variable Initializations - End

## Signal Handling - Start
def signal_handler(signal, frame):
    """
    signal_handler() attempts to exit cleanly upon receiving a signal
    """
    # TODO: Add database handler closing. 
    print " "
    print "Exiting!"
    os._exit(0)
signal.signal(signal.SIGINT, signal_handler)
## Signal Handling - End

## Function Definitions - Start
def modbot_settings():
    """
    modbot_settings() Loads the settings in MODBOT_SETTINGS_FILE to globals()
    """
    execfile(MODBOT_SETTINGS_FILE, globals())

def init_youtube_api():
    """
    init_youtube_api() initializes the YouTube API and returns YouTube service
    object
    """
    return build(yt_api_service_name, yt_api_version,
        developerKey=yt_developer_key)

def init_reddit_api():
    """
    init_reddit_api() initializes the Re4ddit API and returns a Reddit object
    """
    r = praw.Reddit(r_praw)
    r.login(r_user, r_password)
    return r

def print_critical_error(error_string):
    """
    print_critical_error() print formatted critical errors
    """
    print "Critical Error: %s %s " % (time.strftime("%c"), error_string)

def print_error(error_string)
    """
    print_error() prints formatted errors    
    """
    print "Error: %s %s" % (time.strftime("%c"), log_string)
    
def print_log(log_string):
    """
    print_log() prints formatted log text
    """
    print "Log: %s %s" % (time.strftime("%c"), log_string)

def print_submission(r_submission):
    """
    print_submission() Prints information about a submission
    """
    try:
        created_time = datetime.fromtimestamp(r_submission.created_utc)
        print "  Submission Details"
        print "    URL:           %s" % r_submission.url
        print "    Permalink:     %s" % r_submission.permalink
        print "    Title:         %s" % r_submission.title
        print "    User:          %s" % r_submission.author.name
        print "    Created (UTC): %s" % created_time
    except:
        pass

def video_id(value):
    """
    video_id() Returns the YouTube video ID from a URL

    Example URL's that can be parsed:
    - http://youtu.be/SA2iWivDJiE
    - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/movie?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/attribution_link?a=AbE6fYtNaa4&u=%2F\
    watch%3Fv%3DNbyHNASFi6U%26feature%3Dshare
    - http://www.youtube.com/embed/SA2iWivDJiE
    - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    query = urlparse(value)
    pattern = re.compile('[^\w-].*$')
    if query.hostname == 'youtu.be':
        return pattern.sub('',query.path[1:])
    if query.hostname in yt_hostnames:
        if query.path == '/watch' or query.path == '/movie':
            p = parse_qs(query.query)
            return pattern.sub('',p['v'][0])
        if query.path == '/attribution_link':
            p = parse_qs(query.query)
            p = urlparse(p['u'][0])
            p = parse_qs(p.query)
            return pattern.sub('',p['v'][0])
        if query.path[:7] == '/embed/':
            return pattern.sub('',query.path.split('/')[2])
        if query.path[:3] == '/v/':
            return pattern.sub('',query.path.split('/')[2])
    raise ValueError("No video ID could be extracted from URL %s" % value)

def get_top_submissions(subreddit):
    """
    get_top_submissions() returns top submission IDs and top YouTube VIDs
    """
    print_log("Getting top %s submissions" % bot_top_subs_limit)
    r_top_submission_vids = []
    r_top_submissions_ids = []
    try:
        for top_submission in subreddit.get_top_from_all(limit=bot_top_subs_limit):
            try:
                r_top_submission_vids.appaend(video_id(top_submission.url))
                r_top_submissions_ids.appaend(top_submission.id)
            except:
                pass
        print_log("Top %s submissions grabbed successfully" % bot_top_subs_limit)
        return r_top_submission_vids, r_top_submissions_ids
    except:
        print_error("Unable to grab top %s submissions" % bot_top_subs_limit)
        raise Exception("Unable to grab top %s submissions" % bot_top_subs_limit)
    
def bot_sleep (loop_start):
    """
    bot_sleep() Determines if the bot needs to sleep
    """
    sleep_for = max(0.0, bot_sleep_sec - (time.time() - loop_start))
    time.sleep(sleep_for)
    
def is_valid_url(url):
    """
    is_valid_url() Returns True if it is a valid YouTube URL    
    """
    url_obj = urlparse(url)
    if any(url_obj.hostname in s for s in yt_host_names):
        try:
            video_id(url)
            return True
        except:
            return False
    else:
        return False
## Function Definitions - End

## Main Function - Start
def main(argv=None):
    # Last Time the top submissions were grabbed
    last_top_get = 0
    # List of submission ID's that have already been processed
    r_already_done = []
    # List of top submission YouTube video IDs
    r_top_submission_vids = []
    # List of top submission Reddit IDs
    r_top_submissions_ids = []
    # List of reasons a submission is being removed
    r_reasons = []
    try:
        modbot_settings()
    except:
        print_critical_error("Unable to load settings from file %s" 
            % MODBOT_SETTINGS_FILE)
        return 1
    try:
        yt_service = init_youtube_api()
    except:
        print_critical_error("Unable to Initialize YouTube API")
        return 1
    try:
        r = init_reddit_api()
    except:
        print_critical_error("Unable to initializes Reddit API")
        return 1
    # Get the PRAW subreddit object
    r_subreddit_obj = r.get_subreddit(r_subreddit)
    while True:
        loop_start = time.time()
        # If it has been long enough, grab the tops submissions
        if last_top_get < loop_start - bot_reload_top_subs_sec:
            try:
                r_top_submission_vids, r_top_submissions_ids = \
                    get_top_submissions(r_subreddit_obj) 
                last_top_get = time.time()
            except:
                pass
        bot_sleep(loop_start)
        for r_submission in subreddit.get_new(limit=bot_subs_limit):
            r_reasons = []
            if r_submission.id in already_done:
                continue
            if r_submission.is_self:
                print_log("Self-post detected")
                print_submission(r_submission)
                continue
            
                
                
                
## call main()
if __name__ == '__main__':
    status = main()
    sys.exit(status)
