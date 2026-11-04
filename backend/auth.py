from werkzeug.security import generate_password_hash, check_password_hash
from backend.database import get_db_connection


def register_user(username, email, password):
    username = username.strip()
    email = email.strip().lower()

    if not username or not email or not password:
        return False, "All fields are required."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
            """,
            (username, email, hashed_password)
        )

        connection.commit()
        return True, "Account created successfully!"

    except Exception as error:
        if "UNIQUE constraint failed" in str(error):
            return False, "This email is already registered."

        return False, "Registration failed. Please try again."

    finally:
        connection.close()


def login_user(email, password):
    email = email.strip().lower()

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    )

    user = cursor.fetchone()

    if not user:
        connection.close()
        return None, "Invalid email or password."

    if not check_password_hash(user["password"], password):
        connection.close()
        return None, "Invalid email or password."

    # Record successful login activity
    cursor.execute(
        "INSERT INTO login_activity (user_id) VALUES (?)",
        (user["id"],)
    )

    connection.commit()

    user_data = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"]
    }

    connection.close()

    return user_data, "Login successful!"


def get_user_by_id(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, username, email FROM users WHERE id = ?",
        (user_id,)
    )

    user = cursor.fetchone()
    connection.close()

    return dict(user) if user else None
