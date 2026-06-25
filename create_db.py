import os
import sys
import subprocess
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_db_config():
    # Attempt to load settings manually or from .env if needed
    # We fallback to defaults in studio_api/settings.py
    return {
        "name": os.environ.get("DB_NAME", "studio"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", "password"),
        "host": os.environ.get("DB_HOST", "127.0.0.1"),
        "port": os.environ.get("DB_PORT", "5432"),
    }

def create_database():
    config = get_db_config()
    db_name = config["name"]
    print(f"Connecting to PostgreSQL to check database '{db_name}'...")
    
    try:
        # Connect to default 'postgres' database first
        conn = psycopg2.connect(
            dbname="postgres",
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"]
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Database '{db_name}' does not exist. Creating...")
            cursor.execute(f"CREATE DATABASE {db_name};")
            print(f"Database '{db_name}' created successfully!")
        else:
            print(f"Database '{db_name}' already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking/creating database: {e}", file=sys.stderr)
        sys.exit(1)

def run_django_commands():
    python_exe = sys.executable
    if not python_exe:
        python_exe = "python"
        
    print("\n--- Running Migrations ---")
    try:
        subprocess.run([python_exe, "manage.py", "migrate"], check=True)
        print("Migrations applied successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error applying migrations: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n--- Running Project Setup ---")
    try:
        subprocess.run([python_exe, "setup_project.py"], check=True)
        print("Project setup script completed.")
    except subprocess.CalledProcessError as e:
        print(f"Error in project setup: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n--- Seeding Studio Content ---")
    try:
        subprocess.run([python_exe, "seed_studio_content.py"], check=True)
        print("Studio content seeded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error seeding studio content: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    create_database()
    run_django_commands()
    print("\n--- Database Setup Complete! ---")
