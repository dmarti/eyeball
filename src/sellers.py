#!/usr/bin/env python3

import logging
from urllib.parse import urlparse

from utils import path_to_url, snarf_file

class Sellers(object):
    eyeball = None

#-- sellers.json files
#CREATE TABLE IF NOT EXISTS sellersjson (
#        id SERIAL PRIMARY KEY,
#        domain TEXT NOT NULL,
#        contact_email TEXT,     -- optional contact email
#        contact_address TEXT,   -- optional contact postal address
#        version TEXT NOT NULL,  -- version, required
#        ext TEXT,               -- optional extensions
#        created TIMESTAMP NOT NULL DEFAULT NOW()
#);

    def __init__(self, domain, contact_email=None, contact_address=None,
                 version='1.0', ext=None,
                 fulltext='', created=None, modified=None, sid=None):
        self.id = sid
        self.domain = domain
        self.contact_email = contact_email
        self.contact_address = contact_address
        self.version = version
        self.ext = ext
        self.fulltext = fulltext
        self.created = created
        self.modified = modified

    def __repr__(self):
        return "sellers.json file from %s" % self.domain

    def __eq__(self, other):
        if (not self) or (not other):
            return False
        if self.id and other.id and self.id != other.id:
            logging.debug('mismatched id') 
            return False
        if self.domain != other.domain:
            return False
        if self.fulltext != other.fulltext:
            logging.debug('mismatched fulltext')
            return False
        if self.created != other.created:
            return False
        if self.modified != other.modified:
            return False
        return True

    def _persist(self, curs):
        if self.id is not None:
            curs.execute('''UPDATE sellersjson SET domain = %s, contact_email = %s, contact_address = %s, 
                            version = %s, ext = %s, fulltext = %s
                            WHERE id = %s''',
                (self.domain, self.contact_email, self.contact_address,
                 self.version, self.ext, self.fulltext, self.id))
        else:
            curs.execute('''INSERT INTO sellersjson (domain, contact_email, contact_address,
                            version, ext, fulltext)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING id, created, modified''',
                (self.domain, self.contact_email, self.contact_address,
                 self.version, self.ext, self.fulltext))
            (self.id, self.created, self.modified) = curs.fetchone()
        logging.debug("persisted %s" % self)

    def persist(self, cursor=None):
        if cursor and not cursor.closed:
            return self._persist(cursor)
        else:
            with self.eyeball.conn.cursor() as curs:
                self._persist(curs)
                curs.connection.commit()
                return self

    @classmethod
    def parse_file(cls, url):
        domain = urlparse(url).netloc
        if ':' in domain:
            raise NotImplementedError
        fulltext = snarf_file(url, 'sellers')
        entry = cls(domain, fulltext)

    @classmethod
    def lookup_all(cls, sid=None, domain=None):
        (all_sids, all_domains) = (False, False)
        if not sid:
            all_sids = True
        if not domain:
            all_domains = True
        result = []
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('''SELECT domain, contact_email, contact_address, 
                                   version, ext, fulltext, created, modified, id FROM sellersjson WHERE
                            (id = %s OR %s) AND
                            (domain = %s OR %s) 
                            ''', (sid, all_sids, domain, all_domains))
            for row in curs.fetchall():
                result.append(cls(*row))
        return result

#    def __init__(self, domain, contact_email, contact_address, version, ext, fulltext='', created=None, modified=None, sid=None):


    @classmethod
    def lookup_one(cls, aid=None, domain=None):
        tmp = list(cls.lookup_all(aid, domain))
        if len(tmp) == 1:
            return tmp[0]
        else:
            logging.debug("lookup_one adstxt for %s failed with count %d" % (domain, len(tmp)))
            return None


# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
