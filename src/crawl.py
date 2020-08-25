#!/usr/bin/env python3

from email.utils import formatdate
from http.client import RemoteDisconnected
import logging
import multiprocessing
import os
import random 
import sys
from time import sleep, time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from utils import spew_file, url_to_path, touch_file

def crawl_wrap(domain, category):
    c = Crawler()
    c.mirror_domain(domain, category)

class Crawler(object):
    eyeball = None

    @classmethod
    def mirror_url(cls, url, category):
        tmp = urlparse(url)
        if not tmp or not tmp.hostname or not tmp.netloc or not tmp.scheme or not tmp.scheme.startswith('http'):
            logging.info("Skipping bad url %s" % url)
            return
        try:
            req = Request(url, headers={'User-Agent': 'eyeball'})
        except ValueError:
            logging.warning("Skipping unrequestable URL: %s" % url)
            return False
        filename = url_to_path(url, category)
        
        # FIXME handle stale files and multiple versions
        if os.path.exists(filename):
#            logging.info("Already mirrored: %s at %s" % (url, filename))
            return True

        try:
            res = urlopen(req, timeout=10)
            encodings = (res.headers.get_content_charset(), 'utf-8', 'latin_1')
            stuff = res.read()
            headers = ''
            for h in res.headers:
                headers = headers + "%s: %s\n" % (h, res.getheader(h))
            for encoding in encodings:
                try:
                    stuff = stuff.decode(encoding)
                    break
                except:
                    pass
            else:       
                print("Failed to decode %s" % url)
                return False
            spew_file(filename, '\n'.join([headers, stuff]))
            logging.info("Mirrored: %s" % url)
            return True
        except HTTPError as err:
            if err.code == 304:
                logging.info("304 Not Modified: %s" % url)
                return True
            logging.warning("Failed %d fetching: %s" % (err.code, url))
            touch_file(filename)
            return False
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logging.warning("%s fetching %s" % (str(e), url))
            touch_file(filename)
            return False

    @classmethod
    def mirror_domain(cls, domain, filetype="ads"):
        if "ads" == filetype:
            cls.mirror_url("https://%s/ads.txt" % domain, filetype)
        elif "sellers" == filetype:
            cls.mirror_url("https://%s/sellers.json" % domain, filetype)
        else:
            raise NotImplementedError

    @classmethod
    def mirror_all(cls):
        with multiprocessing.Pool(processes=4) as pool:
            for domain in cls.eyeball.relationship.all_sellers():
                pool.apply_async(crawl_wrap, [domain, 'sellers'])
            for domain in cls.eyeball.relationship.all_sources():
                pool.apply_async(crawl_wrap, [domain, 'ads'])

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    c = Crawler()
    for domain in sys.argv[1:]:
        c.mirror_domain(domain)
    
