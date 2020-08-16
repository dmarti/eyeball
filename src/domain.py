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
        
    def persist(self):
        with self.eyeball.conn.cursor() as curs:
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
            curs.connection.commit()
        assert(self.id is not None)
        return self

    def refresh(self):
        if not self.id:
            self.persist()
        return self.__class__.lookup(wid=self.id)

    @classmethod
    def lookup(cls, did=None, owner=None):
        if not did and not owner:
            return None
        (all_dids, all_owners) = (False, False)
        if not did:
            all_dids = True
        if not owner:
            all_owners = True
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('''SELECT id, domain, owner FROM eyeball WHERE
                            (id = %s OR %s) AND
                            (owner = %s OR %s) 
                            ''', (did, all_dids, owner, all_owners))
            for row in curs.fetchall():
                yield cls(*row)

# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
