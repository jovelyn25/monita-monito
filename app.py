# Monita–Monito with User-Defined Codenames (Flask)
# Members see Monita/Monito by CODENAME only
# Real names are never revealed

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
    return f"Group created ✅<br>Group Code: <b>{code}</b><br><a href='/admin'>Go to Admin Page</a>"

@app.route('/admin')
def admin_page():
    return render_template_string('''
<h2>Admin Panel</h2>
<a href='/admin/create'>Create New Group</a><br><br>
<h3>Reset a Group</h3>
<form method='get' action='/admin/reset'>
<input name='code' placeholder='Group Code' required>
<button>Reset Group</button>
</form>
''')

@app.route('/admin/reset')
def admin_reset():
    code = request.args.get('code')
    if not code:
        return "No group code provided"

    with db() as con:
        g = con.execute("SELECT code FROM groups WHERE code=?", (code,)).fetchone()
        if not g:
            return "Invalid group code"
        con.execute("DELETE FROM users WHERE group_code=?", (code,))
        con.execute("DELETE FROM pairs WHERE group_code=?", (code,))
        con.execute("UPDATE groups SET paired=0 WHERE code=?", (code,))
    return f"Group {code} has been reset! ✅<br><a href='/admin'>Back to Admin Panel</a>"

@app.route('/admin/pair/<code>')
def admin_pair(code):
    with db() as con:
        paired_status = con.execute("SELECT paired FROM groups WHERE code=?", (code,)).fetchone()
        if not paired_status:
            return "Invalid group code"
        if paired_status[0]:
            return "This group is already paired! 🔒"

        users = con.execute("SELECT id FROM users WHERE group_code=?", (code,)).fetchall()
        if len(users) < 2:
            return "Need at least 2 members"

        existing_pairs = con.execute("SELECT * FROM pairs WHERE group_code=?", (code,)).fetchall()
        if existing_pairs:
            return "Pairs already exist. Cannot double pair."

        ids = [u[0] for u in users]
        random.shuffle(ids)
        for i in range(len(ids)):
            con.execute("INSERT INTO pairs VALUES (?,?,?)", (ids[i], ids[(i+1)%len(ids)], code))
        con.execute("UPDATE groups SET paired=1 WHERE code=?", (code,))
    return "Pairing complete 🔐"

# ---------------- USER ----------------
@app.route('/', methods=['GET','POST'])
def join():
    if request.method == 'POST':
        real = request.form['real']
        code_name = request.form['codename']
        group = request.form['group']

        with db() as con:
            g = con.execute("SELECT paired FROM groups WHERE code=?", (group,)).fetchone()
            if not g:
                return "Invalid group code"
            if g[0]:
                return "This group is already paired. You cannot join now."

            con.execute("INSERT INTO users (real_name,codename,group_code) VALUES (?,?,?)",
                        (real, code_name, group))
            uid = con.execute("SELECT last_insert_rowid()").fetchone()[0]

        session['uid'] = uid
        return redirect('/dashboard')

    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
<title>Monita–Monito</title>
<style>
body{font-family:Arial,Helvetica,sans-serif;background:#f6f7fb;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.card{background:white;padding:30px;border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,.1);width:100%;max-width:380px}
h2{text-align:center;margin-bottom:20px}
input{width:100%;padding:10px;margin-top:6px;margin-bottom:14px;border-radius:8px;border:1px solid #ccc}
button{width:100%;padding:12px;border:none;border-radius:8px;background:#6c63ff;color:white;font-size:16px;cursor:pointer}
button:hover{background:#574fe0}
.small{text-align:center;margin-top:15px}
a{text-decoration:none;color:#6c63ff}
</style>
</head>
<body>
<div class="card">
<h2>🎁 Monita–Monito</h2>
<form method="post">
<label>Real Name</label>
<input name="real" required>
<label>Code Name (Alias)</label>
<input name="codename" required>
<label>Group Code</label>
<input name="group" required>
<button>Join Game</button>
</form>
<div class="small">
<a href="/admin">Admin Panel</a>
</div>
</div>
</body>
</html>
''' )

@app.route('/dashboard')
def dashboard():
    uid = session.get('uid')
    if not uid:
        return redirect('/')

    with db() as con:
        pair = con.execute("SELECT receiver FROM pairs WHERE giver=?", (uid,)).fetchone()
        if not pair:
            return "Waiting for pairing 🔒"
        receiver = pair[0]
        monito = con.execute("SELECT codename FROM users WHERE id=?", (receiver,)).fetchone()[0]
        monita = con.execute("SELECT codename FROM users WHERE id=(SELECT giver FROM pairs WHERE receiver=?)", (uid,)).fetchone()[0]

        table = con.execute("""
            SELECT u.codename AS you, m.codename AS your_monito
            FROM pairs p
            JOIN users u ON u.id=p.giver
            JOIN users m ON m.id=p.receiver
            WHERE p.group_code=(SELECT group_code FROM users WHERE id=?)
        """, (uid,)).fetchall()

    return render_template_string('''
<h3>Your Assignment</h3>
<p>🌸 Your Monita (giver): <b>{{monita}}</b></p>
<p>🎁 Your Monito (receiver): <b>{{monito}}</b></p>
<hr>
<h3>Group Table (Codenames Only)</h3>
<table border="1" cellpadding="6">
<tr><th>Giver</th><th>Monito</th></tr>
{% for r in table %}
<tr><td>{{r[0]}}</td><td>{{r[1]}}</td></tr>
{% endfor %}
</table>
''', monita=monita, monito=monito, table=table)

# ---------------- RUN ----------------
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Render sets PORT automatically
    app.run(debug=True, host='0.0.0.0', port=port)
