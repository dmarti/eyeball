#!/usr/bin/env python3

import logging

class Relationship(object):
    eyeball = None

    def __init__(self, source, destination, account_id, rid=None):
        self.id = rid
        self.source = source
        self.destination = destination
        self.account_id = account_id
        self.rid = rid
        if self.source is None or self.destination is None:
            raise NotImplementedError

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
        if self.id is not None:
            curs.execute('''UPDATE relationship set source = %s, destination = %s, account_id = %s
                            WHERE id = %s''',
                (self.source, self.destination, self.account_id, self.id))
        else:
            curs.execute('''INSERT INTO relationship
                            (source, destination, account_id)
                            VALUES (%s, %s, %s) RETURNING id''',
                (self.source, self.destination, self.account_id))
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
    def lookup_all(cls, rid=None, source=None, destination=None, account_id=None):
        (all_rids, all_sources, all_destinations, all_account_ids) = (False, False, False, False)
        if rid is None:
            all_rids = True
        if not source:
            all_source = True
        if not destination:
            all_destinations = True
        if account_id is None:
            all_account_ids = True
        result = []
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('''SELECT source, destination, account_id, id FROM eyeball WHERE
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
    def lookup_one(cls, rid=None, source=None, destination=None):
        try:
            tmp = cls.lookup_all(rid, source, destination)
            if len(tmp) == 1:
                return tmp[0]
            else:
                return None
        except:
            raise NotImplementedError

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
