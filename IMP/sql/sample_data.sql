INSERT INTO facilities
(
    facility,
    master_instance,
    warehouse_code,
    region,
    country_code,
    city,
    site_code,
    customer
)
VALUES

('MIL1','UKMIL_1','MIL1','UKI','UK','Milton Keynes','MIL','Acme Retail'),

('MAN1','UKMAN_1','MAN1','UKI','UK','Manchester','MAN','Global Electronics'),

('LEE1','UKLEE_1','LEE1','UKI','UK','Leeds','LEE','Healthcare Distribution');
INSERT INTO instances
(
    master_instance,
    instance_name,
    environment_code
)
VALUES

('UKMIL_1','UKMILP1','P'),
('UKMIL_1','UKMILT1','T'),
('UKMIL_1','UKMILD1','D'),
('UKMIL_1','UKMILH1','H'),

('UKMAN_1','UKMANP1','P'),
('UKMAN_1','UKMANT1','T'),
('UKMAN_1','UKMAND1','D'),
('UKMAN_1','UKMANH1','H'),

('UKLEE_1','UKLEEP1','P'),
('UKLEE_1','UKLEET1','T'),
('UKLEE_1','UKLEED1','D'),
('UKLEE_1','UKLEEH1','H');INSERT INTO instance_details
(
    instance_name,
    version,
    console_url,
    service_url,
    refs_url,
    authentication_url,
    swagger_url
)
SELECT
    instance_name,

    '2024.1.1',

    'https://demo-url.' || LOWER(instance_name) || '.com:4500/console',

    'https://demo-url.' || LOWER(instance_name) || '.com:4500/service',

    'https://demo-url.' || LOWER(instance_name) || '.com:8080',

    'https://demo-url.' || LOWER(instance_name) || '.com:4500/ws/auth/login?usr_id=<user>&password=<pass>',

    'https://demo-url.' || LOWER(instance_name) || '.com:4500/api/'

FROM instances;INSERT INTO mobile_url
(
    facility,
    instance_name,
    mobile_url
)
SELECT
    f.facility,
    i.instance_name,
    'https://demo-url.' || LOWER(i.instance_name) || '.com:8096'
FROM facilities f
INNER JOIN instances i
    ON f.master_instance = i.master_instance
WHERE i.environment_code IN ('P','T','D');INSERT INTO facility_contacts
(
    facility,
    full_name,
    email,
    phone,
    role,
    shift_hours
)
VALUES

('MIL1','Alex Johnson','alex.johnson@example.com','01234 111111','facility_administrator','09:00-17:30'),
('MIL1','Chris Taylor','chris.taylor@example.com','','it_engineer','09:00-17:30'),
('MIL1','Service Desk','servicedesk@example.com','','it_service_desk','24x7'),
('MIL1','Jordan Smith','jordan.smith@example.com','','it_site_support','09:00-17:30'),
('MIL1','Morgan Lee','morgan.lee@example.com','','it_escalations','09:00-17:30'),

('MAN1','Jamie Wilson','jamie.wilson@example.com','01234 222222','facility_administrator','09:00-17:30'),
('MAN1','Chris Taylor','chris.taylor@example.com','','it_engineer','09:00-17:30'),
('MAN1','Service Desk','servicedesk@example.com','','it_service_desk','24x7'),
('MAN1','Jordan Smith','jordan.smith@example.com','','it_site_support','09:00-17:30'),
('MAN1','Morgan Lee','morgan.lee@example.com','','it_escalations','09:00-17:30'),

('LEE1','Taylor Brown','taylor.brown@example.com','01234 333333','facility_administrator','09:00-17:30'),
('LEE1','Chris Taylor','chris.taylor@example.com','','it_engineer','09:00-17:30'),
('LEE1','Service Desk','servicedesk@example.com','','it_service_desk','24x7'),
('LEE1','Jordan Smith','jordan.smith@example.com','','it_site_support','09:00-17:30'),
('LEE1','Morgan Lee','morgan.lee@example.com','','it_escalations','09:00-17:30');INSERT INTO rollouts
(
    rollout_code,
    rollout_name,
    scope,
    category_id,
    description,
    created_by,
    created_date,
    active
)
VALUES

('GL_REFSPORTAL_0001','Portal Security Enhancement','GL',7,'Security improvements to portal access','Demo User',CURRENT_TIMESTAMP,1),

('CT_MOCACOMMAND_0001','Inventory Validation Command','CT',1,'Inventory validation command','Demo User',CURRENT_TIMESTAMP,1),

('CT_RFSCREEN_0001','Receipt Screen Enhancement','CT',2,'Updated receiving workflow','Demo User',CURRENT_TIMESTAMP,1),

('RG_INTEGRATOR_0001','ERP Inventory Interface','RG',4,'ERP integration for inventory synchronisation','Demo User',CURRENT_TIMESTAMP,1),

('CT_LABEL_0001','Pallet Label Optimisation','CT',5,'Enhanced pallet label design','Demo User',CURRENT_TIMESTAMP,1),

('GL_PAGEBUILDER_0001','Operations Dashboard','GL',3,'Operations KPI dashboard','Demo User',CURRENT_TIMESTAMP,1);INSERT INTO rollout_versions
(
    rollout_id,
    version_number,
    status,
    artifact_path,
    notes,
    created_by,
    created_date,
    approval_status,
    rollout_file
)
VALUES

(1,'V001','Released','files/extensions/portal_v1.zip','Initial release','Demo User',CURRENT_TIMESTAMP,'APPROVED','portal_v1.zip'),

(1,'V002','Testing','files/extensions/portal_v2.zip','Security updates','Demo User',CURRENT_TIMESTAMP,'DRAFT','portal_v2.zip'),

(2,'V001','Released','files/extensions/moca_v1.zip','Initial release','Demo User',CURRENT_TIMESTAMP,'APPROVED','moca_v1.zip'),

(3,'V001','Testing','files/extensions/rf_v1.zip','Receiving enhancements','Demo User',CURRENT_TIMESTAMP,'DRAFT','rf_v1.zip');INSERT INTO rollout_deployments
(
    version_id,
    instance_name,
    deployment_status,
    deployed_by,
    deployment_date,
    deployment_notes
)
VALUES

(1,'UKMILD1','SUCCESS','Demo User',CURRENT_TIMESTAMP,'Deployment completed successfully'),

(1,'UKMILT1','SUCCESS','Demo User',CURRENT_TIMESTAMP,'Business validation complete'),

(2,'UKMILP1','IN_PROGRESS','Demo User',CURRENT_TIMESTAMP,'Awaiting production approval'),

(3,'UKMAND1','SUCCESS','Demo User',CURRENT_TIMESTAMP,'Testing completed successfully');INSERT INTO rollout_documents
(
    version_id,
    document_type,
    file_name,
    file_path,
    uploaded_by,
    uploaded_date
)
VALUES

(1,'FDD','Functional_Design_Document.docx','files/documents/Functional_Design_Document.docx','Demo User',CURRENT_TIMESTAMP),

(1,'Release Notes','Release_Notes.docx','files/documents/Release_Notes.docx','Demo User',CURRENT_TIMESTAMP),

(2,'Test Script','Test_Script.xlsx','files/documents/Test_Script.xlsx','Demo User',CURRENT_TIMESTAMP),

(3,'Technical Design','Technical_Design_Document.docx','files/documents/Technical_Design_Document.docx','Demo User',CURRENT_TIMESTAMP);
INSERT INTO documentation
(
    document_name,
    file_path,
    uploaded_by
)
VALUES

('WMS_User_Guide.pdf','files/documentation/WMS_User_Guide.pdf','Demo User'),

('MOCA_Developer_Guide.pdf','files/documentation/MOCA_Developer_Guide.pdf','Demo User'),

('Integrator_Training_Guide.pdf','files/documentation/Integrator_Training_Guide.pdf','Demo User'),

('SQL_Reference_Guide.pdf','files/documentation/SQL_Reference_Guide.pdf','Demo User'),

('Operations_Handbook.pdf','files/documentation/Operations_Handbook.pdf','Demo User');INSERT INTO improvements
(
    description,
    submitted_name,
    submitted_email,
    acknowledged
)
VALUES

('Add deployment approval workflow','Alex Johnson','alex@example.com',1),

('Add SSO support to the portal','Jordan Smith','jordan@example.com',0),

('Add extension search filters','Taylor Brown','taylor@example.com',0),

('Add deployment rollback capability','Morgan Lee','morgan@example.com',0);INSERT INTO training_requests
(
    training_id,
    requester_name,
    requester_email,
    comments,
    processed
)
VALUES

(1,'Alex Johnson','alex@example.com','New starter onboarding',1),

(2,'Jordan Smith','jordan@example.com','Interested in development training',0),

(17,'Taylor Brown','taylor@example.com','Need SQL reporting skills',0);
