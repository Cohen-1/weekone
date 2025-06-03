import os
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bc_1.db')

# Upload folder setup
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ------------------ DB INIT ------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            birthday TEXT NOT NULL,
            address TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            image_filename TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ------------------ ROUTES ------------------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        birthday = request.form['birthday']
        address = request.form['address']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        image_file = request.files.get('image')
        image_filename = None
        if image_file and image_file.filename != '':
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image_file.save(image_path)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (name, birthday, address, email, password, image_filename) VALUES (?, ?, ?, ?, ?, ?)",
                (name, birthday, address, email, hashed_password, image_filename)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password_input):
            session['user_id'] = user[0]
            session['email'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, birthday, address, image_filename FROM users WHERE id=?", (session['user_id'],))
    user = c.fetchone()
    conn.close()

    if user:
        name, birthday, address, image_filename = user
        birthday_date = datetime.strptime(birthday, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birthday_date.year - ((today.month, today.day) < (birthday_date.month, birthday_date.day))

        return render_template("dashboard.html", name=name, age=age, address=address, image=image_filename)
    else:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(debug=True)
