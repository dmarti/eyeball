#!/usr/bin/env python3

import logging

class Domain(object):
    eyeball = None

    def __init__(self, domain, owner=None, did=None):
        self.id = did
        self.domain = domain
        self.owner = owner

    def __repr__(self):
        return "Domain %s with owner %s" % (self.domain, self.owner)

    def __eq__(self, other):
        if (not self) or (not other):
            return False
        if self.id and other.id and self.id != other.id:
            return False
        if self.domain != other.domain:
            return False
        if self.owner != other.owner:
            return False
        return True
        
    def _persist(self, curs):
        if self.id is not None:
            curs.execute('''UPDATE domain set domain = %s, owner = %s
                            WHERE id = %s''',
                (self.domain, self.owner, self.id))
        else:
            curs.execute('''INSERT INTO domain (domain, owner)
                            VALUES (%s, %s)
                            ON CONFLICT (domain) DO UPDATE SET owner = %s
                            RETURNING id''',
                (self.domain, self.owner, self.owner))
            self.id = curs.fetchone()[0]
        logging.debug("persisted %s" % self)

    def persist(self, cursor=None):
        if cursor:
            return self._persist(cursor)
        else:
            with self.eyeball.conn.cursor() as curs:
                self._persist(curs)

    def refresh(self):
        if not self.id:
            self.persist()
        return self.__class__.lookup(wid=self.id)

    @classmethod
    def _lookup_all(cls, did, domain, owner, curs):
        (all_dids, all_domains, all_owners) = (False, False, False)
        if not did:
            all_dids = True
        if not domain:
            all_domains = True
        if not owner:
            all_owners = True
        result = []
        curs.execute('''SELECT domain, owner, id FROM domain WHERE
                        (id = %s OR %s) AND
                        (domain = %s OR %s) AND
                        (owner = %s OR %s) 
                        ''', (did, all_dids, domain, all_domains, owner, all_owners))
        for row in curs.fetchall():
            result.append(cls(*row))
        return result

    @classmethod
    def lookup_all(cls, did=None, domain=None, owner=None, cursor=None):
        logging.debug("cursor is %s" % cursor)
        if cursor and not cursor.closed:
            return cls._lookup_all(did, domain, owner, cursor)
        else:
            with cls.eyeball.conn.cursor() as curs:
                return cls._lookup_all(did, domain, owner, curs)

    @classmethod
    def lookup_one(cls, did=None, domain=None, owner=None, cursor=None):
        tmp = list(cls.lookup_all(did, domain, owner, cursor))
        if len(tmp) == 1:
            return tmp[0]
        else:
            logging.debug("lookup of %s failed with count %d" % (domain, len(tmp)))
            return None

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
