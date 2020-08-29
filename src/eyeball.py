#!/usr/bin/env python3

from datetime import timezone
import logging
import os
import signal
import subprocess
import sys
import time

try:
    import psycopg2
except:
    print("This needs to be run on the server or container with Python dependencies installed.")
    sys.exit(0)

import config
from adstxt import AdsTxt
from crawl import Crawler
from relationship import Relationship
from sellers import Sellers

class Eyeball(object):

    def __init__(self, applog=None, start_demo_db=False):
        global logging
        if applog is not None:
            logging = applog
        self.logging = logging
        self.adstxt = AdsTxt
        self.adstxt.eyeball = self
        self.crawler = Crawler
        self.crawler.eyeball = self
        self.relationship = Relationship
        self.relationship.eyeball = self
        self.sellers = Sellers
        self.sellers.eyeball = self
        if start_demo_db:
            self.start_demo_db()
        self.connect()

    def connect(self):
        for i in range(5):
            try: 
                self.conn = psycopg2.connect(database=config.DB_NAME, user=config.DB_USER,
                                             host=config.DB_HOST, port=config.DB_PORT)
                if i > 0:
                    logging.info("Connected to database after %d attempt(s)." % i)
                break
            except psycopg2.OperationalError:
                logging.info("Waiting for database.")
                time.sleep(2**(i+3))
        else:
            logging.error("Database connection failed")
            raise RuntimeError

    def start_demo_db(self):
        try:
            psycopg2.connect(database=config.DB_NAME, user=config.DB_USER, host=config.DB_HOST, port=config.DB_PORT)
            return
        except psycopg2.OperationalError:
            pass
        demo_db = subprocess.Popen(["/usr/bin/sudo", "-u", "postgres", "/usr/lib/postgresql/9.6/bin/postgres",
                                    "-D", "/var/lib/postgresql/9.6/main",
                                    "-c", "config_file=/etc/postgresql/9.6/main/postgresql.conf"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("Started test database. PID is %d" % demo_db.pid)

    def stop_demo_db(self):
        self.conn.close()
        try:
            with open("/var/lib/postgresql/9.6/main/postmaster.pid") as pidfile:
                pidline = pidfile.readline()
            os.kill(int(pidline), signal.SIGKILL)
            logging.info("Waiting for test database to shut down.")
            time.sleep(1)
        except ProcessLookupError:
            pass

        while True:
            try:
                psycopg2.connect(database=config.DB_NAME, user=config.DB_USER, host=config.DB_HOST, port=config.DB_PORT)
            except:
                return

    def now(self):
        with self.conn.cursor() as curs:
            curs.execute("SELECT NOW()")
            when = curs.fetchone()[0]
            when = when.replace(tzinfo=timezone.utc)
            return when

    def parse_all(self):
        self.sellers.parse_all()
        self.adstxt.parse_all()

    def do_background(self):
        if not os.fork():
            seller_parser = self.__class__()
            while True:
                seller_parser.sellers.parse_all()
        if not os.fork():
            adstxt_parser = self.__class__()
            while True:
                adstxt_parser.adstxt.parse_all()
        if not os.fork():
            mirrorer = self.__class__()
            while True:
                mirrorer.crawler.mirror_all()
        return


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    e = Eyeball(start_demo_db=True)
#    e.do_background()
    e.adstxt.parse_file('https://nytimes.com/ads.txt')
    while True:
        time.sleep(10)
        logging.debug("tick")

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
