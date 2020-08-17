#!/usr/bin/env python3

import logging

class AdsRecord(object):
    eyeball = None

    def __init__(self, source, domain, account_id, account_type,
                 certification_authority_id, adstxt=None, aid=None):
        self.id = aid
        self.relationship = self.eyeball.relationship(source, domain, account_id)
        self.account_type = account_type
        self.certification_authority_id = certification_authority_id
        if adstxt is None:
            self.adstxt = self.eyeball.adstxt(domain)
        else:
            self.adstxt = adstxt

    @property
    def source(self):
        return self.relationship.source

    @property
    def domain(self):
        return self.relationship.destination

    def __repr__(self):
        return "ads.txt record from %s to %s" % (self.source, self.domain)

    def __eq__(self, other):
        if (not self) or (not other):
            return False
        if self.id and other.id and self.id != other.id:
            return False
        if self.relationship != other.relationship:
            return False
        if self.account_type != other.account_type:
            return False
        if self.certification_authority_id != other.certification_authority_id:
            return False
        return True

    def persist(self):
        with self.eyeball.conn.cursor() as curs:
            self.relationship.persist(cursor=curs)
            self.adstxt.persist(cursor=curs)

            if self.id is not None:
                curs.execute('''UPDATE adsrecord SET relationship = %s,
                                account_type = %s,
                                certification_authority_id = %s,
                                adstxt = %s,
                                WHERE id = %s''',
                    (self.relationship.id, self.account_type, self.certification_authority_id,
                     self.adstxt.id, self.id))
            else:
                curs.execute('''INSERT INTO adsrecord (relationship, account_type, certification_authority_id, adstxt)
                                VALUES (%s, %s, %s, %s)
                                RETURNING id''',
                    (self.relationship.id, self.account_type, self.certification_authority_id, self.adstxt.id))
                self.id = curs.fetchone()[0]
            curs.connection.commit()
        assert(self.id is not None)
        logging.debug("persisted %s" % self)
        return self

    def refresh(self):
        if not self.id:
            self.persist()
        return self.__class__.lookup(wid=self.id)

    @classmethod
    def lookup_all(cls, did=None, owner=None):
        if not did and not owner:
            return None
        (all_dids, all_owners) = (False, False)
        if not did:
            all_dids = True
        if not owner:
            all_owners = True
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('''SELECT id, domain, owner FROM domain WHERE
                            (id = %s OR %s) AND
                            (owner = %s OR %s) 
                            ''', (did, all_dids, owner, all_owners))
            for row in curs.fetchall():
                yield cls(*row)

    @classmethod
    def lookup_one(cls, did=None, owner=None):
        try:
            tmp = list(cls.lookup_all(rid, source, destination))
            if len(tmp) == 1:
                return tmp[0]
            else:
                return None
        except:
            raise NotImplementedError


# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
