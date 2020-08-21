#!/usr/bin/env python3

import logging

class Relationship(object):
    eyeball = None

    def __init__(self, source, destination, account_id, adstxt=None, sellersjson=None,
                 is_confidential=False, seller_type=None, account_type=None,
                 certification_authority_id=None,
                 is_passthrough=False, name=None, comment=None,
                 created=None, modified=None, rid=None):
        self.source = source
        self.destination = destination
        self.account_id = account_id
        self.adstxt = adstxt
        self.sellersjson = sellersjson
        self.is_confidential = not not is_confidential
        if seller_type:
            self.seller_type = seller_type.upper()
        else:
            self.seller_type = None
        if account_type:
            self.account_type = account_type.upper()
        else:
            self.account_type = None
        self.certification_authority_id = certification_authority_id
        self.is_passthrough = not not is_passthrough
        self.name = name
        self.comment = comment
        self.created = created
        self.modified = modified
        self.id = rid

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
        return True
        
    def _persist(self, curs):
        (aid, jid) = (self.adstxt, self.sellersjson)
        if self.adstxt and not isinstance(self.adstxt, int):
            if not self.adstxt.id:
                self.adstxt.persist()
            aid = self.adstxt.id       
        if self.sellersjson and not isinstance(self.sellersjson, int):
            if not self.sellersjson.id:
                self.sellersjson.persist()
            jid = self.sellersjson.id
        if self.id is not None:
            curs.execute('''UPDATE relationship set source = %s, destination = %s, account_id = %s,
                            adstxt = %s, sellersjson = %s, is_confidential = %s, seller_type = %s,
                            account_type = %s, certification_authority_id = %s, is_passthrough = %s,
                            name = %s, comment = %s, created = %s, modified = %s
                            WHERE id = %s''',
                (self.source, self.destination, self.account_id, aid, jid,
                 self.is_confidential, self.seller_type, self.account_type, self.certification_authority_id,
                 self.is_passthrough, self.name, self.comment, self.created, self.modified, self.id))
        else:
            curs.execute('''INSERT INTO relationship (source, destination, account_id, adstxt, sellersjson,
                            is_confidential, seller_type, account_type, certification_authority_id, is_passthrough,
                            name, comment)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id''', 
                    (self.source, self.destination, self.account_id, aid, jid,
                     self.is_confidential, self.seller_type, self.account_type, self.certification_authority_id,
                     self.is_passthrough, self.name, self.comment))
            self.id = curs.fetchone()[0]
        return self

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

    def refresh(self):
        if not self.id:
            self.persist()
        return self.__class__.lookup(rid=self.id)

    @classmethod
    def lookup_all(cls, rid=None, source=None, destination=None, account_id=None):
        (all_rids, all_sources, all_destinations, all_account_ids) = (False, False, False, False)
        if rid is None:
            all_rids = True
        if not source:
            all_sources = True
        if not destination:
            all_destinations = True
        if account_id is None:
            all_account_ids = True
        else:
            account_id = str(account_id)
        result = []
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('''SELECT source, destination, account_id, adstxt, sellersjson,
                            is_confidential, seller_type, account_type, certification_authority_id,
                            is_passthrough, name, comment, created, modified, id FROM relationship WHERE 
                            (id = %s OR %s) AND
                            (source = %s OR %s) AND
                            (destination = %s OR %s) AND
                            (account_id = %s OR %s)
                            ''', (rid, all_rids, source, all_sources,
                                  destination, all_destinations,
                                  account_id, all_account_ids))
            for row in curs.fetchall():
                result.append(cls(*row))
        return result

    @classmethod
    def lookup_one(cls, rid=None, source=None, destination=None, account_id=None):
        try:
            tmp = cls.lookup_all(rid, source, destination, account_id)
            if len(tmp) == 1:
                return tmp[0]
            else:
                return None
        except:
            raise NotImplementedError

    @classmethod
    def lookup_or_new(cls, rid=None, source=None, destination=None, account_id=None):
        tmp = cls.lookup_one(rid, source, destination, account_id)
        if tmp:
            return tmp
        return cls(source, destination, account_id)

    @classmethod
    def all_sellers(cls):
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('SELECT DISTINCT destination FROM relationship')
            for row in curs.fetchall():
                yield(row[0])

    @classmethod
    def all_sources(cls):
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('SELECT DISTINCT source FROM relationship')
            for row in curs.fetchall():
                yield(row[0])

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
