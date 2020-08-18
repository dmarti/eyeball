#!/usr/bin/env python3

import logging
from random import randint
import unittest

try:
    import psycopg2
except:
    print("This should be run on the server or container with Python dependencies installed.")
    print("To start the container and run tests, use test.sh")
    sys.exit(0)

from eyeball import Eyeball

class EyeballTestCase(unittest.TestCase):

    def test_db_time(self):
        '''
        Sanity test: is the time on the database close to the time in the application?
        '''
        tg = Eyeball()
        from datetime import datetime
        self.assertAlmostEqual(tg.now().timestamp(), datetime.now().timestamp(), delta = 0.2)

    def test_adstxt(self):
        tg = Eyeball()
        ta = tg.adstxt(domain="x.example.com", fulltext="# comment")
        ta.persist()
        ta2 = tg.adstxt.lookup_one(domain="x.example.com")
        self.assertEqual(ta, ta2)

    def test_adsrecord(self):
        tg = Eyeball()
        tr = tg.adsrecord(source = "example.com",
                          domain = "aloodo.com",
                          account_id = 31337,
                          account_type = 'RESELLER',
                          certification_authority_id = 'abc123'
                          )
        tr.persist()

    def test_adsrecord_from_objects(self):
        tg = Eyeball()
        tr = tg.adsrecord(source = "example.com",
                          domain = "aloodo.com",
                          account_id = 31337,
                          account_type = 'RESELLER',
                          certification_authority_id = 'abc123',
                          adstxt = tg.adstxt("example.com")
                          )
        tr.persist()

    def test_persist_adsrecord(self):
        tg = Eyeball()
        tr = tg.adsrecord(domain = "aloodo.com",
                          account_id = 'xyz123',
                          account_type = 'RESELLER',
                          certification_authority_id = 'abc123',
                          adstxt = tg.adstxt("example.com")
                          )
        tr.persist()
        tr2 = tg.adsrecord.lookup_one(account_id='xyz123')
        self.assertEqual(tr, tr2)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    demo_db = Eyeball(start_demo_db=True)
    unittest.main(failfast=True)
    demo_db.stop_demo_db()


# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

