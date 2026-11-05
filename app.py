"""Aplicación Flask mínima: login + dashboard con SQLite, lista para Render."""
import os
import secrets
import sqlite3
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join("data", "app.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
);
"""

SAMPLE_PRODUCTS = [
    ("Teclado mecánico", "Periféricos", 89.90, 34),
    ("Ratón inalámbrico", "Periféricos", 29.50, 120),
    ("Monitor 27''", "Pantallas", 249.00, 15),
    ("Webcam HD", "Video", 59.99, 48),
    ("Auriculares USB", "Audio", 45.00, 62),
    ("Disco SSD 1TB", "Almacenamiento", 74.90, 27),
    ("Hub USB-C", "Accesorios", 35.00, 80),
    ("Micrófono condensador", "Audio", 99.00, 12),
]


def get_db():
    """Devuelve la conexión SQLite asociada a la petición actual."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea el esquema y siembra usuario admin y datos de ejemplo (idempotente)."""
    os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
    db = sqlite3.connect(DATABASE_PATH)
    db.executescript(SCHEMA)
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")
    if not db.execute("SELECT 1 FROM users WHERE username = ?", (admin_user,)).fetchone():
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                   (admin_user, generate_password_hash(admin_pass)))
    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO products (name, category, price, stock) VALUES (?, ?, ?, ?)",
            SAMPLE_PRODUCTS)
    db.commit()
    db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.route("/")
def index():
    return redirect(url_for("dashboard" if "user_id" in session else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if not secrets.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x")):
            abort(400)
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Credenciales inválidas.")
    return render_template("login.html")


@app.post("/logout")
def logout():
    if not secrets.compare_digest(request.form.get("csrf", ""), session.get("csrf", "x")):
        abort(400)
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY id").fetchall()
    stats = db.execute(
        "SELECT COUNT(*) AS total, COALESCE(SUM(stock), 0) AS units, "
        "COALESCE(SUM(price * stock), 0) AS inventory_value FROM products").fetchone()
    return render_template("dashboard.html", products=products, stats=stats)


@app.get("/health")
def health():
    """Endpoint para el health check de Render."""
    return {"status": "ok"}


init_db()

if __name__ == "__main__":
    app.run(debug=True)
