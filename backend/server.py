
import os
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash
)
from dotenv import load_dotenv

from backend.database import init_db, get_db_connection
from backend.auth import register_user, login_user, get_user_by_id
from backend.rag_engine import RAGEngine


# ---------------------------------------
# 1. Project configuration
# ---------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY is missing from .env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

rag_engine = RAGEngine(api_key)

init_db()


# ---------------------------------------
# 2. Helper functions
# ---------------------------------------

def login_required():
    return "user_id" in session


def get_user_conversation(conversation_id):
    connection = get_db_connection()

    conversation = connection.execute(
        """
        SELECT * FROM conversations
        WHERE id = ? AND user_id = ?
        """,
        (conversation_id, session["user_id"])
    ).fetchone()

    connection.close()
    return conversation


# ---------------------------------------
# 3. Home page
# ---------------------------------------

@app.route("/")
def home():
    if login_required():
        return redirect(url_for("chat"))

    return redirect(url_for("login"))


# ---------------------------------------
# 4. Registration
# ---------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        success, message = register_user(
            username, email, password
        )

        if success:
            flash(message, "success")
            return redirect(url_for("login"))

        flash(message, "error")

    return render_template("register.html")


# ---------------------------------------
# 5. Login
# ---------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "")
        password = request.form.get("password", "")

        user, message = login_user(email, password)

        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect(url_for("chat"))

        flash(message, "error")

    return render_template("login.html")


# ---------------------------------------
# 6. Logout
# ---------------------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------
# 7. Chat page
# ---------------------------------------
@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = get_user_by_id(session["user_id"])

    if not user:
        session.clear()
        return redirect(url_for("login"))

    return render_template("chat.html", user=user)

# ---------------------------------------
# 8. Create a new conversation
# ---------------------------------------

@app.route("/api/conversations", methods=["POST"])
def create_conversation():

    if not login_required():
        return jsonify({"error": "Please log in."}), 401

    connection = get_db_connection()

    cursor = connection.execute(
        """
        INSERT INTO conversations (user_id, title)
        VALUES (?, ?)
        """,
        (session["user_id"], "New Chat")
    )

    conversation_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return jsonify({
        "id": conversation_id,
        "title": "New Chat"
    })


# ---------------------------------------
# 9. Get conversation history
# ---------------------------------------

@app.route("/api/conversations", methods=["GET"])
def get_conversations():

    if not login_required():
        return jsonify({"error": "Please log in."}), 401

    connection = get_db_connection()

    conversations = connection.execute(
        """
        SELECT id, title, created_at
        FROM conversations
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    connection.close()

    return jsonify([dict(item) for item in conversations])


# ---------------------------------------
# 10. Get messages from a conversation
# ---------------------------------------

@app.route("/api/conversations/<int:conversation_id>", methods=["GET"])
def get_conversation(conversation_id):

    if not login_required():
        return jsonify({"error": "Please log in."}), 401

    conversation = get_user_conversation(conversation_id)

    if not conversation:
        return jsonify({"error": "Conversation not found."}), 404

    connection = get_db_connection()

    messages = connection.execute(
        """
        SELECT role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY id ASC
        """,
        (conversation_id,)
    ).fetchall()

    connection.close()

    return jsonify({
        "id": conversation["id"],
        "title": conversation["title"],
        "messages": [dict(item) for item in messages]
    })


# ---------------------------------------
# 11. Delete a conversation
# ---------------------------------------

@app.route("/api/conversations/<int:conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):

    if not login_required():
        return jsonify({"error": "Please log in."}), 401

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM messages
        WHERE conversation_id = ?
        AND conversation_id IN (
            SELECT id FROM conversations WHERE id = ? AND user_id = ?
        )
        """,
        (conversation_id, conversation_id, session["user_id"])
    )

    connection.execute(
        """
        DELETE FROM conversations
        WHERE id = ? AND user_id = ?
        """,
        (conversation_id, session["user_id"])
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Conversation deleted."})


# ---------------------------------------
# 12. Upload PDF documents
# ---------------------------------------

@app.route("/api/upload", methods=["POST"])
def upload_pdf():

    if not login_required():
        return jsonify({"error": "Please log in."}), 401

    files = request.files.getlist("files")

    if not files or not any(file.filename for file in files):
        return jsonify({"error": "Please select a PDF."}), 400

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are allowed."}), 400

    try:
        result = rag_engine.process_pdf(
            files,
            session["user_id"]
        )

        return jsonify(result)

    except Exception as error:
        app.logger.exception("PDF processing failed")
        return jsonify({
            "error": f"PDF processing failed: {str(error)}"
        }), 500


# ---------------------------------------
# 13. Ask Gemini AI
# ---------------------------------------

@app.route("/api/ask", methods=["POST"])
def ask_question():

    if not login_required():
        return jsonify({"error": "Please log in."}), 401

    data = request.get_json(silent=True) or {}

    question = data.get("question", "").strip()
    conversation_id = data.get("conversation_id")

    if not question:
        return jsonify({"error": "Please enter a question."}), 400

    connection = get_db_connection()

    # Create a conversation if needed
    if conversation_id:
        conversation = connection.execute(
            """
            SELECT * FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, session["user_id"])
        ).fetchone()

        if not conversation:
            connection.close()
            return jsonify({"error": "Invalid conversation."}), 404

    else:
        cursor = connection.execute(
            """
            INSERT INTO conversations (user_id, title)
            VALUES (?, ?)
            """,
            (session["user_id"], question[:45])
        )

        conversation_id = cursor.lastrowid

    # Set the title for the first question
    count = connection.execute(
        """
        SELECT COUNT(*) FROM messages
        WHERE conversation_id = ?
        """,
        (conversation_id,)
    ).fetchone()[0]

    if count == 0:
        connection.execute(
            """
            UPDATE conversations
            SET title = ?
            WHERE id = ? AND user_id = ?
            """,
            (question[:45], conversation_id, session["user_id"])
        )

    connection.commit()
    connection.close()

    try:
        user_id = session["user_id"]

        # Use PDF context when documents are uploaded
        if str(user_id) in rag_engine.user_documents:

            result = rag_engine.ask(
                question=question,
                user_id=user_id,
                level=data.get("level", "Beginner"),
                language=data.get("language", "English")
            )

        # Otherwise use normal Gemini chat
        else:

            result = rag_engine.ask_general(
                question=question,
                level=data.get("level", "Beginner"),
                language=data.get("language", "English")
            )

        connection = get_db_connection()

        connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, "user", question)
        )

        connection.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            (conversation_id, "assistant", result["answer"])
        )

        connection.commit()
        connection.close()

        return jsonify({
            "conversation_id": conversation_id,
            "answer": result["answer"],
            "sources": result["sources"]
        })

    except Exception as error:
        app.logger.exception("Gemini request failed")

        return jsonify({
            "error": f"AI response failed: {str(error)}"
        }), 500


# ---------------------------------------
# 14. Health check
# ---------------------------------------

@app.route("/health")
def health():
    return jsonify({
        "status": "ClearMind AI backend is running!"
    })


# ---------------------------------------
# 15. Run Flask server
# ---------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
