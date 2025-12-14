# Monita–Monito with Manual Pairing + Simple UI Design

from flask import Flask, render_template_string, request, redirect, session
import random, sqlite3

app = Flask(__name__)
app.secret_key = "secret-key"
DB = "monita.db"

# ---------------- DB ----------------
def db():
    return sqlite3.connect(DB)

with db() as con:
    con.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        code TEXT PRIMARY KEY,
        paired INTEGER DEFAULT 0
    )
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        real_name TEXT,
        codename TEXT,
        group_code TEXT
    )
    """)
    con.execute("""
    CREATE TABLE IF NOT EXISTS pairs (
        giver INTEGER,
        receiver INTEGER,
        group_code TEXT
    )
    """)

# ---------------- ADMIN ----------------
@app.route('/admin/create')
def admin_create():
    code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
    with db() as con:
        con.execute("INSERT INTO groups VALUES (?,0)", (code,))
    return render_template_string('''
    <html><head><title>Group Created</title>
    <style>
    body { font-family: Arial; background: #ffe6f0; text-align:center; padding:50px; }
    a { color:#ff3399; text-decoration:none; font-weight:bold; }
    </style>
    </head><body>
    <h2>Group Created ✅</h2>
    <p>Group Code: <b>{{code}}</b></p>
    <a href='/'>Go to Join Page</a>
    </body></html>
    ''', code=code)

@app.route('/admin/pair/<code>')
def admin_pair(code):
    with db() as con:
        users = con.execute("SELECT id FROM users WHERE group_code=?", (code,)).fetchall()
        if len(users) < 2:
            return "Need at least 2 members"
        existing_pairs = con.execute("SELECT * FROM pairs WHERE group_code=?", (code,)).fetchone()
        if existing_pairs:
            return "Pairing already done 🔒"
        ids = [u[0] for u in users]
        random.shuffle(ids)
        for i in range(len(ids)):
            con.execute("INSERT INTO pairs VALUES (?,?,?)", (ids[i], ids[(i+1)%len(ids)], code))
        con.execute("UPDATE groups SET paired=1 WHERE code=?", (code,))
    return redirect(f'/admin/table/{code}')

@app.route('/admin/table/<code>')
def admin_table(code):
    with db() as con:
        table = con.execute("""
            SELECT u.codename AS giver, m.codename AS monito
            FROM pairs p
            JOIN users u ON u.id = p.giver
            JOIN users m ON m.id = p.receiver
            WHERE p.group_code=?
        """, (code,)).fetchall()

    return render_template_string('''
    <html><head><title>Admin Table</title>
    <style>
    body { font-family: Arial; background:#fff0f5; padding:40px; }
    h3 { color:#ff3399; }
    table { border-collapse: collapse; width: 60%; margin:auto; background:#fff; }
    th, td { border:1px solid #ff99cc; padding:10px; text-align:center; }
    th { background:#ff99cc; color:white; }
    a { display:inline-block; margin-top:20px; text-decoration:none; color:#ff3399; font-weight:bold; }
    </style>
    </head><body>
    <h3>Full Pairing Table (Codenames Only)</h3>
    <table>
        <tr><th>Giver</th><th>Monito</th></tr>
        {% for r in table %}
        <tr><td>{{r[0]}}</td><td>{{r[1]}}</td></tr>
        {% endfor %}
    </table>
    <a href="/admin/reset/{{code}}">Reset Game</a>
    </body></html>
    ''', table=table, code=code)

@app.route('/admin/reset/<code>')
def reset_game(code):
    with db() as con:
        con.execute("DELETE FROM pairs WHERE group_code=?", (code,))
        con.execute("DELETE FROM users WHERE group_code=?", (code,))
        con.execute("UPDATE groups SET paired=0 WHERE code=?", (code,))
    return f'''
    <html><head><title>Reset Game</title></head>
    <body style="font-family:Arial; background:#ffe6f0; text-align:center; padding:50px;">
    <h2>Game reset for group {code} ✅</h2>
    <a href='/'>Back to join page</a>
    </body></html>
    '''

# ---------------- USER ----------------
@app.route('/', methods=['GET','POST'])
def join():
    if request.method == 'POST':
        real = request.form['real']
        code_name = request.form['codename']
        group = request.form['group']
        with db() as con:
            g = con.execute("SELECT code FROM groups WHERE code=?", (group,)).fetchone()
            if not g:
                return "Invalid group code"
            con.execute("INSERT INTO users (real_name,codename,group_code) VALUES (?,?,?)",
                        (real, code_name, group))
            uid = con.execute("SELECT last_insert_rowid()").fetchone()[0]

        session['uid'] = uid
        return redirect('/dashboard')

    return render_template_string('''
    <html><head><title>Join Monita-Monito</title>
    <style>
    body { font-family: Arial; background:#ffe6f0; padding:50px; text-align:center; }
    input { padding:10px; width:200px; margin:5px; border-radius:5px; border:1px solid #ff99cc; }
    button { padding:10px 20px; background:#ff3399; color:white; border:none; border-radius:5px; cursor:pointer; }
    button:hover { background:#ff66aa; }
    a { color:#ff3399; text-decoration:none; font-weight:bold; display:block; margin-top:20px; }
    h2 { color:#ff3399; }
    </style>
    </head><body>
    <h2>Join Monita–Monito</h2>
    <form method="post">
        Real Name:<br><input name="real" required><br>
        Code Name (alias):<br><input name="codename" required><br>
        Group Code:<br><input name="group" required><br><br>
        <button>Join</button>
    </form>
    <a href="/admin/create">Create Group (Admin)</a>
    </body></html>
    ''')

@app.route('/dashboard')
def dashboard():
    uid = session.get('uid')
    if not uid:
        return redirect('/')

    with db() as con:
        pair = con.execute("SELECT receiver FROM pairs WHERE giver=?", (uid,)).fetchone()
        if not pair:
            return render_template_string('''
            <html><body style="font-family:Arial; background:#ffe6f0; text-align:center; padding:50px;">
            <h3>Waiting for admin to pair 🔒</h3>
            </body></html>
            ''')

        receiver = pair[0]
        monito = con.execute("SELECT codename FROM users WHERE id=?", (receiver,)).fetchone()[0]
        monita = con.execute("SELECT codename FROM users WHERE id=(SELECT giver FROM pairs WHERE receiver=?)", (uid,)).fetchone()[0]

    return render_template_string('''
    <html><head><title>Your Assignment</title>
    <style>
    body { font-family: Arial; background:#fff0f5; padding:50px; text-align:center; }
    h3 { color:#ff3399; }
    p { font-size:18px; }
    b { color:#ff3399; }
    </style>
    </head><body>
    <h3>Your Assignment</h3>
    <p>🌸 Your Monita (giver): <b>{{monita}}</b></p>
    <p>🎁 Your Monito (receiver): <b>{{monito}}</b></p>
    </body></html>
    ''', monita=monita, monito=monito)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
