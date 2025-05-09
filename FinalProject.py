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

def generate_chart_and_sales(reservations):
    chart = [['O' for _ in range(4)] for _ in range(12)]
    cost_matrix = get_cost_matrix()
    total_sales = 0

    for r in reservations:
        row, col = r[2], r[3] 
        chart[row][col] = 'X'
        total_sales += cost_matrix[row][col]

    return chart, total_sales

def generate_eticket(name):
    pattern = "INFOTC4320"
    result = []
    name_letters = list(name)
    pattern_letters = list(pattern)

    # Alternate between name and pattern letters
    max_len = max(len(name_letters), len(pattern_letters))
    for i in range(max_len):
        if i < len(name_letters):
            result.append(name_letters[i])
        if i < len(pattern_letters):
            result.append(pattern_letters[i])

    return ''.join(result)

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
    chart, total_sales = generate_chart_and_sales(reservations)

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

@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    error = None
    success = None

    if request.method == 'POST':
        passenger_name = request.form['passengerName']
        seat_row = int(request.form['seatRow']) - 1  # Convert to 0-indexed
        seat_col = int(request.form['seatColumn'])

        if not (0 <= seat_row < 12 and 0 <= seat_col < 4):
            error = "Invalid seat selection."
        else:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM reservations WHERE seatRow=? AND seatColumn=?", (seat_row, seat_col))
            if cursor.fetchone():
                error = f"Seat {seat_row + 1}{chr(65 + seat_col)} is already taken."
            else:
                eticket = generate_eticket(passenger_name)
                cursor.execute(
                    "INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)",
                    (passenger_name, seat_row, seat_col, eticket)
                )
                conn.commit()
                success = f"Reservation successful! Seat {seat_row + 1}{chr(65 + seat_col)} | eTicket: {eticket}"
            conn.close()

    reservations = get_reservations()
    chart, _ = generate_chart_and_sales(reservations)

    return render_template('reservations.html', chart=chart, error=error, success=success)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008)
