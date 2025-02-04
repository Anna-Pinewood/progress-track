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


def execute_query(query, params=None, fetch=False):
    conn = get_database_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        result = cur.fetchall() if fetch else None
        conn.commit()
        return result
    finally:
        cur.close()
        conn.close()


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


def get_all_users():
    """Return list of tuples (user_id, username) for all users"""
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    conn.close()
    return users


def create_group_colors_table():
    query = '''
    CREATE TABLE IF NOT EXISTS group_colors (
        user_id INTEGER,
        group_name TEXT,
        color TEXT,
        PRIMARY KEY (user_id, group_name),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    '''
    execute_query(query)


def save_group_color(user_id, group_name, color):
    query = '''
    INSERT INTO group_colors (user_id, group_name, color)
    VALUES (%s, %s, %s)
    ON CONFLICT (user_id, group_name) 
    DO UPDATE SET color = EXCLUDED.color
    '''
    execute_query(query, (user_id, group_name, color))


def get_group_colors(user_id):
    query = 'SELECT group_name, color FROM group_colors WHERE user_id = %s'
    results = execute_query(query, (user_id,), fetch=True)
    return {row[0]: row[1] for row in results}

# Add this to your initialization code
create_group_colors_table()
