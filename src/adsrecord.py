#!/usr/bin/env python3

import logging

class AdsRecord(object):
    eyeball = None

    def __init__(self, domain, account_id, account_type, source=None,
                 certification_authority_id=None, adstxt=None, aid=None):
        self.id = aid
        if source is None:
            source = adstxt.domain
        if not domain:
            raise NotImplementedError
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
            if not self.relationship.id:
                self.relationship.persist(cursor=curs)
            if not self.adstxt.id:
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


# FIXME (self, domain, account_id, account_type, source=None, certification_authority_id=None, adstxt=None, aid=None):

# needs objects: 2 domains, 1 relationship, 1 adstxt

    @classmethod
    def lookup_all(cls, aid=None, domain=None, account_id=None, account_type=None,
                   source=None, certification_authority_id=None, adstxt=None):
        (all_aids, all_domains, all_account_ids, all_account_types,
         all_sources, all_certification_authority_ids, all_adstxt) = (False, False, False, False, False, False, False)
        if not aid:
            all_aids = True
        if not domain:
            all_domains = True
        if not account_id:
            all_account_ids = True
        if not account_type:
            all_account_types = True
        result = []
        with cls.eyeball.conn.cursor() as curs:
            curs.execute('''SELECT destination, account_id, account_type, source,
                                   certification_authority_id, adstxt, id
                            FROM adsrecord_overview WHERE
                            (id = %s OR %s) AND
                            (domain = %s OR %s) AND
                            (account_id = %s OR %s) AND
                            (account_type = %s OR %s)
                            ''', (aid, all_aids, domain, all_domains, account_id, all_account_ids,
                                  account_type, all_account_types))
            for row in curs.fetchall():
                result.append(cls(*row))
        return result

    @classmethod
    def lookup_one(cls, aid=None, domain=None, account_id=None, account_type=None,
                   source=None, certification_authority_id=None, adstxt=None):
        tmp = cls.lookup_all(aid, domain, account_id, account_type,
                             source, certification_authority_id, adstxt)
        if len(tmp) == 1:
            return tmp[0]
        else:
            return None


# vim: autoindent textwidth=100 tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python
