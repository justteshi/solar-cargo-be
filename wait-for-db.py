import time
import psycopg2
import os
import subprocess

while True:
    try:
        conn = psycopg2.connect(
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host="db",
            port="5432",
        )
        conn.close()
        print("PostgreSQL is ready.")
        break
    except psycopg2.OperationalError:
        print("Waiting for PostgreSQL...")
        time.sleep(2)

print("Running Django migrations...")
subprocess.run(["python", "backend/manage.py", "migrate", "--noinput"], check=True)

# Check if we are in production (by checking settings module)
settings_module = os.getenv("DJANGO_SETTINGS_MODULE", "")
if settings_module.endswith(".prod"):
    print("Production environment detected. Running collectstatic...")
    subprocess.run(["python", "backend/manage.py", "collectstatic", "--noinput"], check=True)
else:
    print("Development environment detected. Skipping collectstatic.")