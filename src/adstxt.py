#!/usr/bin/env python3

import logging
from urllib.parse import urlparse

from utils import path_to_url, snarf_file

class AdsTxt(object):
    eyeball = None

    def __init__(self, domain, fulltext='', created=None, modified=None, aid=None):
        self.id = aid
        self.domain = domain
        self.fulltext = fulltext
        self.created = created
        self.modified = modified

    def __repr__(self):
        return "ads.txt file from %s" % self.domain

    def __eq__(self, other):
        if (not self) or (not other):
            return False
        if self.id and other.id and self.id != other.id:
            return False
        if self.domain != other.domain:
            return False
        if self.fulltext != other.fulltext:
            return False
        if self.created != other.created:
            return False
        if self.modified != other.modified:
            return False
        return True

    def _persist(self, curs):
        if self.id is not None:
            curs.execute('''UPDATE adstxt SET domain = %s, fulltext = %s
                            WHERE id = %s''',
                (self.domain, self.fulltext, self.id))
        else:
            curs.execute('''INSERT INTO adstxt (domain, fulltext)
                            VALUES (%s, %s)
                            RETURNING id, created, modified''',
                (self.domain, self.fulltext))
            (self.id, self.created, self.modified) = curs.fetchone()
        logging.debug("persisted %s" % self)

    def persist(self, cursor=None):
        conn = None
        try:
            if cursor:
                conn = cursor.connection
                return self._persist(cursor)
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
        fulltext = snarf_file(url, 'ads')
        entry = cls(domain, fulltext)
        in_headers = True
        lineno = 0
        with cls.eyeball.conn.cursor() as curs:
            if not entry.persist(cursor=curs):
                return False    
            for line in fulltext.splitlines():
                if not line: # out of headers with 1st blank line
                    in_headers=False
                if in_headers:
                    continue
                lineno += 1
                if '#' in line:
                    (stuff, comment) = line.split('#', 1)
                    line = stuff
                try:
                    line = line.strip()
                    if line.startswith('<'):
                        logging.info("%s looks like HTML. Skipping." % url)
                        logging.info(line)
                        break
                    fields = line.split(',', 3)
                    for i in range(len(fields)):
                        fields[i] = fields[i].strip()
                    (domain, account_id, account_type,
                     certification_authority_id) = (None, None, None, None)
                    if len(fields) == 4:
                        (domain, account_id, account_type, certification_authority_id) = fields
                    elif len(fields) == 3:
                        (domain, account_id, account_type) = fields
                    else:
                        continue
                    rel = cls.eyeball.relationship.lookup_or_new(source=entry.domain,
                                                                 destination=domain, account_id=account_id)
                    rel.account_type = account_type.upper()
                    rel.adstxt = entry
                    rel.certification_authority_id = certification_authority_id
                    if rel.is_valid:
                        rel.persist(cursor=curs)
                    else:
                        logging.info('-------------------------------------------------------------------------------')
                        logging.info("Error on line %d of %s" % (lineno, url))
                        logging.info(line)
                        for err in rel.validation_errors():
                            logging.info(" -  %s" % err)
                        logging.info('-------------------------------------------------------------------------------')
                except Exception as e:
                    logging.error("Failed to parse %s: %s" % (url, e))
                    raise

    @classmethod
    def lookup_all(cls, aid=None, domain=None):
        (all_aids, all_domains) = (False, False)
        if not aid:
            all_aids = True
        if not domain:
            all_domains = True
        result = []
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('''SELECT domain, fulltext, created, modified, id FROM adstxt WHERE
                            (id = %s OR %s) AND
                            (domain = %s OR %s) 
                            ''', (aid, all_aids, domain, all_domains))
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

    @classmethod
    def parse_all(cls, max=0):
        count = 0
        for domain in cls.eyeball.relationship.all_sources():
            if cls.lookup_all(domain=domain):
                logging.info("https://%s/ads.txt already parsed." % domain)
                continue
            try:
                cls.parse_file('https://%s/ads.txt' % domain)
                count += 1
                if count == max:
                    return
            except FileNotFoundError:
                pass


# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
