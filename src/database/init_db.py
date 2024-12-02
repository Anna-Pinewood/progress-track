import psycopg2
import os
import time
import sys
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def wait_for_db():
    max_retries = 30
    log(f"Attempting to connect to database at {os.getenv('POSTGRES_HOST')}...")
    log(f"Database: {os.getenv('POSTGRES_DB')}")
    log(f"User: {os.getenv('POSTGRES_USER')}")

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST"),
                database=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD")
            )
            log("Successfully connected to database!")
            return conn
        except psycopg2.OperationalError as e:
            log(f"Failed to connect, attempt {i + 1}: {str(e)}")
            if i < max_retries - 1:
                time.sleep(1)
            else:
                raise Exception("Could not connect to database after maximum retries") from e

def check_table_exists(cur, table_name):
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = %s
        );
    """, (table_name,))
    return cur.fetchone()[0]

def init_db():
    try:
        log("Starting database initialization...")
        conn = wait_for_db()
        cur = conn.cursor()

        # Check tables individually
        users_exist = check_table_exists(cur, 'users')
        achievements_exist = check_table_exists(cur, 'achievements')

        log(f"Tables status - users: {'exists' if users_exist else 'missing'}, "
            f"achievements: {'exists' if achievements_exist else 'missing'}")

        if not users_exist or not achievements_exist:
            log("Creating missing tables...")

            if not users_exist:
                log("Creating users table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password_hash VARCHAR(64) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

            if not achievements_exist:
                log("Creating achievements table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS achievements (
                        id SERIAL PRIMARY KEY,
                        description TEXT NOT NULL,
                        points INTEGER NOT NULL,
                        user_id INTEGER REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

            conn.commit()
            log("Tables created successfully!")
        else:
            log("All required tables exist, skipping initialization")

        # Verify tables
        for table in ['users', 'achievements']:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            log(f"Table {table} contains {count} records")

        cur.close()
        conn.close()
        log("Database initialization completed successfully!")
    except Exception as e:
        log(f"Database initialization error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
