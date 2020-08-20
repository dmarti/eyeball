CREATE OR REPLACE FUNCTION update_modified_column()   
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified = NOW();
    RETURN NEW;   
END;
$$ language 'plpgsql';

-- This table describes publisher/seller relationships.
CREATE TABLE IF NOT EXISTS relationship (
	id SERIAL PRIMARY KEY,
	source TEXT NOT NULL,                     -- ads.txt "domain" / sellers.json seller(domain)       usually publisher
	destination TEXT NOT NULL,                -- ads.txt "adystem" / sellers.json (top level) domain  usually adtech firm
	account_id TEXT,                          -- ads.txt account_id / sellers.json seller_id
	created TIMESTAMP NOT NULL DEFAULT NOW(),
	modified TIMESTAMP NOT NULL DEFAULT NOW()
);
DROP TRIGGER IF EXISTS update_relationship_modified ON adsrecord;
CREATE TRIGGER update_relationship_modified BEFORE UPDATE ON relationship FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- ads.txt files https://iabtechlab.com/wp-content/uploads/2019/03/IAB-OpenRTB-Ads.txt-Public-Spec-1.0.2.pdf
CREATE TABLE IF NOT EXISTS adstxt (
	id SERIAL PRIMARY KEY,
	domain TEXT NOT NULL,
	fulltext TEXT NOT NULL,
	created TIMESTAMP NOT NULL DEFAULT NOW(),
	modified TIMESTAMP NOT NULL DEFAULT NOW()
);
DROP TRIGGER IF EXISTS update_adstxt_modified ON adstxt;
CREATE TRIGGER update_adstxt_modified BEFORE UPDATE ON adstxt FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

DO $$ BEGIN
        CREATE TYPE ads_account_type AS ENUM('DIRECT', 'RESELLER');
EXCEPTION
        WHEN duplicate_object THEN null;
END $$;

-- ads.txt records (lines)
CREATE TABLE IF NOT EXISTS adsrecord (
	id SERIAL PRIMARY KEY,
	adstxt INT REFERENCES adstxt(id),
	-- adsystem and account_id are in a "relationship" record
	relationship INT REFERENCES relationship(id),
	account_type ads_account_type NOT NULL,
	certification_authority_id TEXT,
	created TIMESTAMP NOT NULL DEFAULT NOW(),
	modified TIMESTAMP NOT NULL DEFAULT NOW()
);
DROP TRIGGER IF EXISTS update_adsrecord_modified ON adsrecord;
CREATE TRIGGER update_adsrecord_modified BEFORE UPDATE ON adsrecord FOR EACH ROW EXECUTE PROCEDURE update_modified_column();


DROP VIEW IF EXISTS adsrecord_overview;
CREATE VIEW adsrecord_overview AS
	SELECT relationship.id AS relationship, relationship.source, relationship.destination, relationship.account_id,
	adstxt.id as adstxt, adstxt.domain, 
	adsrecord.id as id, adsrecord.account_type, adsrecord.certification_authority_id, adsrecord.created, adsrecord.modified
	FROM adsrecord LEFT OUTER JOIN relationship ON relationship.id = adsrecord.relationship
	               LEFT OUTER JOIN adstxt ON adsrecord.adstxt = adstxt.id;


-- sellers.json files
CREATE TABLE IF NOT EXISTS sellersjson (
	id SERIAL PRIMARY KEY,
	domain TEXT NOT NULL,
	contact_email TEXT,     -- optional contact email
	contact_address TEXT,   -- optional contact postal address
	version TEXT NOT NULL,  -- version, required
	ext TEXT,               -- optional extensions
	fulltext TEXT,
	created TIMESTAMP NOT NULL DEFAULT NOW(),
	modified TIMESTAMP NOT NULL DEFAULT NOW()
);
DROP TRIGGER IF EXISTS update_sellersjson_modified ON sellersjson;
CREATE TRIGGER update_sellersjson_modified BEFORE UPDATE ON sellersjson FOR EACH ROW EXECUTE PROCEDURE update_modified_column();


-- identifier objects found in sellers.json files
CREATE TABLE IF NOT EXISTS identifier (
	id SERIAL PRIMARY KEY,
	sellersjson INT REFERENCES sellersjson(id),
	name TEXT NOT NULL,
	value TEXT NOT NULL
);

DO $$ BEGIN
        CREATE TYPE seller_seller_type AS ENUM('PUBLISHER', 'INTERMEDIARY', 'BOTH');
EXCEPTION
        WHEN duplicate_object THEN null;
END $$;

-- seller records from sellers.json files
CREATE TABLE IF NOT EXISTS seller (
	id SERIAL PRIMARY KEY,
	sellersjson INT REFERENCES sellersjson(id),
	-- seller_id and publisher "domain" are in a "relationship" record
	is_confidential BOOLEAN default FALSE,
	seller_type seller_seller_type NOT NULL,
	is_passthrough BOOLEAN default FALSE,
	name TEXT,    -- may be null for confidential records
	domain TEXT,  -- "
	comment TEXT, -- optional
	ext TEXT      -- "
);

