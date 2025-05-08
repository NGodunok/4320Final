from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "your-secret-key"

DB_PATH = "reservations.db"

def validate_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()
    print(result)
    conn.close()
    return result is not None

def get_reservations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reservations")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        if validate_login(user, pw):
            session['admin'] = user
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))

    reservations = get_reservations()

    # Generate 12x4 chart with 'O'
    chart = [['O' for _ in range(4)] for _ in range(12)]
    cost_matrix = get_cost_matrix()
    total_sales = 0

    for r in reservations:
        row, col = r[3], r[4]  # seat_row, seat_col
        chart[row - 1][col - 1] = 'X'
        total_sales += cost_matrix[row - 1][col - 1]

    return render_template('admin.html', chart=chart, reservations=reservations, total_sales=total_sales)

@app.route('/delete_reservation/<int:res_id>', methods=['POST'])
def delete_reservation(res_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reservations WHERE id=?", (res_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/reservations')
def reservations():
    if 'admin' not in session:
        return redirect(url_for('login'))
    data = get_reservations()
    return render_template('reservations.html', reservations=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008)
