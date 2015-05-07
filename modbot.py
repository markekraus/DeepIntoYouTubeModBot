## Import Modules - Start
# These two lines will set urllib3 to use PyOpenSSL which will disable the InsecurePlatformWarning#
import signal
import sys
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()
import praw
import time
import datetime
from pprint import pprint
from urlparse import urlparse
from urlparse import parse_qs
import string, re
from apiclient.discovery import build

## Import Modules - End

## Signal Handling - Start

def signal_handler(signal, frame):
    print ' '
    print 'Exiting!'
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

## Signal Handling - End

## Settings - Start
# This is the name of the modbot config file
modbotSettingsFile = 'modbot.conf'
## Settings - End

## Function Definitions - Start
# Function to load settings file
def modbotsettings():
    try:
        # Try to execfile on the settings file and load them into the globals
        # this is terrible coding, but I don't feel like making a proper settings function
        execfile(modbotSettingsFile, globals())
        return True
    except:
        # Failed to load the settings file
        print '!!!! Syntax error in ' + modbotSettingsFile + ' !!!'
        return False

#Load the settings before continuing as they are used by just about everything
if not modbotsettings():
    print 'Unable to initilize settings. Exiting.'
    exit()

# Function to determine the youtube video ID from a URL
def video_id(value):
    """
    Example URL's that can be parsed:
    - http://youtu.be/SA2iWivDJiE
    - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/movie?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/attribution_link?a=AbE6fYtNaa4&u=%2Fwatch%3Fv%3DNbyHNASFi6U%26feature%3Dshare
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
    # fail?
    raise ValueError('No video ID could be extracted from URL %s' % value)

## Function Definitions - End
    
## API Initializations - Start
#YouTube API initialization
try:
    yt_service = build(yt_api_service_name, yt_api_version, developerKey=yt_developer_key)
except:
    print '!!!! Unable to initialize to youtube API !!!'
    exit()
# Reddit API initialization
try:     
    r = praw.Reddit(r_praw)
    r.login(r_user, r_password)
except:
    print '!!!! Unable to login to Reddit API !!!'
    exit()
## API Initializations - End
    
## Variable Initializations - Start
# Last Time the top submissions were grabbed
lasttopget = 0
# List of submission ID's that have already been processes so we can skip them
already_done = []
# List of top submission YouTube video IDs
topsubmissionvids = []
# List of top submission Reddit IDa
topsubmissionsids = []
# list of reasons a submission is being removed
reasons = []
## Variable Initializations - End

## Main Loop - Start
while True:
    # set the time this loop iteration was started
    loopstart = time.time()
    # Update the settings
    modbotsettings()
    # create the subreddit object
    subreddit = r.get_subreddit(r_subredit)
    # If it has been long enough since the last top submission pull, pull them again
    if lasttopget < loopstart - bot_reloadTopSubsSec:
        print 'Getting top ' + str(bot_topSubsLimit) + ' submissions...'
        try:
            topsubmissions = subreddit.get_top_from_all(limit=bot_topSubsLimit)
        except:
            print '** Failed to get top sumissions'
            print 'time: ' + time.strftime("%c")
            print ''
        else:
            # Set the last top submission pull tim to now
            lasttopget = time.time()
            # Blank out the top submissions lists
            topsubmissionvids = []
            topsubmissionsids = []
            # Fill the top submissions lists
            for topsubmission in topsubmissions:
                try:
                    topytvid=video_id(topsubmission.url)
                except:
                    print
                else:
                    if topytvid != None:
                        topsubmissionvids.append(topytvid)
                        topsubmissionsids.append(topsubmission.id)
            print 'Top submissions grabbed!'
            print 'time: ' + time.strftime("%c")
            print ''
        # Take a break before continuing to stay compliant with API rules
        sleepfor = max(0.0, bot_sleepsec - (time.time() - loopstart))
        time.sleep(sleepfor)
    # Try to pull the newest submissions
    try:
                submissions = subreddit.get_new(limit=bot_subsLimit)
    except:
        e = sys.exc_info()[0]
        print '**get_new failed: %s' % str(e)
        print 'time: ' + time.strftime("%c")
        print ''
    else:
        # Loop through the newest submissions
        try:
            for submission in submissions:
                reasons = []
                # Lets check if it's a good post, but only if wqe haven't already checked it before
                if submission.id not in already_done:
                    # We don't need to check anything if it is a selfpost, but it's good to see them
                    if submission.is_self:
                        print '!!! Selfpost !!!!'
                        print 'Permalink:' 
                        pprint(submission.permalink)
                        pprint(submission.title)
                        pprint(submission.author)
                        print 'time: ' + time.strftime("%c")
                        print ''
                    # ok, not a self post, so lets see if it's ok
                    else:
                        # Create a urlpares object of the submission URL for tests
                        suburl = urlparse(submission.url)
                        # check if it is an approved URL hostname
                        if any(suburl.hostname in s for s in yt_hostnames):
                            # Try to grab the YouTube video ID from the URL
                            try:
                                ytvid=video_id(submission.url)
                            # Couldn't get a video ID so it must not be a valid URL
                            except:
                                print '!!!! poorly formated URL !!!'
                                reasons.append('* The URL you submitted appears to be poorly formated. Only direct links to YouTube videos are allowed. Links to YouTube channels or playlist are prohibited.')
                            else:
                                # Check if the Youtube Video ID is in the top submissions
                                # AND make sure this post is not a top post itself
                                if ytvid in topsubmissionvids and submission.id not in topsubmissionsids:
                                    print '!!!! Repost of a top ' + str(bot_topSubsLimit) + ' submission !!!'
                                    reasons.append('* This video is in the [top ' + str(bot_topSubsLimit) +'](http://www.reddit.com/r/'+ r_subredit +'/top/?sort=top&t=all) submission of all time in this sub. ')
                                try:
                                    # Take a break before searching for reposts, but only if not enough time since the last search has passed.
                                    sleepfor = max(0.0, bot_sleepsec - (time.time() - loopstart))
                                    time.sleep(sleepfor)
                                    # Search the subreddit to see
                                    searchres = list(r.search('url:"%s"' % str(ytvid) ,  subreddit=r_subredit))
                                except:
                                    e = sys.exc_info()[0]
                                    print '**Search failed! %s' % str(e)
                                    print 'time: ' + time.strftime("%c")
                                    print ''
                                else:
                                    # Check if we found more than 1 instance of this video being posted
                                    if len(list(searchres)) > 1:
                                        # tma is the max age time of reposts
                                        tma = time.time() - bot_repostMaxAge
                                        # cycle through the possible repost submissions
                                        for curres in searchres:
                                            # if the current search result is not the current submission and it is neweer than tma, it is a repost 
                                            if curres.id != submission.id and curres.created_utc > tma:
                                                print '!!!! Repost !!!'
                                                print 'previous post:'
                                                pprint(curres.url)
                                                pprint(curres.permalink)
                                                pprint(submission.title)
                                                reasons.append("* This video has [already been posted in the last " + bot_repostMaxAgeTxt + "](http://www.reddit.com/r/" + r_subredit + "/search?q=url%3A%22" + str(ytvid) + "%22&restrict_sr=on).")
                                                break
                                try:
                                    # Try to get the YouTube API data for the current submissions video ID
                                    entry = yt_service.videos().list(id=ytvid, part='snippet,statistics').execute()
                                except:
                                    print '**Youtube look up for %s failed!' % str(ytvid)
                                    reasons.append('* I was unable to locate data on the YouTube video. Perhaps the URL is malformed or the video is video is no longer available. ')
                                    pprint(submission.url)
                                    pprint(submission.permalink)
                                    print 'time: ' + time.strftime("%c")
                                    print ''
                                else:
                                    if not entry["items"]:
                                        print '**Youtube look up for %s failed!' % str(ytvid)
                                        reasons.append('* I was unable to locate data on the YouTube video. Perhaps the URL is malformed or the video is video is no longer available. ')
                                        pprint(submission.url)
                                        pprint(submission.permalink)
                                        print 'time: ' + time.strftime("%c")
                                        print ''
                                    else:
                                        # Determins the age of the youtube video
                                        _tmp = time.strptime(entry["items"][0]["snippet"]["publishedAt"], '%Y-%m-%dT%H:%M:%S.000Z')
                                        ptime = datetime.datetime(*_tmp[:6])
                                        now = datetime.datetime.now()
                                        tdelta = now - ptime
                                        seconds = tdelta.total_seconds()
                                        # if the age of the video is less than the minium age, then it is too neweer
                                        if seconds < bot_minVideoAge:
                                            print '!!! Video is newer than ' + bot_minVideoAgeTxt + ' !!!!'
                                            reasons.append('* Your submission violates rule #1, no videos uploaded to YouTube in the past ' + bot_minVideoAgeTxt + ' are allowed. ')
                                        # If the video has more view than the max view count, then it is not allowed
                                        if float(entry["items"][0]["statistics"]["viewCount"]) > bot_maxViewCount:
                                            print '!!! Video has been viewed more than ' + str(bot_maxViewCount) + ' times !!!!'
                                            reasons.append('* Your submission violates rule #2, no YouTube videos with greater than ' + bot_maxViewCountTxt + ' views are allowed. ')
                                        # Check if the link is to a banned YouTube channel
                                        if entry["items"][0]["snippet"]["channelTitle"].lower() in (banname.lower() for banname in yt_bannedchannels):
                                            print '!!! Video is from a banned channel: ' + entry["items"][0]["snippet"]["channelTitle"] + ' !!!!'
                                            reasons.append('* Your submission links to the ' + entry["items"][0]["snippet"]["channelTitle"] + ' YouTube channel which has been banned in /r/' + r_subredit + '. ')
                                        
                        else:
                            # after all that, this probably not a YouTube link
                            print '!!!! Submission does not contain valid youtube link !!!'
                            reasons.append('* Your submission does not appear to contain a link to YouTube. Only direct links to YouTube videos are allowed. Links to any site other than YouTube are prohibited.')
                        # If we have indicated there are any reasons to remove this post, it's time to do that
                        if len(reasons) > 0:
                            # built modcommenttxt wityh all the reasons
                            modcommenttxt = "Your submission has been automatically removed for the following reason(s):\n\n"
                            for reason in reasons:
                                modcommenttxt += str(reason) + "\n\n"
                            modcommenttxt += "\n\nPlease review the subreddit rules. If you believe your submission has been removed in error, [message the moderators](http://www.reddit.com/message/compose?to=%2Fr%2F" + r_subredit + ") as replies to this comment or PM's to /u/" + r_user + " will not be read by the moderators."
                            print 'Submission Info:'
                            pprint(submission.url)
                            pprint(submission.permalink)
                            pprint(submission.title)
                            pprint(submission.author)
                            try:
                                print 'Video ID: %s' % ytvid
                                print 'Video published on: %s ' % entry["items"][0]["snippet"]["publishedAt"]
                                print 'Video view count: %s' % entry["items"][0]["statistics"]["viewCount"]
                                print 'Video channel: %s' % entry["items"][0]["snippet"]["channelTitle"]
                            except:
                                pass
                            # Try to distinguished comment on the cubmission and remove it
                            try:
                                modcomment = submission.add_comment(modcommenttxt)
                                modcomment.distinguish(as_made_by='mod')
                                submission.remove(spam=False)
                            except:
                                print 'time: ' + time.strftime("%c")
                                print '** Comment or removal failed! link possibly deleted by user during checks.'
                                print ''
                            else:
                                print 'Submission removed!'
                                print 'time: ' + time.strftime("%c")
                                print ''
                    # Update the list of already processed submissions, even if there were erros so we dont get stuck in endless loops.
                    already_done.append(submission.id)
        except:
            # How the hell did this happen with all those try/excepts?
            e = sys.exc_info()[0]
            print '**Main For loop failed: %s' % str(e)
            print 'time: ' + time.strftime("%c")
            print 'Submission Info:'
            try:
                pprint(submission.url)
                pprint(submission.permalink)
                pprint(submission.title)
                pprint(submission.author)
                already_done.append(submission.id)
            except:
                pass
            print ''
    # Time to sleep again before the next loop itteration.
    loopend = time.time()
    sleepfor = max(0.0, bot_sleepsec - (loopend - loopstart))
    time.sleep(sleepfor)

## Main Loop - End
