#!/usr/bin/env python3

import logging

class Relationship(object):
    eyeball = None

    def __init__(self, source, destination, account_id,
                 adstxt=None, sellersjson=None, rid=None):
        self.id = rid
        self.source = self.eyeball.domain(source)
        self.destination = self.eyeball.domain(destination)
        self.account_id = account_id
        self.adstxt=adstxt
        self.sellersjson=sellersjson
        self.rid = rid

    def __repr__(self):
        return "relationship %s %s" % (self.source, self.destination)

    def __eq__(self, other):
        if (not self) or (not other):
            return False
        if self.id and other.id and self.id != other.id:
            return False
        if self.source != other.source:
            return False
        if self.destination != other.destination:
            return False
        if self.account_id != other.account_id:
            return False
        if self.adstxt != other.adstxt:
            return False
        if self.sellersjson != other.sellersjson:
            return False
        return True
        
    def _persist(self, curs):
        self.source.persist(cursor=curs)
        self.destination.persist(cursor=curs)
        if self.id is not None:
            curs.execute('''UPDATE relationship set source = %s, destination = %s,
                            account_id = %s, adstxt = %s, sellersjson = %s
                            WHERE id = %s''',
                (self.source, self.destination, self.account_id, self.adstxt, self.sellersjson, self.id))
        else:
            curs.execute('''INSERT INTO relationship
                            (source, destination, account_id, adstxt, sellersjson)
                            VALUES (%s, %s, %s, %s, %s) RETURNING id''',
                (self.source.id, self.destination.id, self.account_id,
                 self.adstxt, self.sellersjson))
            self.id = curs.fetchone()[0]
        logging.debug("persisted %s" % self)

    def persist(self, cursor=None):
        if cursor:
            return self._persist(cursor)
        else:
            with self.eyeball.conn.cursor() as curs:
                self._persist(curs)
                curs.connection.commit()
                return self

    def refresh(self):
        if not self.id:
            self.persist()
        return self.__class__.lookup(rid=self.id)

    @classmethod
    def lookup_all(cls, rid=None, source=None, destination=None):
        (all_rids, all_sources, all_destinations) = (False, False, False)
        if not rid:
            all_rids = True
        if not source:
            all_source = True
        if not destination:
            all_destinations = True
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('''SELECT source, destination, account_id, adstxt, sellersjson, id FROM eyeball WHERE
                            (id = %s OR %s) AND
                            (source = %s OR %s) AND
                            (destination = %s OR %s)
                            ''', (rid, all_rids, source, all_sources, destination, all_destinations))
            for row in curs.fetchall():
                yield cls(*row)

    @classmethod
    def lookup_one(cls, rid=None, source=None, destination=None):
        try:
            tmp = list(cls.lookup_all(rid, source, destination))
            if len(tmp) == 1:
                return tmp[0]
            else:
                return None
        except:
            raise NotImplementedError

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
