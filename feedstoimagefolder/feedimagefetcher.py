
#!/usr/bin/env python
import os
import md5
from urllib import URLopener
from urllib2 import urlopen
import feedparser
import html5lib
from bs4 import BeautifulSoup

IMAGE_DIR = os.path.expanduser('~/Pictures/ImageFeed/')

def status(message):
	print message.encode('utf8')

def safe_filename(raw_name):
    return "".join(c for c in raw_name if c.isalnum() or c in (' ', '.')).rstrip()
    
def fetch_image(feed_title, image_caption, image_url):
    dir_name = os.path.join(
            IMAGE_DIR, 
            safe_filename(feed_title))
    os.system("mkdir -p '%s'" % dir_name)
    image_filename = "%s/%s.%s" % (
                dir_name,
                  safe_filename(image_caption)[:200],
                  image_url.rsplit('.',1)[1])
    status(u"   retrieve %s" % image_url)
    status(u"         to %s" % image_filename)
    URLopener().retrieve(image_url, image_filename)
    status(u"")

def parseFeed(feed_url, depth=0):
    if depth > 1:
        print "Skipping '%s' as to deep" % feed_url
        return
    print "--------------------"
    contents = feedparser.parse(feed_url)
    if contents.entries:
        print "Handling feed '%s'" % feed_url
        for e in contents.entries:
            link_suffix = e.link.rsplit('.',1)[1].upper()
            if link_suffix in ('PNG', 'JPG', 'JPEG'):
                fetch_image(feed_title = contents.title, 
                      image_caption=e.title, 
                      image_url=e.link)
            elif e.link == feed_url:
            	print "skipping self link"
            else:
                parseFeed(e.link, depth+1)
    else:
        soup = BeautifulSoup(urlopen(feed_url))  
        feed_title = " ".join(soup.title.stripped_strings)
        bigPictureBoths = soup.find_all('div', 'bpBoth')
        if bigPictureBoths:
            print "Handling Big Picture page '%s'" % feed_url
            for bpBoth in bigPictureBoths:
                fetch_image(feed_title = feed_title, 
                     image_caption = " ".join(bpBoth.find('', 'bpCaption').stripped_strings), 
                     image_url=bpBoth.find('img')['src'])
        else:
            print "Skipping '%s' as type not recognized" % feed_url
 
if __name__ == "__main__":
    for feed_url in (
             # 'http://deskfeed.neophytou.net/rss/ddoi',
              'http://feeds.boston.com/boston/bigpicture/index',
              ):
        parseFeed(feed_url)
