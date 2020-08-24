#!/usr/bin/env python3

import json
import logging
from urllib.parse import urlparse

from utils import path_to_url, snarf_file

class Sellers(object):
    eyeball = None

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
        conn = None
        try:
            if cursor:
                conn = cursor.connection
                self._persist(cursor)
                return self
            else:
                with self.eyeball.conn.cursor() as curs:
                    conn = curs.connection
                    self._persist(curs)
                    conn.commit()
                    return self
        except Exception as e:
            logging.info("Failed to persist %s: %s" % (self, e))
            conn.rollback()
            return None

    @classmethod
    def parse_file(cls, url):
        domain = urlparse(url).netloc
        if ':' in domain:
            domain = domain.split(':')[0]
        fulltext = snarf_file(url, 'sellers')
        entry = cls(domain, fulltext)
        try:
            data = json.loads(fulltext.split('\n\n',1)[1])
        except:
            logging.info("Missing or invalid content for %s" % url)
            return
        with cls.eyeball.conn.cursor() as curs:
            if not entry.persist(cursor=curs):
                return False
            for seller in data['sellers']:
                try:
                    rel = cls.eyeball.relationship.lookup_or_new(account_id=seller.get('seller_id'),
                                                                 source=seller.get('domain'),
                                                                 destination=domain)
                    rel.name = data.get('name')
                    rel.sellersjson = entry
                    rel.is_confidential = data.get('is_confidential', False)
                    rel.seller_type = data.get('seller_type')
                    rel.account_type = data.get('account_type')
                    if rel.account_type:
                        rel.account_type = rel.account_type.upper()
                    rel.certification_authority_id = data.get('certification_authority_id')
                    rel.is_passthrough = data.get('is_passthrough')
                    rel.name = data.get('name')
                    rel.comment = data.get('comment')
                    if rel.is_valid:
                        rel.persist(cursor=curs)
                    else:
                        logging.info('-------------------------------------------------------------------------------')
                        logging.info("Malformed seller entry in %s" % url)
                        logging.info(seller)
                        for err in rel.validation_errors():
                            logging.info(" - %s" % err)
                        logging.info('-------------------------------------------------------------------------------')
                except Exception as e:
                    logging.error("Malformed seller entry in %s not caught by validation" % url)
                    logging.error(seller)
                    logging.error(e)
                    raise
            curs.connection.commit()

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

    @classmethod
    def lookup_one(cls, aid=None, domain=None):
        tmp = list(cls.lookup_all(aid, domain))
        if len(tmp) == 1:
            return tmp[0]
        else:
            return None
            return None

    @classmethod
    def parse_all(cls, max=0):
        for domain in cls.eyeball.relationship.all_sellers():
            if cls.lookup_all(domain=domain):
                logging.info("https://%s/sellers.json already parsed." % domain)
                continue
            try:
                cls.parse_file('https://%s/sellers.json' % domain)
            except FileNotFoundError:
                logging.warning("No sellers file cached for %s" % domain)


# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
