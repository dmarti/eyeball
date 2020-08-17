#!/usr/bin/env python3

import logging

class AdsTxt(object):
    eyeball = None

    def __init__(self, domain, fulltext='', created=None, modified=None, aid=None):
        self.id = aid
        try:
            domain.domain
            self.domain = domain
        except AttributeError:
            self.domain = self.eyeball.domain(domain)
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
        self.domain.persist(curs)
        if self.id is not None:
            curs.execute('''UPDATE adstxt SET domain = %s, fulltext = %s
                            WHERE id = %s''',
                (self.domain.id, self.fulltext, self.id))
        else:
            curs.execute('''INSERT INTO adstxt (domain, fulltext)
                            VALUES (%s, %s)
                            RETURNING id, created, modified''',
                (self.domain.id, self.fulltext))
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
    def lookup_all(cls, aid=None, domain=None):
        (all_aids, all_domains) = (False, False)
        if not aid:
            all_aids = True
        if not domain:
            all_domains = True
        did = None
        try:
            did = domain.id
        except:
            pass
        with cls.eyeball.conn.cursor() as curs:
            if did is None:
                domain = cls.eyeball.domain.lookup_one(domain=domain, cursor=curs)
                if not domain:
                    return []
                else:
                    did = domain.id
            curs.execute('''SELECT domain, fulltext, created, modified, id FROM adstxt WHERE
                            (id = %s OR %s) AND
                            (domain = %s OR %s) 
                            ''', (aid, all_aids, did, all_domains))
            for row in curs.fetchall():
                tmp = cls(*row)
                tmp.domain = domain
                yield tmp

    @classmethod
    def lookup_one(cls, aid=None, domain=None):
        tmp = list(cls.lookup_all(aid, domain))
        if len(tmp) == 1:
            return tmp[0]
        else:
            logging.debug("lookup_one adstxt for %s failed with count %d" % (domain, len(tmp)))
            return None


# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
