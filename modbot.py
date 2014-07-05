import praw
import time
import datetime
from pprint import pprint
from urlparse import urlparse
from urlparse import parse_qs
import gdata.youtube
import gdata.youtube.service

yt_hostnames = ['youtube.com', 'www.youtube.com', 'youtu.be']

yt_service = gdata.youtube.service.YouTubeService()
yt_service.ssl = True
yt_service.developer_key = '<snip>'
yt_service.email = '<snip>'
yt_service.password = '<snip>'
yt_service.source = '<snip>'
yt_service.ProgrammaticLogin()


def video_id(value):
    """
    Examples:
    - http://youtu.be/SA2iWivDJiE
    - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/embed/SA2iWivDJiE
    - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    query = urlparse(value)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None
	
r = praw.Reddit('PRAW /r/deepintoyoutube modbot by /u/markekraus 0.1. '
				'URL: https://github.com/markekraus/DeepIntoYouTubemodBot')
r.login()
while True:
	loopstart = time.time()
	subreddit = r.get_subreddit('deepintoyoutube')
	for submission in subreddit.get_new(limit=100):
		problem = 0
		if submission.is_self:
			print '!!! Selfpost !!!!'
			print 'Permalink:' 
			pprint(submission.permalink)
		suburl = urlparse(submission.url)
		if any(suburl.hostname in s for s in yt_hostnames):
			suburlqs = parse_qs(suburl.query)
			
			try:
				#entry = yt_service.GetYouTubeVideoEntry(video_id=suburlqs['v'][0])
				entry = yt_service.GetYouTubeVideoEntry(video_id=video_id(submission.url))
			except:
				#print 'poorly formated URL'
				#pprint(submission.url)
				#pprint(submission.permalink)
				#pprint(suburl.query)
				break
			_tmp = time.strptime(entry.published.text, '%Y-%m-%dT%H:%M:%S.000Z')
			ptime = datetime.datetime(*_tmp[:6])
			now = datetime.datetime.now()
			tdelta = now - ptime
			seconds = tdelta.total_seconds()
			if seconds < 12360000:
				print '!!! Video is newer than 4.7 months !!!!'
				problem = 1
			if float(entry.statistics.view_count) > 200000:
				print '!!! Video has been viewed more than 200000 times !!!!'
				problem = 1
			if problem == 1:
				pprint(submission.url)
				pprint(submission.url)
				pprint(suburl.hostname)
				pprint(seconds)
				print 'Video published on: %s ' % entry.published.text
				print 'Video view count: %s' % entry.statistics.view_count
				print 'Permalink:' 
				pprint(submission.permalink)
				pprint(submission.hidden)
				submission.remove(spam=False)
				print 'Submission removed!'
				print ''
	loopend = time.time()
	sleepfor = max(0.0, 30.0 - (loopend - loopstart))
	time.sleep(sleepfor)
