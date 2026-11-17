# app/deployment_worker.py

import sqlite3
import time
from cryptography.fernet import Fernet
from ssh import deploy_rollout

DATABASE = "app/database/imp.db"

#############################################################
#   Security Stuff
#############################################################



with open("app/env/ENCRYPTION_KEY.env", "r") as f:
    ENCRYPTION_KEY = f.read().strip()

CIPHER = Fernet(ENCRYPTION_KEY.encode())


def encrypt_password(password):
    return CIPHER.encrypt(
        password.encode()
    ).decode()


def protect_passwords():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            credential_id,
            password
        FROM instance_credentials
        WHERE password_status = 'PLAINTEXT'
    """)

    rows = cursor.fetchall()

    for credential_id, password in rows:

        if not password:
            continue

        encrypted_password = encrypt_password(password)

        cursor.execute("""
            UPDATE instance_credentials
            SET
                password = ?,
                password_status = 'ENCRYPTED'
            WHERE credential_id = ?
        """, (
            encrypted_password,
            credential_id
        ))

        print(
            f"Encrypted credential {credential_id}"
        )

    conn.commit()
    conn.close()




#############################################################
#   END Security Stuff
#############################################################


def decrypt_password(password):
    return CIPHER.decrypt(
        password.encode()
    ).decode()


print("Deployment Worker Started")

while True:

    try:
        protect_passwords()
        print("Checking deployments...")

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                rd.deployment_id,
                rd.version_id,
                rd.instance_name,
                rv.artifact_path,
                rd.scheduled_date
            FROM rollout_deployments rd
            INNER JOIN rollout_versions rv
                ON rv.version_id = rd.version_id
            WHERE rd.deployment_status = 'PENDING'
            AND rd.scheduled_date BETWEEN
                datetime(CURRENT_TIMESTAMP, '-1 minute')
                AND
                datetime(CURRENT_TIMESTAMP, '+1 minute')
        """)

        deployments = cursor.fetchall()

        for deployment in deployments:

            deployment_id = deployment["deployment_id"]
            version_id = deployment["version_id"]
            instance_name = deployment["instance_name"]
            artifact_path = deployment["artifact_path"]

            print(
                f"Launching deployment "
                f"{deployment_id}"
            )

            print(
                f"Instance: {instance_name}"
            )

            print(
                f"Artifact: {artifact_path}"
            )



            cursor.execute("""
                SELECT
                   DISTINCT
                    HOST,
                    username as USER,
                    password
                FROM instance_credentials
                WHERE instance_name = ?
                """, (instance_name,))

            HOST, USER, encrypted_password = cursor.fetchone()

            PASSWORD = decrypt_password(
                encrypted_password
            )

            cursor.execute("""
                UPDATE rollout_deployments
                SET
                    deployment_status = 'IN_PROGRESS',
                    started_date = CURRENT_TIMESTAMP
                WHERE deployment_id = ?
            """, (deployment_id,))

            conn.commit()

            try:
                # print(f"Host     : {HOST}")
                # print(f"User     : {USER}")
                # print(f"Password : {PASSWORD}")
                deploy_rollout(
                    deployment_id=deployment_id,
                    version_id=version_id,
                    host=HOST,
                    user=USER,
                    password=PASSWORD
                )

                cursor.execute("""
                    UPDATE rollout_deployments
                    SET
                        deployment_status = 'SUCCESS',
                        completed_date = CURRENT_TIMESTAMP,
                        deployment_result = ?
                    WHERE deployment_id = ?
                """, (
                    "Deployment completed successfully",
                    deployment_id
                ))

                conn.commit()

                print(
                    f"Deployment {deployment_id} SUCCESS"
                )

            except Exception as ex:

                cursor.execute("""
                    UPDATE rollout_deployments
                    SET
                        deployment_status = 'FAILED',
                        completed_date = CURRENT_TIMESTAMP,
                        deployment_result = ?
                    WHERE deployment_id = ?
                """, (
                    str(ex),
                    deployment_id
                ))

                conn.commit()

                print(
                    f"Deployment {deployment_id} FAILED"
                )

                print(str(ex))

        conn.close()

    except Exception as ex:

        print(
            f"WORKER ERROR: {str(ex)}"
        )

    time.sleep(30)