import sqlite3
import paramiko
from datetime import datetime


def deploy_rollout(
    deployment_id,
    version_id,
    host,
    user,
    password
    ):

    LOG_LINES = []

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


    DB_PATH = "app/database/imp.db"

# ==========================================================
# GET ROLLOUT DETAILS
# ==========================================================

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM rollout_versions
        WHERE version_id = ?
    """, (version_id,))

    row = cursor.fetchone()

    if not row:
        raise Exception(f"Version ID {version_id} not found")

    LOCAL_ZIP = row["artifact_path"]
    ROLLOUT_FILE = row["rollout_file"]
    ROLLOUT_NAME = ROLLOUT_FILE.replace(".zip", "")

    print(f"Version ID  : {version_id}")
    print(f"Rollout     : {ROLLOUT_NAME}")
    print(f"ZIP         : {LOCAL_ZIP}")

    conn.close()

# ==========================================================
# SSH CONNECT
# ==========================================================

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        hostname=host,
        username=user,
        password=password,
        timeout=10
    )

# ==========================================================
# HELPERS
# ==========================================================

    def run_wms(command):

        full_command = f"sudo su -l wmsadmin -c '{command}'"

        print(f"\n--- {command} ---")

        stdin, stdout, stderr = ssh.exec_command(
            full_command
        )

        out = stdout.read().decode()
        err = stderr.read().decode()

        out = "\n".join(
            line
            for line in out.splitlines()
            if "Setting up the LES" not in line
        )

        err = "\n".join(
            line
            for line in err.splitlines()
            if "Setting up the LES" not in line
        )
        LOG_LINES.append(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        )
        LOG_LINES.append(
            f"\n--- {command} ---"
        )

        if out:
            LOG_LINES.append(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
            )
            LOG_LINES.append(out)

        if err:
            print("ERROR:")
            print(err)

            LOG_LINES.append("ERROR:")
            LOG_LINES.append(err)

        return err

    def run_wms_required(command):

        err = run_wms(command)

        if err:
            raise Exception(err)



# ==========================================================
# VERIFY WMSADMIN
# ==========================================================

    run_wms("whoami")

# ==========================================================
# GET LESDIR
# ==========================================================

    stdin, stdout, stderr = ssh.exec_command(
        "sudo su -l wmsadmin -c 'echo $LESDIR'"
    )

    output = stdout.read().decode()

    output = "\n".join(
        line
        for line in output.splitlines()
        if "Setting up the LES" not in line
    )

    LESDIR = output.strip()
    print(f"LESDIR = {LESDIR}")
    if not LESDIR:
        raise Exception(
            "Unable to determine LESDIR"
        )

# ==========================================================
# LOG HEADER
# ==========================================================
    LOG_LINES.append(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
    )  
    LOG_LINES.append(
    f"""
    Deployment Time : {timestamp}
    Deployment ID   : {deployment_id}
    Version ID      : {version_id}
    Rollout Name    : {ROLLOUT_NAME}
    Uploaded By     : {user}
    LESDIR          : {LESDIR}
    Host            : {host}
    """
    )


# ==========================================================
# CREATE BYADMIN STAGING
# ==========================================================

    print("\nCreating deployment staging folder...")

    ssh.exec_command("mkdir -p /home/byadmin/deployments")
    ssh.exec_command("chmod 755 /home/byadmin")
    ssh.exec_command("chmod 755 /home/byadmin/deployments")

# ==========================================================
# SFTP UPLOAD
# ==========================================================

    REMOTE_ZIP = f"/home/byadmin/deployments/{ROLLOUT_NAME}.zip"
    LOG_LINES.append(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
    )
    LOG_LINES.append(
        f"Uploading {LOCAL_ZIP} to {REMOTE_ZIP}"
    )

    transport = paramiko.Transport((host, 22))

    transport.connect(
        username=user,
        password=password
    )

    sftp = paramiko.SFTPClient.from_transport(transport)

    print("\nUploading ZIP...")

    sftp.put(
        LOCAL_ZIP,
        REMOTE_ZIP
    )

    print("Upload complete.")
    LOG_LINES.append(
    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
    )
    LOG_LINES.append(
        f"Uploaded {LOCAL_ZIP} to {REMOTE_ZIP}"
    )

    sftp.close()
    transport.close()

# ==========================================================
# PREPARE LESDIR
# ==========================================================

    run_wms_required(
        f"mkdir -p {LESDIR}/rollouts/{ROLLOUT_NAME}"
    )

    run_wms_required(
        f"mkdir -p {LESDIR}/temp/{ROLLOUT_NAME}"
    )

# ==========================================================
# COPY FILES
# ==========================================================

    run_wms_required(
        f"cp /home/byadmin/deployments/{ROLLOUT_NAME}.zip "
        f"{LESDIR}/temp/{ROLLOUT_NAME}/"
    )

    run_wms_required(
        f"cp /home/byadmin/deployments/{ROLLOUT_NAME}.zip "
        f"{LESDIR}/rollouts/{ROLLOUT_NAME}/"
    )

# ==========================================================
# VERIFY
# ==========================================================

    run_wms_required(
        f"ls -l {LESDIR}/temp/{ROLLOUT_NAME}"
    )

    run_wms_required(
        f"ls -l {LESDIR}/rollouts/{ROLLOUT_NAME}"
    )

# ==========================================================
# UNZIP
# ==========================================================

    run_wms_required(
        f"cd {LESDIR}/rollouts/{ROLLOUT_NAME} && "
        f"unzip -o {ROLLOUT_NAME}.zip"
    )

    run_wms_required(
        f"cd {LESDIR}/rollouts/{ROLLOUT_NAME} && "
        f"ls -la"
    )

# ==========================================================
# DEPLOY
# ==========================================================


    try:

        run_wms_required("rp stop")

        run_wms_required(
            f"cd {LESDIR}/rollouts/{ROLLOUT_NAME} && "
            f"ls -l {ROLLOUT_NAME}"
        )

        run_wms_required(
            f"cd {LESDIR}/rollouts/{ROLLOUT_NAME} && "
            f"cat {ROLLOUT_NAME}"
        )

        run_wms_required(
            f"cd {LESDIR}/rollouts/{ROLLOUT_NAME} && "
            f"perl rollout.pl {ROLLOUT_NAME}"
        )
        run_wms(
            f'cat "$(ls -t {LESDIR}/log/{ROLLOUT_NAME}*.log | head -1)"'
        )

    except Exception as ex:

        LOG_LINES.append(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        )
        LOG_LINES.append(f"DEPLOYMENT FAILED: {str(ex)}")

        raise

    finally:

        run_wms("rp start")

# ==========================================================
# WRITE LOG
# ==========================================================

    log_file = (
        f"{LESDIR}/log/"
        f"IMP_DEPLOYMENT_{ROLLOUT_NAME}{timestamp}.log"
    )

    log_text = "\n".join(LOG_LINES)

    run_wms(f"""
    mkdir -p {LESDIR}/log

    cat > {log_file} << 'EOF'
    {log_text}
    EOF
    """)

# ==========================================================
# CLEANUP
# ==========================================================

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE rollout_deployments
        SET
            deployment_log = ?
        WHERE deployment_id = ?
    """, (
        log_text,
        deployment_id
    ))

    conn.commit()
    conn.close()

    ssh.close()

    print("\nDeployment complete.")

    return True


