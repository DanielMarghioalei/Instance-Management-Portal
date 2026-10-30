import sqlite3
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, RedirectResponse

database ="app/database/imp.db"


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
            "instance_data": instance_data
        }
    )


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



@app.post("/extensions/create")
def create_extension(
    rollout_name: str = Form(...),
    scope: str = Form(...),
    category_id: int = Form(...),
    description: str = Form(""),
    active: str = Form(None)
):

    conn = sqlite3.connect(database)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            category_code
        FROM rollout_categories
        WHERE category_id = ?
    """, (category_id,))

    category_code = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            MAX(
                CAST(
                    SUBSTR(rollout_code,-4)
                    AS INTEGER
                )
            )
        FROM rollouts
        WHERE scope = ?
        AND category_id = ?
    """, (scope, category_id))

    result = cursor.fetchone()[0]

    next_number = 1 if result is None else result + 1

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
            ?,?,?,?,?,?
        )
    """,
    (
        rollout_code,
        rollout_name,
        category_id,
        description,
        1 if active else 0,
        scope
    ))

    rollout_id = cursor.lastrowid

    conn.commit()

    conn.close()

    return RedirectResponse(
        url=f"/extension/{rollout_id}",
        status_code=303
    )


#######################rollout view

@app.get("/extension/{rollout_id}")
def extension_details(
    request: Request,
    rollout_id: int
):

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.rollout_id,
            r.rollout_code,
            r.rollout_name,
            r.description,
            c.category_name
        FROM rollouts r
        LEFT JOIN rollout_categories c
            ON r.category_id = c.category_id
        WHERE r.rollout_id = ?
    """, (rollout_id,))

    rollout = cursor.fetchone()

    cursor.execute("""
        SELECT
            version_id,
            version_number,
            status,
            created_by,
            created_date,
            CASE
                WHEN LENGTH(notes) > 80
                THEN SUBSTR(notes,1,77) || '...'
                ELSE notes
            END AS notes
        FROM rollout_versions
        WHERE rollout_id = ?
        ORDER BY version_id DESC
    """, (rollout_id,))

    versions = cursor.fetchall()

    cursor.execute("""
        SELECT
            file_name as document_name,
            document_type,
            uploaded_by,
            uploaded_date,
            file_path
        FROM rollout_documents rd
        INNER JOIN rollout_versions rv
            ON rd.version_id = rv.version_id
        WHERE rv.rollout_id = ?
        ORDER BY uploaded_date DESC
    """, (rollout_id,))

    documents = cursor.fetchall()

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

    conn.close()

    return templates.TemplateResponse(
        request,
        "extension_details.html",
        {
            "request": request,
            "rollout": rollout,
            "versions": versions,
            "documents": documents,
            "deployments": deployments
        }
    )
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

#######################dont know what this does lol

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
    version_file: UploadFile = File(...)
):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    saved_file_path = None

    try:
        cursor.execute("""
            SELECT
                r.rollout_code,
                r.rollout_name,
                r.scope,
                c.category_code,
                c.category_id
            FROM rollouts r
            INNER JOIN rollout_categories c
                ON r.category_id = c.category_id
            WHERE r.rollout_id = ?
            order by c.category_id asc
        """, (extension_id,))

        rollout = cursor.fetchone()

        if rollout is None:
            return RedirectResponse(
                url="/extensions",
                status_code=303
            )

        rollout_code = rollout[0]
        rollout_name = rollout[1]
        scope = rollout[2]
        category_code = rollout[3]

        original_file_name = Path(
            version_file.filename or ""
        ).name

        if not original_file_name.lower().endswith(".zip"):
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
                    "rollout_code": rollout_code,
                    "rollout_name": rollout_name,
                    "next_version": next_version,
                    "error": "The rollout package must be a ZIP file."
                },
                status_code=400
            )

        cursor.execute("""
            SELECT
                1
            FROM rollout_versions
            WHERE rollout_id = ?
            AND version_number = ?
        """, (
            extension_id,
            version_number
        ))

        existing_version = cursor.fetchone()

        if existing_version is not None:
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

        version_directory = Path(
            "files",
            "extensions",
            scope,
            category_code,
            rollout_code,
            version_number
        )

        version_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        saved_file_name = (
            f"{rollout_code}.{version_number}.ZIP"
        )

        saved_file_path = (
            version_directory / saved_file_name
        )

        with open(saved_file_path, "wb") as output_file:
            while True:
                content = await version_file.read(
                    1024 * 1024
                )

                if not content:
                    break

                output_file.write(content)

        await version_file.close()

        cursor.execute("""
            INSERT INTO rollout_versions
            (
                rollout_id,
                version_number,
                status,
                artifact_path,
                notes,
                created_by,
                created_date,
                rollout_file
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?
            )
        """, (
            extension_id,
            version_number,
            status,
            str(saved_file_path),
            notes,
            created_by,
            saved_file_name
        ))

        conn.commit()

    except Exception:
        conn.rollback()

        if (
            saved_file_path is not None
            and saved_file_path.exists()
        ):
            saved_file_path.unlink()

        raise

    finally:
        conn.close()

    return RedirectResponse(
        url=f"/extension/{extension_id}",
        status_code=303
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