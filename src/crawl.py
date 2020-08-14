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

from utils import spew_file, url_to_path

def mirror_url(url, category):
    tmp = urlparse(url)
    if not tmp or not tmp.hostname or not tmp.netloc or not tmp.scheme or not tmp.scheme.startswith('http'):
        logging.debug("Skipping bad url %s" % url)
        return

    try:
        req = Request(url, headers={'User-Agent': 'eyeball'})
    except ValueError:
        logging.debug("Skipping unrequestable URL: %s" % url)
        return False
    filename = url_to_path(url, category)

    try:
        res = urlopen(req, timeout=60)
        encodings = (res.headers.get_content_charset(), 'utf-8', 'latin_1')
        stuff = res.read()
        for encoding in encodings:
            try:
                stuff = stuff.decode(encoding)
                break
            except:
                pass
        else:       
            print("Failed to decode %s" % url)
            return False
        spew_file(filename, stuff)
        logging.info("Mirrored: %s" % url)
        return True
    except HTTPError as err:
        if err.code == 304:
            logging.info("304 Not Modified: %s" % url)
            return True
        logging.warning("Failed %d fetching: %s" % (err.code, url))
        return False
    except KeyboardInterrupt:
        raise
    except Exception as e:
        logging.warning("%s fetching %s" % (str(e), url))
        return False

def mirror_domain(domain):
    mirror_url("https://%s/ads.txt" % domain, 'ads')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    for domain in sys.argv[1:]:
        mirror_domain(domain)

