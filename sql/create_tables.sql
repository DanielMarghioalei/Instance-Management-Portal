DROP TABLE IF EXISTS instance_details;
DROP TABLE IF EXISTS instance_stack_contacts;
DROP TABLE IF EXISTS instances;
DROP TABLE IF EXISTS instance_stacks;
DROP TABLE IF EXISTS environments;


CREATE TABLE environments (
environment_code TEXT PRIMARY KEY,
environment_name TEXT NOT NULL
);


CREATE TABLE instance_stacks (
stack_id INTEGER PRIMARY KEY AUTOINCREMENT,

stack_name TEXT NOT NULL UNIQUE,

region TEXT NOT NULL,
country_code TEXT NOT NULL,
city TEXT NOT NULL,

customer TEXT NOT NULL
);


CREATE TABLE instances (

instance_id INTEGER PRIMARY KEY AUTOINCREMENT,

stack_id INTEGER NOT NULL,

instance_name TEXT NOT NULL UNIQUE,

country_code TEXT NOT NULL,
site_code TEXT NOT NULL,

environment_code TEXT NOT NULL,

instance_number INTEGER NOT NULL,

FOREIGN KEY (stack_id)
REFERENCES instance_stacks(stack_id),

FOREIGN KEY (environment_code)
REFERENCES environments(environment_code),

UNIQUE (
country_code,
site_code,
environment_code,
instance_number
)
);


CREATE TABLE instance_stack_contacts (

stack_id INTEGER PRIMARY KEY,

facility_administrator TEXT,
it_engineer TEXT,
it_service_desk TEXT,
it_site_support TEXT,

ops_manager_1 TEXT,
ops_manager_2 TEXT,

general_manager TEXT,

it_escalations TEXT,
ops_escalations TEXT,

FOREIGN KEY (stack_id)
REFERENCES instance_stacks(stack_id)
);


CREATE TABLE instance_details (

instance_id INTEGER PRIMARY KEY,

console_url TEXT,
service_url TEXT,
refs_url TEXT,
version_url TEXT,
url_port TEXT,

FOREIGN KEY (instance_id)
REFERENCES instances(instance_id)
);