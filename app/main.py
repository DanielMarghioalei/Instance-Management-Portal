import sqlite3
from pathlib import Path
from uuid import uuid4
import fnmatch
import shutil
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, RedirectResponse

ROLLOUT_STORAGE_ROOT = Path("app/uploads/extensions")
ROLLOUT_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

database ="app/database/imp.db"

ROLLOUT_STORAGE_ROOT = Path("app/uploads/extensions")
ROLLOUT_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

ROLLOUT_TEMPLATE_ROOT = Path("app/templates/rollout")

ROLLOUT_PL_TEMPLATE = (
    ROLLOUT_TEMPLATE_ROOT
    / "rollout.pl"
)

BUILD_C_FILES_PL_TEMPLATE = (
    ROLLOUT_TEMPLATE_ROOT
    / "build_c_files.pl"
)

ROLLOUT_README_TEMPLATE = (
    ROLLOUT_TEMPLATE_ROOT
    / "README.txt"
)

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)
 
templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "request": request
        }
    )


@app.get("/search")
def search(request: Request, search: str):

    conn = sqlite3.connect(database)

    cursor = conn.cursor()

    cursor.execute("""
            SELECT
                instances.master_instance AS master_instance_id,
                instances.master_instance,
                GROUP_CONCAT(DISTINCT facilities.customer) AS customers,
                GROUP_CONCAT(DISTINCT facilities.city) AS cities,
                instance_details.version,
                MAX(facility_administrator.email) AS facility_administrator,
                MAX(it_site_support.email) AS it_site_support,
                MAX(it_service_desk.email) AS it_service_desk,
                MAX(it_escalations.email) AS it_escalations
            FROM instances
            LEFT JOIN instance_details
                ON instances.instance_name = instance_details.instance_name
            LEFT JOIN facilities
                ON facilities.master_instance = instances.master_instance
            LEFT JOIN facility_contacts facility_administrator
                ON facility_administrator.facility = facilities.facility
                AND facility_administrator.role = 'facility_administrator'
            LEFT JOIN facility_contacts it_site_support
                ON it_site_support.facility = facilities.facility
                AND it_site_support.role = 'it_site_support'
            LEFT JOIN facility_contacts it_service_desk
                ON it_service_desk.facility = facilities.facility
                AND it_service_desk.role = 'it_service_desk'
            LEFT JOIN facility_contacts it_escalations
                ON it_escalations.facility = facilities.facility
                AND it_escalations.role = 'it_escalations'
            WHERE LOWER(instances.master_instance) LIKE LOWER(?)
                or LOWER(facilities.customer) LIKE LOWER(?)
                or LOWER(facilities.city) LIKE LOWER(?)
            GROUP BY
                instances.master_instance,
                instance_details.version
            ORDER BY
                instances.master_instance
    """,
    (
        f"%{search}%",
        f"%{search}%",
        f"%{search}%"
    ))

    results = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request,
        "search_results.html",
        {
            "request": request,
            "results": results
        }
    )


@app.get("/stack/{master_instance_id}")
def stack(request: Request, master_instance_id: str):

    conn = sqlite3.connect(database)

    cursor = conn.cursor()

    cursor.execute("""
            select 	instances.master_instance, 
                    GROUP_CONCAT(DISTINCT facilities.customer) AS customers,
                    GROUP_CONCAT(DISTINCT facilities.city) AS city
            FROM instances
            LEFT JOIN facilities
                ON facilities.master_instance = instances.master_instance
            WHERE instances.master_instance = ?
            group by instances.master_instance
    """, (master_instance_id,))

    stack = cursor.fetchone()

    cursor.execute("""
            select 	instances.instance_name, 
                    environments.environment_name
            from instances
            left join environments
                on instances.environment_code = environments.environment_code
                where instances.master_instance = ?
            order by environments.environment_id asc
    """, (master_instance_id,))

    instances = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request,
        "stack.html",
        {
            "request": request,
            "stack": stack,
            "instances": instances
        }
    )


@app.get("/instance/{instance_name}")
def instance(request: Request, instance_name: str, facility: str = None):

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            instances.instance_name,
            instances.master_instance,
            instance_details.console_url,
            instance_details.service_url,
            instance_details.refs_url,
            instance_details.version,
            instance_details.authentication_url,
            instance_details.swagger_url
        FROM instances
        LEFT JOIN instance_details
            ON instances.instance_name = instance_details.instance_name
        WHERE instances.instance_name = ?
        """, (instance_name,))

    instance_data = cursor.fetchone()
    
    cursor.execute("""
        SELECT facility
        FROM facilities
        WHERE master_instance = (
            SELECT master_instance
            FROM instances
            WHERE instance_name = ?
        )
        ORDER BY facility
        """, (instance_name,))

    facilities = cursor.fetchall()
    
    if facility is None and facilities:
        facility = facilities[0][0]

    cursor.execute("""
            SELECT
                region,
                country_code,
                city,
                customer,
                facility
            FROM facilities
            WHERE facility = ?
        """, (facility,))

    facility_data = cursor.fetchone()
    
    cursor.execute("""
            SELECT mobile_url
            FROM mobile_url
            WHERE facility = ?
            AND instance_name = ?
        """, (facility, instance_name))

    mobile = cursor.fetchone()

    cursor.execute("""
            SELECT
                MAX(CASE WHEN role = 'facility_administrator' THEN full_name END) AS facility_administrator_name,
                MAX(CASE WHEN role = 'facility_administrator' THEN email END) AS facility_administrator_email,
                MAX(CASE WHEN role = 'facility_administrator' THEN phone END) AS facility_administrator_phone,
                MAX(CASE WHEN role = 'facility_administrator' THEN shift_hours END) AS facility_administrator_hours,

                MAX(CASE WHEN role = 'it_engineer' THEN full_name END) AS it_engineer_name,
                MAX(CASE WHEN role = 'it_engineer' THEN email END) AS it_engineer_email,
                MAX(CASE WHEN role = 'it_engineer' THEN phone END) AS it_engineer_phone,
                MAX(CASE WHEN role = 'it_engineer' THEN shift_hours END) AS it_engineer_hours,

                MAX(CASE WHEN role = 'it_service_desk' THEN full_name END) AS it_service_desk_name,
                MAX(CASE WHEN role = 'it_service_desk' THEN email END) AS it_service_desk_email,
                MAX(CASE WHEN role = 'it_service_desk' THEN phone END) AS it_service_desk_phone,
                MAX(CASE WHEN role = 'it_service_desk' THEN shift_hours END) AS it_service_desk_hours,

                MAX(CASE WHEN role = 'it_site_support' THEN full_name END) AS it_site_support_name,
                MAX(CASE WHEN role = 'it_site_support' THEN email END) AS it_site_support_email,
                MAX(CASE WHEN role = 'it_site_support' THEN phone END) AS it_site_support_phone,
                MAX(CASE WHEN role = 'it_site_support' THEN shift_hours END) AS it_site_support_hours,

                MAX(CASE WHEN role = 'it_escalations' THEN full_name END) AS it_escalations_name,
                MAX(CASE WHEN role = 'it_escalations' THEN email END) AS it_escalations_email,
                MAX(CASE WHEN role = 'it_escalations' THEN phone END) AS it_escalations_phone,
                MAX(CASE WHEN role = 'it_escalations' THEN shift_hours END) AS it_escalations_hours,

                MAX(CASE WHEN role = 'ops_manager_1' THEN full_name END) AS ops_manager_1_name,
                MAX(CASE WHEN role = 'ops_manager_1' THEN email END) AS ops_manager_1_email,
                MAX(CASE WHEN role = 'ops_manager_1' THEN phone END) AS ops_manager_1_phone,
                MAX(CASE WHEN role = 'ops_manager_1' THEN shift_hours END) AS ops_manager_1_hours,

                MAX(CASE WHEN role = 'ops_manager_2' THEN full_name END) AS ops_manager_2_name,
                MAX(CASE WHEN role = 'ops_manager_2' THEN email END) AS ops_manager_2_email,
                MAX(CASE WHEN role = 'ops_manager_2' THEN phone END) AS ops_manager_2_phone,
                MAX(CASE WHEN role = 'ops_manager_2' THEN shift_hours END) AS ops_manager_2_hours,

                MAX(CASE WHEN role = 'general_manager' THEN full_name END) AS general_manager_name,
                MAX(CASE WHEN role = 'general_manager' THEN email END) AS general_manager_email,
                MAX(CASE WHEN role = 'general_manager' THEN phone END) AS general_manager_phone,
                MAX(CASE WHEN role = 'general_manager' THEN shift_hours END) AS general_manager_hours,

                MAX(CASE WHEN role = 'ops_escalations' THEN full_name END) AS ops_escalations_name,
                MAX(CASE WHEN role = 'ops_escalations' THEN email END) AS ops_escalations_email,
                MAX(CASE WHEN role = 'ops_escalations' THEN phone END) AS ops_escalations_phone,
                MAX(CASE WHEN role = 'ops_escalations' THEN shift_hours END) AS ops_escalations_hours

            FROM facility_contacts
            WHERE facility = ?
        """, (facility,))

    contacts = cursor.fetchone()
        # ---------------------------------------------------------
    # Deployments
    # ---------------------------------------------------------

    cursor.execute("""
        SELECT
            rd.deployment_id,
            r.rollout_code,
            rv.version_number,
            rd.deployment_status,
            rd.deployed_by,
            strftime('%d/%m/%Y %H:%M', rd.deployment_date),
            rd.deployment_notes
        FROM rollout_deployments rd
        INNER JOIN rollout_versions rv
            ON rv.version_id = rd.version_id
        INNER JOIN rollouts r
            ON r.rollout_id = rv.rollout_id
        WHERE rd.instance_name = ?
        ORDER BY rd.deployment_id DESC
    """, (instance_name,))

    deployments = cursor.fetchall()

    # ---------------------------------------------------------
    # Rollout versions for deployment request dropdown
    # ---------------------------------------------------------

    cursor.execute("""
        SELECT
            rv.version_id,
            r.rollout_code || '.' || rv.version_number,
            r.rollout_name as short_description
        FROM rollout_versions rv
        INNER JOIN rollouts r
            ON r.rollout_id = rv.rollout_id
        ORDER BY
            r.rollout_code,
            rv.version_number DESC
    """)

    rollout_versions = cursor.fetchall()

    return templates.TemplateResponse(
    request,
    "instance.html",
    {
        "request": request,
        "instance": instance_data,
        "contacts": contacts,
        "facilities": facilities,
        "mobile_url": mobile,
        "selected_facility": facility,
        "facility_data": facility_data,
        "instance_data": instance_data,
        "deployments": deployments,
        "rollout_versions": rollout_versions
    }
    )
    conn.close()

########################################upload and create#####################################new version

def sanitise_filename(filename: str) -> str:
    """
    Remove any supplied directory information.

    Example:
        ../../dangerous.txt -> dangerous.txt
    """

    filename = Path(filename).name.strip()

    if not filename:
        raise ValueError("Invalid filename")

    return filename


def get_matching_rollout_rule(
    cursor: sqlite3.Cursor,
    filename: str
):
    """
    Find all active rules and evaluate them using Python fnmatch.

    Lowest priority number wins.

    Examples:
        INV-ADJ.slexp.msql matches:
            *.slexp.msql priority 10
            *.msql       priority 100

        The priority 10 Integrator rule wins.
    """

    cursor.execute("""
        SELECT
            RULE_ID,
            RULE_NAME,
            FILE_NAME_PATTERN,
            TARGET_DIRECTORY,
            DECISION,
            PRIORITY
        FROM ROLLOUT_FILE_RULE
        WHERE ACTIVE_FLAG = 1
        ORDER BY
            PRIORITY ASC,
            RULE_ID ASC
    """)

    rules = cursor.fetchall()

    matching_rules = []

    for rule in rules:

        (
            rule_id,
            rule_name,
            file_name_pattern,
            target_directory,
            decision,
            priority
        ) = rule

        if fnmatch.fnmatchcase(
            filename.lower(),
            file_name_pattern.lower()
        ):
            matching_rules.append({
                "rule_id": rule_id,
                "rule_name": rule_name,
                "file_name_pattern": file_name_pattern,
                "target_directory": target_directory,
                "decision": decision,
                "priority": priority
            })

    if not matching_rules:
        return None

    winning_priority = matching_rules[0]["priority"]

    winning_rules = [
        rule
        for rule in matching_rules
        if rule["priority"] == winning_priority
    ]

    automatic_targets = {
        rule["target_directory"]
        for rule in winning_rules
        if rule["decision"] == "AUTO"
    }

    if len(automatic_targets) > 1:
        return {
            "rule_id": None,
            "rule_name": "Conflicting rollout rules",
            "file_name_pattern": None,
            "target_directory": None,
            "decision": "MANUAL",
            "priority": winning_priority,
            "reason": (
                "Multiple rules matched at the same priority "
                "with different target directories."
            ),
            "matched_rules": winning_rules
        }

    winning_rule = winning_rules[0]
    winning_rule["matched_rules"] = winning_rules

    return winning_rule


def get_rule_actions(
    cursor: sqlite3.Cursor,
    rule_id: int
):
    cursor.execute("""
        SELECT
            ACTION_ORDER,
            ACTION_TYPE,
            COMMAND_TEMPLATE
        FROM ROLLOUT_FILE_RULE_ACTION
        WHERE RULE_ID = ?
        AND ACTIVE_FLAG = 1
        ORDER BY ACTION_ORDER
    """, (rule_id,))

    return cursor.fetchall()


def generate_rollout_commands(
    actions,
    package_file: str,
    target_directory: str,
    filename: str
):
    commands = []

    csv_family = ""

    if filename.lower().endswith(".csv"):
        csv_family = filename.split("_")[0]

    for (
        action_order,
        action_type,
        command_template
    ) in actions:

        command = command_template.format(
            package_file=package_file,
            target_directory=target_directory or "",
            file_name=filename,
            csv_family=csv_family
        )

        commands.append({
            "action_order": action_order,
            "action_type": action_type,
            "command": command
        })

    return commands
############################## end helper function

@app.post("/extensions/create")
def create_extension(
    rollout_name: str = Form(...),
    scope: str = Form(...),
    category_id: int = Form(...),
    description: str = Form(""),
    active: str = Form(None)
):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT
                category_code
            FROM rollout_categories
            WHERE category_id = ?
        """, (category_id,))

        category = cursor.fetchone()

        if category is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid extension category."
            )

        category_code = category["category_code"]

        cursor.execute("""
            SELECT
                MAX(
                    CAST(
                        SUBSTR(rollout_code, -4)
                        AS INTEGER
                    )
                )
            FROM rollouts
            WHERE scope = ?
            AND category_id = ?
        """, (
            scope,
            category_id
        ))

        result = cursor.fetchone()[0]

        next_number = (
            1
            if result is None
            else result + 1
        )

        rollout_code = (
            f"{scope}_{category_code}_{next_number:04d}"
        )

        cursor.execute("""
            INSERT INTO rollouts
            (
                rollout_code,
                rollout_name,
                category_id,
                description,
                active,
                scope
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?
            )
        """, (
            rollout_code,
            rollout_name.strip(),
            category_id,
            description.strip(),
            1 if active else 0,
            scope
        ))

        rollout_id = cursor.lastrowid

        conn.commit()

        return RedirectResponse(
            url=f"/extension/{rollout_id}/version/new",
            status_code=303
        )

    except sqlite3.IntegrityError as error:
        conn.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "The extension could not be created because "
                "the generated extension code already exists."
            )
        ) from error

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


#############################################################################new version

@app.get("/extensions")
def extensions(request: Request):

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.rollout_id,
            r.rollout_code,
            r.rollout_name,
            c.category_name,
            COALESCE(
                (
                    SELECT version_number
                    FROM rollout_versions rv
                    WHERE rv.rollout_id = r.rollout_id
                    ORDER BY rv.version_id DESC
                    LIMIT 1
                ),
                ''
            ) AS latest_version,
            COALESCE(
                (
                    SELECT status
                    FROM rollout_versions rv
                    WHERE rv.rollout_id = r.rollout_id
                    ORDER BY rv.version_id DESC
                    LIMIT 1
                ),
                ''
            ) AS latest_status,
            (
                SELECT COUNT(*)
                FROM rollout_documents rd
                INNER JOIN rollout_versions rv
                    ON rd.version_id = rv.version_id
                WHERE rv.rollout_id = r.rollout_id
            ) AS document_count,
            (
                SELECT COUNT(*)
                FROM rollout_deployments d
                INNER JOIN rollout_versions rv
                    ON d.version_id = rv.version_id
                WHERE rv.rollout_id = r.rollout_id
            ) AS deployment_count
        FROM rollouts r
        LEFT JOIN rollout_categories c
            ON r.category_id = c.category_id
        WHERE r.active = 1
        ORDER BY r.rollout_code
    """)

    rollouts = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
    request,
    "extensions.html",
    {
        "request": request,
        "rollouts": rollouts
    }
    )
################################NEW ROLLOUT

@app.get("/extensions/new")
def new_extension(request: Request):

    conn = sqlite3.connect(database)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            category_id,
            category_code,
            category_name
        FROM rollout_categories
        ORDER BY category_name
    """)

    categories = cursor.fetchall()

    cursor.execute ("""
        select 
            scope_code, 
            scope_description
        from rollout_scopes
        order by id asc
    """)
    scopes= cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request,
        "create_extension.html",
        {
            "request": request,
            "categories": categories,
            "scopes": scopes
        }
    )




#######################rollout view

@app.get("/extension/{rollout_id}")
def extension_details(
    request: Request,
    rollout_id: int
):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    try:
        # ---------------------------------------------------------
        # Extension header
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                r.rollout_id,
                r.rollout_code,
                r.rollout_name,
                r.description,
                c.category_name,
                r.scope,
                r.active
            FROM rollouts r
            LEFT JOIN rollout_categories c
                ON r.category_id = c.category_id
            WHERE r.rollout_id = ?
        """, (rollout_id,))

        rollout = cursor.fetchone()

        if rollout is None:
            raise HTTPException(
                status_code=404,
                detail="Extension not found."
            )

        # ---------------------------------------------------------
        # Files included in the extension
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                rv.version_id,
                rv.version_number,
                rv.status,

                rvf.version_file_id,
                rvf.original_file_name,
                rvf.package_file,
                rvf.target_directory,
                rvf.decision,
                rvf.generated_commands,
                rvf.manual_reason,
                rvf.active,

                rfr.RULE_NAME AS rule_name,
                rfr.FILE_NAME_PATTERN AS file_name_pattern

            FROM rollout_versions rv

            INNER JOIN rollout_version_files rvf
                ON rv.version_id = rvf.version_id

            LEFT JOIN ROLLOUT_FILE_RULE rfr
                ON rvf.rule_id = rfr.RULE_ID

            WHERE rv.rollout_id = ?
            AND rvf.active = 1

            ORDER BY
                rv.version_id DESC,
                CASE rvf.decision
                    WHEN 'MANUAL' THEN 1
                    WHEN 'IGNORE' THEN 2
                    WHEN 'REJECT' THEN 3
                    ELSE 4
                END,
                rvf.package_file
        """, (rollout_id,))

        rollout_files = cursor.fetchall()

        # ---------------------------------------------------------
        # Versions
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                version_id,
                version_number,
                status,
                created_by,
                created_date,
                CASE
                    WHEN LENGTH(notes) > 80
                    THEN SUBSTR(notes, 1, 77) || '...'
                    ELSE notes
                END AS notes
            FROM rollout_versions
            WHERE rollout_id = ?
            ORDER BY version_id DESC
        """, (rollout_id,))

        versions = cursor.fetchall()

        # ---------------------------------------------------------
        # Documents
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                rd.file_name AS document_name,
                rd.document_type,
                rd.uploaded_by,
                rd.uploaded_date,
                rd.file_path
            FROM rollout_documents rd
            INNER JOIN rollout_versions rv
                ON rd.version_id = rv.version_id
            WHERE rv.rollout_id = ?
            ORDER BY rd.uploaded_date DESC
        """, (rollout_id,))

        documents = cursor.fetchall()

        # ---------------------------------------------------------
        # Deployments
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                rd.instance_name,
                rd.deployment_status,
                rd.deployment_date,
                rd.deployed_by,
                rv.version_number
            FROM rollout_deployments rd
            INNER JOIN rollout_versions rv
                ON rd.version_id = rv.version_id
            WHERE rv.rollout_id = ?
            ORDER BY rd.deployment_date DESC
        """, (rollout_id,))

        deployments = cursor.fetchall()

        # ---------------------------------------------------------
        # Summary counts
        # ---------------------------------------------------------

        file_count = len(rollout_files)

        manual_file_count = sum(
            1
            for rollout_file in rollout_files
            if rollout_file["decision"] in (
                "MANUAL",
                "IGNORE"
            )
        )

        automatic_file_count = sum(
            1
            for rollout_file in rollout_files
            if rollout_file["decision"] == "AUTO"
        )

        return templates.TemplateResponse(
            request,
            "extension_details.html",
            {
                "request": request,
                "rollout": rollout,
                "rollout_files": rollout_files,
                "versions": versions,
                "documents": documents,
                "deployments": deployments,
                "file_count": file_count,
                "automatic_file_count": automatic_file_count,
                "manual_file_count": manual_file_count
            }
        )

    finally:
        conn.close()



###################################################**********************************************************
@app.get("/download-document")
def download_document(file_path: str):

    return FileResponse(
        path=file_path,
        filename=file_path.split("\\")[-1]
    )


################### AUTO FILL extension code ###############
@app.get("/api/next-extension-number")
def next_extension_number(
    scope: str,
    category_id: int
    ):
    
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category_code
        FROM rollout_categories
        WHERE category_id = ?
    """, (category_id,))

    category_code = cursor.fetchone()[0]

    prefix = f"{scope}_{category_code}_"

    cursor.execute("""
        SELECT COUNT(*)
        FROM rollouts
        WHERE rollout_code LIKE ?
    """, (prefix + '%',))

    count = cursor.fetchone()[0] + 1

    conn.close()

    return {
        "code": f"{prefix}{count:04d}"
    }



@app.get("/extension/{extension_id}/document/upload")
def upload_document_page(
    request: Request,
    extension_id: int
):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            version_id,
            version_number
        FROM rollout_versions
        WHERE rollout_id = ?
        ORDER BY version_id DESC
    """, (extension_id,))

    versions = cursor.fetchall()

    conn.close()

    if not versions:
        return RedirectResponse(
            url=f"/extension/{extension_id}/version/new",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "upload_document.html",
        {
            "request": request,
            "extension_id": extension_id,
            "versions": versions
        }
    )

@app.post("/extension/{extension_id}/document/upload")
async def upload_document(
    extension_id: int,
    document_type: str = Form(...),
    version_id: int = Form(...),
    document_file: UploadFile = File(...)
):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT
                r.scope,
                c.category_code,
                r.rollout_code,
                rv.version_number
            FROM rollout_versions rv
            INNER JOIN rollouts r
                ON rv.rollout_id = r.rollout_id
            INNER JOIN rollout_categories c
                ON r.category_id = c.category_id
            WHERE rv.version_id = ?
            AND r.rollout_id = ?
        """, (version_id, extension_id))

        upload_details = cursor.fetchone()

        if upload_details is None:
            return RedirectResponse(
                url=f"/extension/{extension_id}",
                status_code=303
            )

        scope = upload_details[0]
        category_code = upload_details[1]
        rollout_code = upload_details[2]
        version_number = upload_details[3]

        # Keep documents under the documents directory.
        document_directory = Path(
            "files",
            "extensions_documents",
            scope,
            category_code,
            rollout_code,
            version_number
        )

        document_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        # Remove any directory information supplied by the browser.
        file_name = Path(document_file.filename).name

        file_path = document_directory / file_name

        # Save the physical file.
        with open(file_path, "wb") as output_file:
            while content := await document_file.read(1024 * 1024):
                output_file.write(content)

        await document_file.close()

        # Add the document metadata to the database.
        cursor.execute("""
            INSERT INTO rollout_documents
            (
                version_id,
                document_type,
                file_name,
                file_path,
                uploaded_by,
                uploaded_date
            )
            VALUES
            (
                ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
            )
        """, (
            version_id,
            document_type,
            file_name,
            str(file_path),
            "Daniel"
        ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return RedirectResponse(
        url=f"/extension/{extension_id}",
        status_code=303
    )

######################## UPLOAD EXTENSION VERSION ########################


@app.get("/extension/{extension_id}/version/new")
def upload_version_page(
    request: Request,
    extension_id: int
):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                rollout_code,
                rollout_name
            FROM rollouts
            WHERE rollout_id = ?
        """, (extension_id,))

        rollout = cursor.fetchone()

        if rollout is None:
            return RedirectResponse(
                url="/extensions",
                status_code=303
            )

        cursor.execute("""
            SELECT
                MAX(
                    CAST(
                        SUBSTR(version_number, 2)
                        AS INTEGER
                    )
                )
            FROM rollout_versions
            WHERE rollout_id = ?
        """, (extension_id,))

        latest_version_number = cursor.fetchone()[0]

        if latest_version_number is None:
            next_version = "V001"
        else:
            next_version = f"V{latest_version_number + 1:03d}"

        return templates.TemplateResponse(
            request,
            "upload_version.html",
            {
                "request": request,
                "extension_id": extension_id,
                "rollout_code": rollout[0],
                "rollout_name": rollout[1],
                "next_version": next_version,
                "error": None
            }
        )

    finally:
        conn.close()


@app.post("/extension/{extension_id}/version/new")
async def upload_version(
    request: Request,
    extension_id: int,
    version_number: str = Form(...),
    status: str = Form(...),
    created_by: str = Form(...),
    notes: str = Form(""),
    files: list[UploadFile] = File(...)
):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    generated_zip_path = None
    cursor = conn.cursor()

    version_directory = None

    try:
        cursor.execute("BEGIN IMMEDIATE")
        if not ROLLOUT_PL_TEMPLATE.is_file():
            raise HTTPException(
                status_code=500,
                detail=(
                    "The rollout.pl template was not found at "
                    f"{ROLLOUT_PL_TEMPLATE}."
                )
            )

        if not ROLLOUT_README_TEMPLATE.is_file():
            raise HTTPException(
                status_code=500,
                detail=(
                    "The rollout readme template was not found at "
                    f"{ROLLOUT_README_TEMPLATE}."
                )
            )
        if not BUILD_C_FILES_PL_TEMPLATE.is_file():
            raise HTTPException(
                status_code=500,
                detail=(
                    "The rollout 'build_c_files.pl' template was not found at "
                    f"{BUILD_C_FILES_PL_TEMPLATE}."
                )
            )
        # ---------------------------------------------------------
        # Validate extension
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                r.rollout_code,
                r.rollout_name,
                r.scope,
                c.category_code
            FROM rollouts r
            INNER JOIN rollout_categories c
                ON r.category_id = c.category_id
            WHERE r.rollout_id = ?
        """, (extension_id,))

        rollout = cursor.fetchone()

        if rollout is None:
            raise HTTPException(
                status_code=404,
                detail="Extension not found."
            )

        rollout_code = rollout["rollout_code"]
        rollout_name = rollout["rollout_name"]
        scope = rollout["scope"]
        category_code = rollout["category_code"]

        # ---------------------------------------------------------
        # Prevent duplicate version numbers
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                version_id
            FROM rollout_versions
            WHERE rollout_id = ?
            AND version_number = ?
        """, (
            extension_id,
            version_number
        ))

        if cursor.fetchone() is not None:
            return templates.TemplateResponse(
                request,
                "upload_version.html",
                {
                    "request": request,
                    "extension_id": extension_id,
                    "rollout_code": rollout_code,
                    "rollout_name": rollout_name,
                    "next_version": version_number,
                    "error": (
                        f"Version {version_number} already exists "
                        f"for this extension."
                    )
                },
                status_code=400
            )

        # ---------------------------------------------------------
        # Classify uploaded files
        # ---------------------------------------------------------

        analysed_files = []

        for uploaded_file in files:

            if not uploaded_file.filename:
                continue

            filename = sanitise_filename(
                uploaded_file.filename
            )

            rule = get_matching_rollout_rule(
                cursor,
                filename
            )

            if rule is None:
                analysed_files.append({
                    "uploaded_file": uploaded_file,
                    "filename": filename,
                    "decision": "MANUAL",
                    "reason": "No approved rollout rule matched.",
                    "rule": None,
                    "target_directory": None,
                    "package_file": (
                        f"_manual_review/{filename}"
                    ),
                    "commands": []
                })

                continue

            decision = rule["decision"]

            if decision == "REJECT":
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"{filename} was rejected by rule "
                        f"'{rule['rule_name']}'."
                    )
                )

            if decision in ("MANUAL", "IGNORE"):
                analysed_files.append({
                    "uploaded_file": uploaded_file,
                    "filename": filename,
                    "decision": decision,
                    "reason": rule.get(
                        "reason",
                        "Manual classification is required."
                    ),
                    "rule": rule,
                    "target_directory": None,
                    "package_file": (
                        f"_manual_review/{filename}"
                    ),
                    "commands": []
                })

                continue

            target_directory = (
                rule["target_directory"] or ""
            ).strip("/")

            package_file = (
                f"{target_directory}/{filename}"
                if target_directory
                else filename
            )

            actions = get_rule_actions(
                cursor,
                rule["rule_id"]
            )

            commands = generate_rollout_commands(
                actions=actions,
                package_file=package_file,
                target_directory=(
                    f"{target_directory}/"
                    if target_directory
                    else ""
                ),
                filename=filename
            )

            analysed_files.append({
                "uploaded_file": uploaded_file,
                "filename": filename,
                "decision": "AUTO",
                "reason": None,
                "rule": rule,
                "target_directory": target_directory,
                "package_file": package_file,
                "commands": commands
            })

        if not analysed_files:
            raise HTTPException(
                status_code=400,
                detail="At least one file must be uploaded."
            )

        # ---------------------------------------------------------
        # Check duplicate package paths
        # ---------------------------------------------------------

        package_paths = [
            analysed_file["package_file"].lower()
            for analysed_file in analysed_files
        ]

        duplicate_paths = {
            package_path
            for package_path in package_paths
            if package_paths.count(package_path) > 1
        }

        if duplicate_paths:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Multiple files resolved to the same package path: "
                    + ", ".join(sorted(duplicate_paths))
                )
            )

        # ---------------------------------------------------------
        # Create version database row
        # ---------------------------------------------------------

        cursor.execute("""
            INSERT INTO rollout_versions
            (
                rollout_id,
                version_number,
                status,
                notes,
                created_by,
                created_date
            )
            VALUES
            (
                ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
            )
        """, (
            extension_id,
            version_number,
            status,
            notes.strip(),
            created_by.strip()
        ))

        version_id = cursor.lastrowid

        # ---------------------------------------------------------
        # Create physical version directory
        # ---------------------------------------------------------

        version_directory = (
            ROLLOUT_STORAGE_ROOT
            / scope
            / category_code
            / rollout_code
            / version_number
        )

        version_directory.mkdir(
            parents=True,
            exist_ok=False
        )

        # ---------------------------------------------------------
        # Save files and file metadata
        # ---------------------------------------------------------

        generated_commands = []

        for analysed_file in analysed_files:

            uploaded_file = analysed_file["uploaded_file"]
            filename = analysed_file["filename"]
            decision = analysed_file["decision"]
            target_directory = analysed_file[
                "target_directory"
            ]
            package_file = analysed_file["package_file"]
            rule = analysed_file["rule"]

            physical_file = (
                version_directory
                / package_file
            )

            physical_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with physical_file.open("wb") as output_file:
                while True:
                    content = await uploaded_file.read(
                        1024 * 1024
                    )

                    if not content:
                        break

                    output_file.write(content)

            await uploaded_file.close()

            command_text = "\n".join(
                command["command"]
                for command in analysed_file["commands"]
            )

            generated_commands.extend(
                command["command"]
                for command in analysed_file["commands"]
            )

            cursor.execute("""
                INSERT INTO rollout_version_files
                (
                    version_id,
                    original_file_name,
                    package_file,
                    target_directory,
                    rule_id,
                    decision,
                    generated_commands,
                    manual_reason,
                    active
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?, ?, 1
                )
            """, (
                version_id,
                filename,
                package_file,
                target_directory,
                (
                    rule.get("rule_id")
                    if rule
                    else None
                ),
                decision,
                command_text,
                analysed_file["reason"]
            ))

#################################################### ZIP BUILDER HERE

        # ---------------------------------------------------------
        # Build rollout package name
        # Example: GL_LABEL_0003.V001
        # ---------------------------------------------------------

        package_name = (
            f"{rollout_code}.{version_number}"
        )

        # ---------------------------------------------------------
        # Get the version creation date in DD-MM-YYYY format
        # ---------------------------------------------------------

        cursor.execute("""
            SELECT
                strftime(
                    '%d-%m-%Y',
                    created_date
                ) AS formatted_created_date
            FROM rollout_versions
            WHERE version_id = ?
        """, (version_id,))

        version_date_row = cursor.fetchone()

        if (
            version_date_row is None
            or not version_date_row["formatted_created_date"]
        ):
            raise HTTPException(
                status_code=500,
                detail="Could not determine the rollout creation date."
            )

        rollout_creation_date = version_date_row[
            "formatted_created_date"
        ]

        # ---------------------------------------------------------
        # Write generated deployment commands
        #
        # The file is intentionally created without an extension:
        # GL_LABEL_0003.V001
        # ---------------------------------------------------------

        deployment_script = (
            version_directory
            / package_name
        )

        deployment_script.write_text(
            (
                "\n".join(generated_commands) + "\n"
                if generated_commands
                else ""
            ),
            encoding="utf-8"
        )

        # ---------------------------------------------------------
        # Copy the generic rollout.pl & build_c_files.pl template
        # ---------------------------------------------------------

        rollout_pl_destination = (
            version_directory
            / "rollout.pl"
        )

        shutil.copy2(
            ROLLOUT_PL_TEMPLATE,
            rollout_pl_destination
        )
        
        build_c_files_pl_destination = (
            version_directory
            / "build_c_files.pl"
        )

        shutil.copy2(
            BUILD_C_FILES_PL_TEMPLATE,
            build_c_files_pl_destination
        )



        # ---------------------------------------------------------
        # Build the rollout readme from its template
        # ---------------------------------------------------------

        readme_template_content = (
            ROLLOUT_README_TEMPLATE.read_text(
                encoding="utf-8"
            )
        )

        readme_content = (
            readme_template_content
            .replace(
                "<CURENT_DATE_FILED>",
                rollout_creation_date
            )
            .replace(
                "<ROLLOUT_NUMBER>",
                package_name
            )
        )

        readme_destination = (
            version_directory
            / "rollout.readme"
        )

        readme_destination.write_text(
            readme_content,
            encoding="utf-8"
        )

        # ---------------------------------------------------------
        # Generate ZIP package
        # ---------------------------------------------------------

        zip_base_path = (
            version_directory.parent
            / package_name
        )

        generated_zip = shutil.make_archive(
            base_name=str(zip_base_path),
            format="zip",
            root_dir=str(version_directory)
        )

        generated_zip_path = Path(generated_zip)

#################################################### END ZIP BUILDER

        generated_zip_path = Path(generated_zip)

        # ---------------------------------------------------------
        # Update version with generated artifact
        # ---------------------------------------------------------

        cursor.execute("""
            UPDATE rollout_versions
            SET
                artifact_path = ?,
                rollout_file = ?
            WHERE version_id = ?
        """, (
            str(generated_zip_path),
            generated_zip_path.name,
            version_id
        ))

        conn.commit()

        return RedirectResponse(
            url=f"/extension/{extension_id}",
            status_code=303
        )

    except HTTPException:
        conn.rollback()

        if (
            version_directory is not None
            and version_directory.exists()
        ):
            shutil.rmtree(version_directory)
        if (
        generated_zip_path is not None
        and generated_zip_path.exists()
        ):
            generated_zip_path.unlink()
        raise

    except sqlite3.IntegrityError as error:
        conn.rollback()

        if (
            version_directory is not None
            and version_directory.exists()
        ):
            shutil.rmtree(version_directory)
        if (
        generated_zip_path is not None
        and generated_zip_path.exists()
        ):
            generated_zip_path.unlink()
        raise HTTPException(
            status_code=409,
            detail=(
                "The version could not be created because "
                "a duplicate version or package path exists."
            )
        ) from error

    except Exception:
        conn.rollback()

        if (
            version_directory is not None
            and version_directory.exists()
        ):
            shutil.rmtree(version_directory)
        if (
        generated_zip_path is not None
        and generated_zip_path.exists()
        ):
            generated_zip_path.unlink()
        raise

    finally:
        conn.close()

@app.get("/extension/version/{version_id}/download")
def download_extension_version(version_id: int):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row

    try:
        version = conn.execute(
            """
            SELECT
                version_id,
                version_number,
                artifact_path,
                rollout_file
            FROM rollout_versions
            WHERE version_id = ?
            """,
            (version_id,)
        ).fetchone()

    finally:
        conn.close()

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Extension version not found."
        )

    if not version["artifact_path"]:
        raise HTTPException(
            status_code=404,
            detail="No downloadable package exists for this version."
        )

    artifact_path = Path(version["artifact_path"])

    if not artifact_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=(
                "The extension package exists in the database, "
                "but the ZIP file was not found on disk."
            )
        )

    download_name = (
        version["rollout_file"]
        or artifact_path.name
    )

    return FileResponse(
        path=artifact_path,
        filename=download_name,
        media_type="application/zip"
    )

################to develop:
@app.get("/documentation")
def documentation(request: Request):

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            document_id,
            document_name,
            uploaded_by,
            uploaded_date,
            file_path
        FROM documentation
        ORDER BY uploaded_date DESC
    """)

    documents = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request,
        "documentation.html",
        {
            "request": request,
            "documents": documents
        }
    )

@app.get("/documentation/upload")
def documentation_upload_page(request: Request):

    return templates.TemplateResponse(
        request,
        "documentation_upload.html",
        {
            "request": request
        }
    )

@app.post("/documentation/upload")
async def documentation_upload(
    document_file: UploadFile = File(...)
):

    directory = Path(
        "files",
        "documentation"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    file_name = Path(
        document_file.filename
    ).name

    file_path = directory / file_name

    with open(file_path, "wb") as output_file:

        while content := await document_file.read(1024 * 1024):
            output_file.write(content)

    conn = sqlite3.connect(database)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO documentation
        (
            document_name,
            file_path,
            uploaded_by
        )
        VALUES
        (
            ?, ?, ?
        )
    """, (
        file_name,
        str(file_path),
        "Daniel"
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(
        "/documentation",
        status_code=303
    )

@app.get("/improvements")
def improvements(request: Request):

    return templates.TemplateResponse(
        request,
        "improvements.html",
        {
            "request": request,
            "submitted": False
        }
    )

@app.post("/improvements")
def submit_improvement(
    request: Request,
    description: str = Form(...),
    submitted_name: str = Form(""),
    submitted_email: str = Form("")
):

    conn = sqlite3.connect(database)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO improvements
        (
            description,
            submitted_name,
            submitted_email,
            acknowledged
        )
        VALUES
        (
            ?,?,?,0
        )
    """, (
        description,
        submitted_name,
        submitted_email
    ))

    conn.commit()
    conn.close()

    return templates.TemplateResponse(
        request,
        "improvements.html",
        {
            "request": request,
            "submitted": True
        }
    )

@app.get("/training")
def training(
    request: Request,
    search: str = ""
):

    conn = sqlite3.connect(database)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            training_id,
            training_name,
            description,
            cost,
            category,
            application
        FROM training_courses
        WHERE active = 1
        AND
        (
            training_name LIKE ?
            OR description LIKE ?
            OR category LIKE ?
            OR application LIKE ?
        )
        ORDER BY training_name
    """,
    (
        f"%{search}%",
        f"%{search}%",
        f"%{search}%",
        f"%{search}%"
    ))

    training_courses = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request,
        "training.html",
        {
            "request": request,
            "training_courses": training_courses,
            "search": search
        }
    )

@app.get("/training/request/{training_id}")
def training_request_page(
    request: Request,
    training_id: int
):

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            training_id,
            training_name,
            description,
            cost
        FROM training_courses
        WHERE training_id = ?
    """, (training_id,))

    training = cursor.fetchone()

    conn.close()

    return templates.TemplateResponse(
        request,
        "training_request.html",
        {
            "request": request,
            "training": training
        }
    )

@app.post("/training/request/{training_id}")
def submit_training_request(
    training_id: int,
    requester_name: str = Form(...),
    requester_email: str = Form(...),
    comments: str = Form("")
):

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO training_requests
        (
            training_id,
            requester_name,
            requester_email,
            comments,
            processed
        )
        VALUES
        (
            ?,?,?,?,0
        )
    """, (
        training_id,
        requester_name,
        requester_email,
        comments
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(
        "/training",
        status_code=303
    )


@app.post("/deployments/create")
def create_deployment(
    version_id: int = Form(...),
    instance_name: str = Form(...),
    deployment_date: str = Form(...),
    deployment_time: str = Form(...),
    deployment_notes: str = Form("")
):

    scheduled_date = (
        f"{deployment_date} {deployment_time}:00"
    )

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO rollout_deployments
            (
                version_id,
                instance_name,
                deployment_status,
                deployment_notes,
                requested_by,
                scheduled_date
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?
            )
        """, (
            version_id,
            instance_name,
            "PENDING",
            deployment_notes.strip(),
            "Daniel",
            scheduled_date
        ))

        conn.commit()

    finally:
        conn.close()

    return RedirectResponse(
        url=f"/instance/{instance_name}",
        status_code=303
    )


######################### deployment log view


@app.get("/instance/view_log/{deployment_id}")
def view_log(deployment_id: int):

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT deployment_log
        FROM rollout_deployments
        WHERE deployment_id = ?
    """, (deployment_id,))

    row = cursor.fetchone()

    conn.close()

    return {
        "log": row[0] if row and row[0] else "No deployment log found"
    }



######JOBS 

def generate_email_inserts(
    job_id,
    recipients
):

    inserts = []
    #add SMTP server in case it doesnt exist - The catch(@?) will handle the error, in case the record already exists...
    inserts.append("""
                    [insert
                        into poldat(polcod, polvar, polval, wh_id_tmpl, srtseq, rtstr1, rtstr2, rtnum1, rtnum2, rtflt1, rtflt2, moddte, mod_usr_id, grp_nam)
                        values ('SYSTEM-INFORMATION', 'SMTP-SERVER', 'HOSTNAME', '----', '1', 'mailrelay.mcl.com', '', '1', '0', '0', '0', to_date('20261111154544', 'YYYYMMDDHH24MISS'), 'NOUSER', 'WMS_REPORTING')] catch(@?);
                    """)
    for index, email in enumerate(
        recipients,
        start=1
    ):
        inserts.append(
    f"""[insert into poldat (polcod,polvar,polval,wh_id_tmpl,srtseq,rtstr1,rtstr2,rtnum1,rtnum2,rtflt1,rtflt2,moddte,mod_usr_id,grp_nam)
    values ('SYSTEM-INFORMATION','REPORTS-EMAIL','{job_id}','----','{index}','{email}','','1','0','0','0',to_date('20261111154544', 'YYYYMMDDHH24MISS'),'NOUSER','WMS_REPORTING')];
    """
        )
######### IMPORTANT -> the date should be changed - hopefully youll work with Oracle DB
    return "\n".join(
        inserts
    )

@app.get("/report-jobs")
def report_jobs(request: Request):

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            instance_name
        FROM instances
        ORDER BY instance_name
    """)
    instances = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse(
        request,
        "report_jobs.html",
        {
            "request": request,
            "instances": instances
        }
    )


def generate_job_definition(
    job_id,
    job_name,
    sender_email,
    email_subject,
    email_message,
    schedule_type,
    cron_expression,
    timer_seconds,
    file_names,
    sql_texts
):
    report_file_section = ""
    for i, file_name in enumerate(
        file_names,
        start=1
    ):
        if not file_name.lower().endswith(
            ".csv"
        ):
            file_name += ".csv"
        report_file_section += (
            f"\n and report_file_name{i} = '{file_name}'"
        )
    body = f"""
    publish data
    where report_directory = '$LESDIR/temp/'
    and email_subject = '{email_subject}'
    and email_message = '{email_message}'
    {report_file_section}
    |
    expand environment variable
    where name = @report_directory
    |
    """

    sql_blocks = ""

    for i, (
        file_name,
        sql_text
    ) in enumerate(
        zip(
            file_names,
            sql_texts
        ),
        start=1
    ):
        sql_blocks += f"""
        {{
        {sql_text}  catch(-1403) >> ress{i}
        |
        if (@ress{i})
        {{
        write csv file
        where filename = @report_file_name{i}
        and path = @value
        and res = @ress{i}
        |
        publish data
        where report_path{i} =
        @value || @report_file_name{i}
        }}
        }}
        |
        """
    attachment_string = []

    for i in range(
        1,
        len(file_names) + 1
    ):

        attachment_string.append(
            f"@report_path{i} || ',' || @report_file_name{i}"
        )

    attachments_clause = (
        " || ';' || ".join(
            attachment_string
        )
    )
    cleanup_section = ""

    for i in range(1, len(file_names) + 1):
        cleanup_section += f"""
        |
        remove file
        where path = @report_path{i}        catch(@?)
        """

    ending = f"""
            [ select distinct (lower(rtstr1)) as email
            from poldat
            WHERE polcod = 'SYSTEM-INFORMATION'
            and polvar = 'REPORTS-EMAIL'
            and polval = '{job_id}'
            and wh_id_tmpl = '----'
            and rtnum1 = '1' ]
            catch(-1403) >> email_ress
            |
            convert column results to string
            where res = @email_ress
            and separator = ';'
            and colnam = 'email'
            |
            publish data
            where recepients_list = @result_string
            |
            [select rtstr1 as smtp_server
              from poldat
            WHERE polcod = 'SYSTEM-INFORMATION'
                and polvar = 'SMTP-SERVER'
                and polval = 'HOSTNAME'
                and wh_id_tmpl = '----'
                and srtseq = '1'
                and rtnum1 = '1'  ]

            |
            send email
            where from = '{sender_email}'
            and to = @recepients_list
            and hostname = @smtp_server
            and subject = '{email_subject}'
            and message = @email_message
            and attachments = {attachments_clause}
            """
    command_text = body + sql_blocks + ending + cleanup_section
    if schedule_type == "CRON":

        schedule_value = cron_expression
        timer_value = ""

    else:

        schedule_value = ""
        timer_value = timer_seconds

    return f"""
    [ insert
    into job_definition (job_id,role_id,name,enabled,type,command,log_file,trace_level,overlap,schedule,start_delay,timer,grp_nam)
    values ('{job_id}','','{job_name}','1','{"cron" if schedule_type=="CRON" else "timer"}',
    '{command_text.replace("'", "''")}',
    '$LESDIR/log/{job_id.lower()}.log',
    '*',
    '0',
    '{schedule_value}',
    '0',
    '{timer_value}',
    'WMS_REPORTING'
    ) ];
    """


@app.post("/report-jobs/generate")
async def generate_report_job(
    request: Request
):

    form = await request.form()

    scope = form.get("scope", "").strip()
    action = form.get("action", "").strip()
    recipient_type = form.get(
        "recipient_type",
        ""
    ).strip()

    specifics = form.get(
        "specifics",
        ""
    ).strip()

    job_id = form.get(
        "job_id",
        ""
    ).strip()

    job_name = form.get(
        "job_name",
        ""
    ).strip()

    instance_name = form.get(
        "instance_name",
        ""
    ).strip()

    sender_email = form.get(
        "sender_email",
        ""
    ).strip()

    email_subject = form.get(
        "email_subject",
        ""
    ).strip()

    email_message = form.get(
        "email_message",
        ""
    ).strip()

    schedule_type = form.get(
        "schedule_type",
        "CRON"
    )

    cron_expression = form.get(
        "generated_cron",
        ""
    )

    timer_seconds = form.get(
        "timer_seconds",
        ""
    )

    file_names = form.getlist(
        "file_name"
    )

    sql_texts = form.getlist(
        "sql_text"
    )

    recipients = form.getlist(
        "recipient_email"
    )

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO report_jobs
    (
        job_id,
        job_name,
        scope,
        action,
        recipient_type,
        specifics,
        instance_name,
        sender_email,
        email_subject,
        email_message,
        schedule_type,
        cron_expression,
        timer_seconds,
        created_by
    )
    VALUES
    (
        ?,?,?,?,?,?,?,?,?,?,?,?,?,?
    )
    """,
    (
        job_id,
        job_name,
        scope,
        action,
        recipient_type,
        specifics,
        instance_name,
        sender_email,
        email_subject,
        email_message,
        schedule_type,
        cron_expression,
        timer_seconds,
        "NOUSER"
    ))
    conn.commit()
    conn.close()

    report_job_id = cursor.lastrowid

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    for sequence_number, (
        file_name,
        sql_text
    ) in enumerate(
        zip(
            file_names,
            sql_texts
        ),
        start=1
    ):

        if not file_name.lower().endswith(
            ".csv"
        ):
            file_name += ".csv"

        cursor.execute("""
        INSERT INTO report_job_files
        (
            report_job_id,
            sequence_number,
            file_name,
            sql_text
        )
        VALUES
        (
            ?,?,?,?
        )
        """,
        (
            report_job_id,
            sequence_number,
            file_name,
            sql_text
        ))

    conn.commit()
    conn.close()

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    for email_address in recipients:

        cursor.execute("""
        INSERT INTO report_job_recipients
        (
            report_job_id,
            email_address
        )
        VALUES
        (
            ?,?
        )
        """,
        (
            report_job_id,
            email_address
        ))

    conn.commit()
    conn.close()

    email_inserts = generate_email_inserts(
        job_id,
        recipients
    )
    job_definition_insert = (
        generate_job_definition(
            job_id,
            job_name,
            sender_email,
            email_subject,
            email_message,
            schedule_type,
            cron_expression,
            timer_seconds,
            file_names,
            sql_texts
        )
    )

    return templates.TemplateResponse(
        request,
        "report_job_output.html",
        {
            "request": request,
            "job_id": job_id,
            "email_inserts": email_inserts,
            "job_definition": job_definition_insert,
            "combined_script":
                email_inserts
                + "\n\n"
                + job_definition_insert
        }
    )

