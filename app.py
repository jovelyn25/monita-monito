# Monita–Monito Flask App (Admin-controlled pairing)
# Members see only their own Monita/Monito
# Admin sees full table (codenames only) after pairing

from flask import Flask, render_template_string, request, redirect, session
import random, sqlite3

app = Flask(__name__)
app.secret_key = "secret-key"
DB = "monita.db"

# ---------------- DATABASE ----------------
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

# ---------------- ADMIN: CREATE GROUP ----------------
@app.route('/admin/create')
def admin_create():
    code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
    with db() as con:
        con.execute("INSERT INTO groups (code, paired) VALUES (?,0)", (code,))
    return f"""
    <h2 style="color:green;">Group Created ✅</h2>
    <p>Group Code: <b>{code}</b></p>
    <p>Go to <a href='/admin/group/{code}'>Admin Page</a> to pair members and view table.</p>
    """

# ---------------- ADMIN: MANUAL PAIRING & TABLE ----------------
@app.route('/admin/group/<code>', methods=['GET','POST'])
def admin_group(code):
    with db() as con:
        g = con.execute("SELECT code, paired FROM groups WHERE code=?", (code,)).fetchone()
        if not g:
            return "Invalid group code"

        if request.method == 'POST' and g[1] == 0:
            # Perform manual pairing
            users = con.execute("SELECT id FROM users WHERE group_code=?", (code,)).fetchall()
            if len(users) < 2:
                return "<p style='color:red;'>Need at least 2 members to pair.</p>"
            con.execute("DELETE FROM pairs WHERE group_code=?", (code,))
            ids = [u[0] for u in users]
            random.shuffle(ids)
            for i in range(len(ids)):
                con.execute("INSERT INTO pairs VALUES (?,?,?)", (ids[i], ids[(i+1)%len(ids)], code))
            con.execute("UPDATE groups SET paired=1 WHERE code=?", (code,))

        # Fetch table with codenames only
        table = con.execute("""
            SELECT u.codename AS giver, m.codename AS receiver
            FROM pairs p
            JOIN users u ON u.id=p.giver
            JOIN users m ON m.id=p.receiver
            WHERE p.group_code=?
        """, (code,)).fetchall()
        paired = g[1]

    return render_template_string('''
    <h2 style="color:blue;">Admin Page — Group {{code}}</h2>
    {% if not paired %}
    <p>Members have joined. Click the button to pair them manually.</p>
    <form method="post">
        <button style="padding:6px 12px;">Pair Members</button>
    </form>
    {% else %}
    <p style="color:green;">Pairing complete ✅</p>
    <h3>Group Table (Codenames Only)</h3>
    <table border="1" cellpadding="6" style="border-collapse: collapse;">
        <tr style="background:#f0f0f0;"><th>Giver (Monita)</th><th>Receiver (Monito)</th></tr>
        {% for r in table %}
        <tr><td>{{r[0]}}</td><td>{{r[1]}}</td></tr>
        {% endfor %}
    </table>
    {% endif %}
    ''', table=table, code=code, paired=paired)

# ---------------- USER: JOIN ----------------
@app.route('/', methods=['GET','POST'])
def join():
    if request.method == 'POST':
        real = request.form['real']
        code_name = request.form['codename']
        group = request.form['group']
        with db() as con:
            g = con.execute("SELECT code FROM groups WHERE code=?", (group,)).fetchone()
            if not g:
                return "<p style='color:red;'>Invalid group code</p>"
            con.execute("INSERT INTO users (real_name,codename,group_code) VALUES (?,?,?)",
                        (real, code_name, group))
            uid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        session['uid'] = uid
        return redirect('/dashboard')

    return render_template_string('''
    <h2 style="color:purple;">Join Monita–Monito</h2>
    <form method="post" style="max-width:400px;">
        Real Name:<br><input name="real" required style="width:100%;padding:6px;margin:4px 0;"><br>
        Code Name (alias):<br><input name="codename" required style="width:100%;padding:6px;margin:4px 0;"><br>
        Group Code:<br><input name="group" required style="width:100%;padding:6px;margin:4px 0;"><br>
        <button style="padding:6px 12px;">Join</button>
    </form>
    <hr>
    <a href="/admin/create">Create Group (Admin)</a>
    ''')

# ---------------- USER: DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    uid = session.get('uid')
    if not uid:
        return redirect('/')

    with db() as con:
        pair = con.execute("SELECT receiver FROM pairs WHERE giver=?", (uid,)).fetchone()
        if not pair:
            return "<p>Waiting for admin to pair members 🔒</p>"
        receiver = pair[0]
        monito = con.execute("SELECT codename FROM users WHERE id=?", (receiver,)).fetchone()[0]
        monita = con.execute("SELECT codename FROM users WHERE id=(SELECT giver FROM pairs WHERE receiver=?)", (uid,)).fetchone()[0]

    return render_template_string('''
    <h3 style="color:green;">Your Assignment</h3>
    <p>🌸 Your Monita (giver): <b>{{monita}}</b></p>
    <p>🎁 Your Monito (receiver): <b>{{monito}}</b></p>
    ''', monita=monita, monito=monito)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
