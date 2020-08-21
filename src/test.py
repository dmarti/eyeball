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

    def test_sellers(self):
        tg = Eyeball()
        ts = tg.sellers(domain="ad.aloodo.com", contact_email="webmaster@aloodo.com")
        ts.persist()
        ts2 = tg.sellers.lookup_one(domain="ad.aloodo.com")
        self.assertEqual(ts, ts2)

    def test_relationship(self):
        tg = Eyeball()
        tr = tg.relationship(source = "example.com",
                             destination = "aloodo.com",
                             account_id = '1337',
                             account_type = 'RESELLER',
                             certification_authority_id = 'abc123'
                            )
        tr.persist()
        tr2 = tg.relationship.lookup_one(source="example.com")
        self.assertEqual(tr, tr2)
        tr3 = tg.relationship.lookup_one(account_id='1337')
        self.assertEqual(tr, tr3)

    def test_parse_adstxt(self):
        tg = Eyeball()
        tg.adstxt.parse_file('https://blog.zgp.org/ads.txt')
        tg.adstxt.parse_file('https://nytimes.com/ads.txt')
        self.assertIn('aloodo.com', list(tg.relationship.all_sellers()))

    def test_parse_all(self):
        tg = Eyeball()
        tg.sellers.parse_file('https://openx.com/sellers.json')
        tg.parse_all()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    demo_db = Eyeball(start_demo_db=True)
    unittest.main(failfast=True)
    demo_db.stop_demo_db()


# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

