# src/database/handlers.py
import psycopg2
import hashlib
import os


def get_database_connection():
    """Connect to the PostgreSQL database server."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )


def hash_password(password):
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    """Register a new user."""
    conn = get_database_connection()
    cur = conn.cursor()

    # Check if user exists
    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False, "Пользователь уже существует"

    # Add new user
    hashed_password = hash_password(password)
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
        (username, hashed_password)
    )
    conn.commit()
    cur.close()
    conn.close()
    return True, "Регистрация успешна"


def verify_user(username, password):
    """Verify user credentials."""
    conn = get_database_connection()
    cur = conn.cursor()

    hashed_password = hash_password(password)
    cur.execute(
        "SELECT id FROM users WHERE username = %s AND password_hash = %s",
        (username, hashed_password)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user[0] if user else None


def add_achievement(description, points, user_id):
    """Add an achievement to the database."""
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO achievements (description, points, user_id) VALUES (%s, %s, %s)",
        (description, points, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_achievements(user_id):
    """Get all achievements for a specific user."""
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, description, points, created_at 
        FROM achievements 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    """, (user_id,))
    achievements = cur.fetchall()
    cur.close()
    conn.close()
    return achievements


def delete_all_achievements(user_id):
    """Delete all achievements for a specific user."""
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM achievements WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()


def delete_achievement(achievement_id, user_id):
    """Delete a specific achievement by its ID and user_id."""
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM achievements WHERE id = %s AND user_id = %s",
        (achievement_id, user_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_achievements_by_category(category, user_id, start_date, end_date):
    """Delete all achievements for a specific user and category within a date range."""
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM achievements 
        WHERE user_id = %s 
        AND description LIKE %s 
        AND DATE(created_at) BETWEEN DATE(%s) AND DATE(%s)
    """, (user_id, f"{category}:%", start_date, end_date))
    conn.commit()
    cur.close()
    conn.close()


def get_user_points(user_id):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(points), 0) as total_points 
        FROM achievements 
        WHERE user_id = %s
    """, (user_id,))
    total_points = cursor.fetchone()[0]
    conn.close()
    return total_points


def get_user_level_info(user_id):
    total_points = get_user_points(user_id)
    level = total_points // 60 + 1
    points_in_level = total_points % 60
    return {
        'level': level,
        'points_in_level': points_in_level,
        'points_to_next': 60 - points_in_level,
        'total_points': total_points
    }