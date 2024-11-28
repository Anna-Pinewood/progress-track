# src/database/init_db.py
import psycopg2
import os
import time
import sys

def wait_for_db():
    max_retries = 30
    print(f"Attempting to connect to database at {os.getenv('POSTGRES_HOST')}...")
    print(f"Database: {os.getenv('POSTGRES_DB')}")
    print(f"User: {os.getenv('POSTGRES_USER')}")
    
    for i in range(max_retries):
        try:
            print(f"Connection attempt {i + 1}/{max_retries}")
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST"),
                database=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD")
            )
            print("Successfully connected to database!")
            return conn
        except psycopg2.OperationalError as e:
            print(f"Failed to connect, attempt {i + 1}: {str(e)}")
            if i < max_retries - 1:
                print("Waiting 1 second before retry...")
                time.sleep(1)
            else:
                print("Max retries reached. Could not connect to database.")
                raise Exception("Could not connect to database after maximum retries") from e

def init_db():
    try:
        print("Starting database initialization...")
        conn = wait_for_db()
        cur = conn.cursor()
        
        # Drop existing tables if they exist
        print("Dropping existing tables...")
        cur.execute("""
            DROP TABLE IF EXISTS achievements CASCADE;
            DROP TABLE IF EXISTS users CASCADE;
        """)
        
        # Create users table first
        print("Creating users table...")
        cur.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Then create achievements table with user_id foreign key
        print("Creating achievements table...")
        cur.execute("""
            CREATE TABLE achievements (
                id SERIAL PRIMARY KEY,
                description TEXT NOT NULL,
                points INTEGER NOT NULL,
                user_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        print("Tables created successfully!")
        cur.close()
        conn.close()
        print("Database initialization completed successfully!")
    except Exception as e:
        print(f"Failed to initialize database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()