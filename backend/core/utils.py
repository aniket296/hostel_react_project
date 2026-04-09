import os
import subprocess
import tempfile
from datetime import datetime

from django.conf import settings


def _get_mysql_env():
    env = os.environ.copy()
    password = settings.DATABASES["default"].get("PASSWORD")
    if password:
        env["MYSQL_PWD"] = str(password)
    return env


def _build_mysql_connection_args():
    db_settings = settings.DATABASES["default"]
    args = []

    host = db_settings.get("HOST")
    port = db_settings.get("PORT")
    user = db_settings.get("USER")
    name = db_settings.get("NAME")

    if host:
        args.append(f"-h{host}")
    if port:
        args.append(f"-P{port}")
    if user:
        args.append(f"-u{user}")
    if name:
        args.append(name)

    return args


def create_mysql_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"hostel_backup_{timestamp}.sql"

    db_connection_args = _build_mysql_connection_args()
    mysqldump_path = getattr(settings, "MYSQLDUMP_PATH", "mysqldump")
    command = [mysqldump_path, *db_connection_args]

    temp_file = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".sql", delete=False)
    temp_file_path = temp_file.name

    try:
        with temp_file:
            result = subprocess.run(
                command,
                stdout=temp_file,
                stderr=subprocess.PIPE,
                text=True,
                env=_get_mysql_env(),
            )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Backup failed.")

        return temp_file_path, file_name
    except Exception:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise


def restore_mysql_backup(sql_file_path):
    mysql_client_path = getattr(settings, "MYSQL_CLIENT_PATH", "mysql")
    command = [mysql_client_path, *_build_mysql_connection_args()]

    with open(sql_file_path, "r", encoding="utf-8") as sql_file:
        result = subprocess.run(
            command,
            stdin=sql_file,
            stderr=subprocess.PIPE,
            text=True,
            env=_get_mysql_env(),
        )

    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Restore failed.")
