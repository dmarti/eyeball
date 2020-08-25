CREATE OR REPLACE FUNCTION update_modified_column()   
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified = NOW();
    RETURN NEW;   
END;
$$ language 'plpgsql';

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

DO $$ BEGIN
        CREATE TYPE ads_account_type AS ENUM('DIRECT', 'RESELLER');
EXCEPTION
        WHEN duplicate_object THEN null;
END $$;

-- This table describes publisher/seller relationships.
CREATE TABLE IF NOT EXISTS relationship (
	id SERIAL PRIMARY KEY,
	source TEXT,                              -- ads.txt "domain" / sellers.json seller(domain)       usually publisher
	                                          -- source is null if this is a confidential sellers.json seller
	destination TEXT NOT NULL,                -- ads.txt "adystem" / sellers.json (top level) domain  usually adtech firm
	account_id TEXT,                          -- ads.txt account_id / sellers.json seller_id
	adstxt INT REFERENCES adstxt(id),
	sellersjson INT REFERENCES sellersjson(id),
	is_confidential BOOLEAN default FALSE,
	seller_type seller_seller_type,
	account_type ads_account_type,
	certification_authority_id TEXT,          -- optional
	is_passthrough BOOLEAN default FALSE,
	name TEXT,    -- may be null for confidential records
	domain TEXT,  -- "
	comment TEXT, -- optional
	created TIMESTAMP NOT NULL DEFAULT NOW(),
	modified TIMESTAMP NOT NULL DEFAULT NOW()
);
DROP TRIGGER IF EXISTS update_relationship_modified ON relationship;
CREATE TRIGGER update_relationship_modified BEFORE UPDATE ON relationship FOR EACH ROW EXECUTE PROCEDURE update_modified_column();


