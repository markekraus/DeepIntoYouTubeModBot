import praw
import time
import datetime
from pprint import pprint
from urlparse import urlparse
from urlparse import parse_qs
import gdata.youtube
import gdata.youtube.service

yt_hostnames = ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com']

yt_service = gdata.youtube.service.YouTubeService()
yt_service.ssl = True
yt_service.developer_key = '<snip>'
yt_service.email = '<snip>'
yt_service.password = '<snip>'
yt_service.source = '<snip>'
yt_service.ProgrammaticLogin()

already_done = []

def video_id(value):
	"""
	Examples:
	- http://youtu.be/SA2iWivDJiE
	- http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
	- http://www.youtube.com/movie?v=_oPAwA_Udwc&feature=feedu
	- http://www.youtube.com/attribution_link?a=AbE6fYtNaa4&u=%2Fwatch%3Fv%3DNbyHNASFi6U%26feature%3Dshare
	- http://www.youtube.com/embed/SA2iWivDJiE
	- http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
	"""
	query = urlparse(value)
	if query.hostname == 'youtu.be':
		return query.path[1:]
	if query.hostname in yt_hostnames:
		if query.path == '/watch' or query.path == '/movie':
			p = parse_qs(query.query)
			return p['v'][0]
		if query.path == '/attribution_link':
			p = parse_qs(query.query)
			p = urlparse(p['u'][0])
			p = parse_qs(p.query)
			return p['v'][0]
		if query.path[:7] == '/embed/':
			return query.path.split('/')[2]
		if query.path[:3] == '/v/':
			return query.path.split('/')[2]
	# fail?
	raise ValueError('No video ID could be extracted from URL %s' % value)
	
r = praw.Reddit('PRAW /r/deepintoyoutube modbot by /u/markekraus 2.04. '
				'URL: https://github.com/markekraus/DeepIntoYouTubemodBot')
r.login()
lasttopget = 0
topsubmissionvids = []
topsubmissionsids = []

while True:
	loopstart = time.time()
	subreddit = r.get_subreddit('deepintoyoutube')
	if lasttopget < loopstart - 86400:
		print 'Getting top 100 submissions...'
		try:
			topsubmissions = subreddit.get_top_from_all(limit=100)
		except:
			print '** Failed to get top sumissions'
			print ''
		else:
			lasttopget = time.time()
			topsubmissionvids = []
			topsubmissionsids = []
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
			print ''
		sleepfor = max(0.0, 30.0 - (time.time() - loopstart))
		time.sleep(sleepfor)
	try:
		submissions = subreddit.get_new(limit=100)
	except:
		e = sys.exc_info()[0]
		print '**get_new failed: %s' % str(e)
		print 'time: ' + time.strftime("%c")
		print ''
	else:
		try:
			for submission in submissions:
				reasons = []
				if submission.id not in already_done:
					if submission.is_self:
						print '!!! Selfpost !!!!'
						print 'Permalink:' 
						pprint(submission.permalink)
						pprint(submission.title)
						pprint(submission.author)
						print 'time: ' + time.strftime("%c")
						print ''
					else:
						suburl = urlparse(submission.url)
						if any(suburl.hostname in s for s in yt_hostnames):
							try:
								ytvid=video_id(submission.url)
							except:
								print '!!!! poorly formated URL !!!'
								reasons.append('* The URL you submitted appears to be poorly formated.')
								print ''
							else:
								if ytvid in topsubmissionvids and submission.id not in topsubmissionsids:
									print '!!!! Repost of a top 100 submission !!!'
									reasons.append('* This video is in the [top 100](http://www.reddit.com/r/DeepIntoYouTube/top/?sort=top&t=all) submission of all time in this sub. ')
								try:
									sleepfor = max(0.0, 30.0 - (time.time() - loopstart))
									time.sleep(sleepfor)
									searchres = list(r.search('url:"%s"' % str(ytvid) ,  subreddit='deepintoyoutube'))
								except:
									e = sys.exc_info()[0]
									print '**Search failed! %s' % str(e)
									print 'time: ' + time.strftime("%c")
									print ''
								else:
									if len(list(searchres)) > 1:
										tma = time.time() - 7889230
										for curres in searchres:
											if curres.id != submission.id and curres.created_utc > tma:
												print '!!!! Repost !!!'
												print 'previous post:'
												pprint(curres.url)
												pprint(curres.permalink)
												reasons.append("* This video has [already been posted in the last 3 months](http://www.reddit.com/r/DeepIntoYouTube/search?q=url%3A%22" + str(ytvid) + "%22&restrict_sr=on).")
												break
								try:
									entry = yt_service.GetYouTubeVideoEntry(video_id=ytvid)
								except:
									print '**Youtube look up for %s failed!' % str(ytvid)
									pprint(submission.url)
									pprint(submission.permalink)
									print 'time: ' + time.strftime("%c")
									print ''
								else:
									_tmp = time.strptime(entry.published.text, '%Y-%m-%dT%H:%M:%S.000Z')
									ptime = datetime.datetime(*_tmp[:6])
									now = datetime.datetime.now()
									tdelta = now - ptime
									seconds = tdelta.total_seconds()
									if seconds < 12360000:
										print '!!! Video is newer than 4.7 months !!!!'
										reasons.append('* Your submission violates rule #1, no videos uploaded to YouTube in the past 5 months are allowed. ')
									if hasattr(entry.statistics, 'view_count') and float(entry.statistics.view_count) > 200000:
										print '!!! Video has been viewed more than 200000 times !!!!'
										reasons.append('* Your submission violates rule #4, no YouTube videos with greater than 200,000 views are allowed. ')
						else:
							print '!!!! Submission does not contain valid youtube link !!!'
							reasons.append('* Your submission does not appear to contain a link to YouTube.')
						if len(reasons) > 0:
							modcommenttxt = "Your submission has been automatically removed for the following reason(s):\n\n"
							for reason in reasons:
								modcommenttxt += str(reason) + "\n\n"
							modcommenttxt += "\n\nIf you believe it has been removed in error, please [message the moderators](http://www.reddit.com/message/compose?to=%2Fr%2FDeepIntoYouTube)."
							print 'Submission Info:'
							pprint(submission.url)
							pprint(submission.permalink)
							pprint(submission.title)
							pprint(submission.author)
							try:
								print 'Video published on: %s ' % entry.published.text
								print 'Video view count: %s' % entry.statistics.view_count
							except:
								pass
							try:
								modcomment = submission.add_comment(modcommenttxt)
								modcomment.distinguish(as_made_by='mod')
								submission.remove(spam=False)
							except:
								print '** Comment or removal failed! link possibly deleted by user during checks.'
								print ''
							else:
								print 'Submission removed!'
								print 'time: ' + time.strftime("%c")
								print ''
					already_done.append(submission.id)
		except:
			print '**Main For loop failed: %s' % str(e)
			print 'time: ' + time.strftime("%c")
			print ''
	loopend = time.time()
	sleepfor = max(0.0, 30.0 - (loopend - loopstart))
	time.sleep(sleepfor)
