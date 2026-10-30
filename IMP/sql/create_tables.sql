CREATE TABLE documentation (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_by TEXT,
    uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE environments (
    environment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    environment_code TEXT NOT NULL UNIQUE,
    environment_name TEXT NOT NULL
);

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

CREATE TABLE facility_contacts (
    facility text NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role TEXT,
    shift_hours TEXT
);

CREATE TABLE improvements (
    improvement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    submitted_name TEXT,
    submitted_email TEXT,
    acknowledged INTEGER DEFAULT 0,
    submitted_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE instance_details (
    instance_name text PRIMARY KEY not null,
    version TEXT ,
    console_url TEXT,
    service_url TEXT,
    refs_url TEXT, AUTHENTICATION_URL TEXT, SWAGGER_URL TEXT,

    FOREIGN KEY (instance_name)
        REFERENCES instances(instance_name)
);

CREATE TABLE instances (
    master_instance text NOT NULL,
    instance_name TEXT NOT NULL UNIQUE,
    environment_code TEXT NOT NULL,
    FOREIGN KEY (environment_code)
        REFERENCES environments(environment_code)
);

CREATE TABLE "mobile_url" (
    FACILITY TEXT,
    instance_name TEXT,
    mobile_url TEXT
);

CREATE TABLE rollout_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_code TEXT NOT NULL UNIQUE,
    category_name TEXT NOT NULL
);

CREATE TABLE rollout_deployments (
    deployment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    instance_name TEXT NOT NULL,
    deployment_status TEXT NOT NULL,
    deployed_by TEXT,
    deployment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    deployment_notes TEXT
, scheduled_date DATETIME, started_date DATETIME, completed_date DATETIME, deployment_log TEXT, deployment_result TEXT, requested_by TEXT, approved_by TEXT);
CREATE TABLE rollout_documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    document_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_by TEXT,
    uploaded_date DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rollout_scopes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_code TEXT NOT NULL UNIQUE,
    scope_description TEXT NOT NULL
);

CREATE TABLE rollout_versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rollout_id INTEGER NOT NULL,
    version_number TEXT NOT NULL,
    status TEXT NOT NULL,
    artifact_path TEXT,
    notes TEXT,
    created_by TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
, approval_status TEXT DEFAULT 'DRAFT', approved_by TEXT, approved_date DATETIME, rollout_file TEXT);
CREATE TABLE rollouts (
    rollout_id INTEGER PRIMARY KEY AUTOINCREMENT,
    rollout_code TEXT NOT NULL UNIQUE,
    rollout_name TEXT NOT NULL,
    scope TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    description TEXT,
    created_by TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    active INTEGER DEFAULT 1
);

CREATE TABLE training_courses (
    training_id INTEGER PRIMARY KEY AUTOINCREMENT,
    training_name TEXT NOT NULL,
    description TEXT,
    cost REAL DEFAULT 0,
    active INTEGER DEFAULT 1
, category TEXT, application TEXT);
