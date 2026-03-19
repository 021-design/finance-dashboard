from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import pickle
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'finance_dashboard_secret_key_2024'
from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=30)
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ── Database setup ──────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()

init_db()

# ── User model ───────────────────────────────────────────────
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, username, email FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None

# Load ML model
model = pickle.load(open("model/model.pkl", "rb"))
vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))

# ── Routes ───────────────────────────────────────────────────

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, username, email, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            remember = request.form.get('remember') == 'on'
            login_user(User(user[0], user[1], user[2]), remember=remember)
            return redirect(url_for('upload'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed = generate_password_hash(password)

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, hashed))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username or email already exists')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload')
@login_required
def upload():
    return render_template('index.html', username=current_user.username)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    df = pd.read_csv(file)

    col = None
    for c in df.columns:
        if 'transaction' in c.lower() or 'description' in c.lower() or 'narration' in c.lower():
            col = c
            break
    if col is None:
        col = df.columns[1]

    descriptions = df[col].astype(str)
    X = vectorizer.transform(descriptions)
    df['Category'] = model.predict(X)

    amount_col = None
    for c in df.columns:
        if 'withdrawal' in c.lower() or 'debit' in c.lower() or 'amount' in c.lower():
            amount_col = c
            break

    category_totals = {}
    if amount_col:
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce').fillna(0)
        category_totals = df.groupby('Category')[amount_col].sum().to_dict()

    tips = generate_tips(category_totals)

    result = {
        'total_transactions': len(df),
        'category_counts': df['Category'].value_counts().to_dict(),
        'category_totals': {k: round(float(v), 2) for k, v in category_totals.items()},
        'tips': tips
    }

    return jsonify(result)

@app.route('/sample')
@login_required
def sample():
    sample_data = {
        'total_transactions': 120,
        'category_counts': {
            'Transfer': 45, 'Cash Withdrawal': 30,
            'Transport': 20, 'Utilities': 15, 'Income': 10
        },
        'category_totals': {
            'Transfer': 45000, 'Cash Withdrawal': 18000,
            'Transport': 5200, 'Utilities': 3100, 'Income': 0
        },
        'tips': [
            '🚗 You spent ₹5.2K on transport. Consider monthly passes to save money.',
            '💸 You withdrew ₹18K in cash. Using UPI helps track spending better.',
            '💡 Your utility bills are ₹3.1K. Energy-efficient appliances can cut costs.'
        ]
    }
    return jsonify(sample_data)


def format_inr(amount):
    if amount >= 10000000:
        return f"₹{amount/10000000:.1f} Cr"
    elif amount >= 100000:
        return f"₹{amount/100000:.1f} L"
    elif amount >= 1000:
        return f"₹{amount/1000:.1f} K"
    else:
        return f"₹{amount:.0f}"

def generate_tips(totals):
    tips = []
    if totals.get('Transport', 0) > 3000:
        tips.append(f"🚗 You spent {format_inr(totals['Transport'])} on transport. Consider carpooling or monthly passes.")
    if totals.get('Utilities', 0) > 2000:
        tips.append(f"💡 Your utility bills are {format_inr(totals['Utilities'])}. Energy-efficient appliances can cut costs.")
    if totals.get('Cash Withdrawal', 0) > 10000:
        tips.append(f"💸 You withdrew {format_inr(totals['Cash Withdrawal'])} in cash. Using UPI helps track spending better.")
    if not tips:
        tips.append("✅ Your spending looks healthy! Keep tracking to spot savings opportunities.")
    return tips


if __name__ == '__main__':
    app.run(debug=True)