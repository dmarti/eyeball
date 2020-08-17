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

    def test_persist_domain(self):
        tg = Eyeball()
        td = tg.domain('example.com')
        self.assertEqual(td.domain, 'example.com')
        td.persist()
        td2 = tg.domain('example.com')
        td2.persist()
        self.assertEqual(td, td2)

    def test_adsrecord(self):
        tg = Eyeball()
        tr = tg.adsrecord(source = "exampleadstxt.com",
                          domain = "aloodo.com",
                          account_id = 31337,
                          account_type = 'RESELLER',
                          certification_authority_id = 'abc123'
                          )
        tr.persist()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    demo_db = Eyeball(start_demo_db=True)
    unittest.main(failfast=True)
    demo_db.stop_demo_db()


# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

