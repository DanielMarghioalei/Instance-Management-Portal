CREATE TABLE environments (
    environment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_code TEXT NOT NULL UNIQUE,
    environment_name TEXT NOT NULL
);

CREATE TABLE instances (
    master_instance text NOT NULL,
    instance_name TEXT NOT NULL UNIQUE,
    environment_code TEXT NOT NULL,
    FOREIGN KEY (environment_code)
        REFERENCES environments(environment_code)
);

CREATE TABLE instance_details (
    instance_name text PRIMARY KEY not null,
    version TEXT ,
    console_url TEXT,
    service_url TEXT,
    refs_url TEXT,

    FOREIGN KEY (instance_name)
        REFERENCES instances(instance_name)
);
drop  TABLE facilities
CREATE TABLE facilities (
    facility text NOT NULL,
    master_instance text NOT NULL,
    warehouse_code TEXT NOT NULL,
	region TEXT,
	country_code TEXT,
	city TEXT,
	site_code TEXT,
	customer TEXT
);
drop TABLE mobile_url
CREATE TABLE mobile_url (
    mobile_url_id INTEGER PRIMARY KEY AUTOINCREMENT,
    facility text NOT NULL,
    instance_name text NOT NULL,
    mobile_url TEXT NOT NULL
); 
drop TABLE facility_contacts
CREATE TABLE facility_contacts (
    facility text NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role TEXT,
    shift_hours TEXT
);

