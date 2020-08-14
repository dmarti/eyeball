#!/usr/bin/env python3

import base64
import hashlib
import logging
import os
import shutil
import socket
from tempfile import NamedTemporaryFile
import time
from urllib.parse import quote_plus, unquote

root = '/var/cache/eyeball'

def url_to_path(url, category):
    tmp = hashlib.sha256(url.encode('utf-8')).digest()
    h = base64.urlsafe_b64encode(tmp).decode('ascii')
    return os.path.join(root, category, h[0:2], h[2:4], h[4:6], 'latest', quote_plus(url))

def path_to_url(path):
    return unquote(os.path.basename(path))

def get_all_urls(category):
    "return urls oldest to newest"
    urls = {}
    feeddir = os.path.join(config.ROOT, category)
    for root, dirs, files in os.walk(feeddir):
        for filename in files:
            if filename[:4] != 'http':
                continue
            pathname = os.path.join(feeddir, filename)
            timestamp = os.path.getmtime(pathname)
            tmp = unquote(filename)
            if not 'amp;amp' in tmp:
                urls[tmp] = timestamp
    return [x for x in sorted(urls, key=urls.get)]

def snarf_file(url, category):
    "Get a file content or empty string if nothing there."
    filename = url_to_path(url, category)
    try:
        with open(filename, 'r', encoding='utf-8') as fdin:
            return fdin.read()
    except:
        return('')

def spew_file(filename, content):
    try:
        os.makedirs(os.path.split(filename)[0])
    except FileExistsError:
        pass
    with NamedTemporaryFile(dir=os.path.dirname(filename), mode='w+',
                            delete=False, encoding='utf-8') as scratch:
        scratch.write(content)
    os.replace(scratch.name, filename)
    try:
        shutil.chown(filename, user="rapids", group="rapids")
    except LookupError:
        pass

def touch_file(filename):
    try:
        os.utime(filename, None)
    except FileNotFoundError:
        spew_file(filename, '')


# vim: set expandtab:

