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

class Crawler(object):
    eyeball = None

    @classmethod
    def mirror_url(cls, url, category):
        tmp = urlparse(url)
        if not tmp or not tmp.hostname or not tmp.netloc or not tmp.scheme or not tmp.scheme.startswith('http'):
            logging.debug("Skipping bad url %s" % url)
            return
        try:
            req = Request(url, headers={'User-Agent': 'eyeball'})
            logging.debug("Mirroring %s" % url)
        except ValueError:
            logging.debug("Skipping unrequestable URL: %s" % url)
            return False
        filename = url_to_path(url, category)
        
        # FIXME handle stale files and multiple versions
        if os.path.exists(filename):
            logging.debug("%s already mirrored at %s" % (url, filename))
            return True
        else:
            logging.debug("file %s not found, fetching." % filename)

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
    def mirror_all_sellers(cls):
        for domain in cls.eyeball.relationship.all_sellers():
            logging.info("Mirroring seller domain %s" % domain)
            cls.mirror_domain(domain, 'sellers')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    c = Crawler()
    for domain in sys.argv[1:]:
        c.mirror_domain(domain)

