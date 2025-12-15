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

# ---------------- SHARED CHRISTMAS STYLE ----------------
STYLE = """
<style>
body {
    background: linear-gradient(to bottom, #b30000, #006400);
    font-family: 'Segoe UI', sans-serif;
    color: #fff;
    text-align: center;
    padding: 40px;
}
.card {
    background: #ffffff;
    color: #333;
    max-width: 420px;
    margin: auto;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
}
h2, h3 {
    color: #b30000;
}
input {
    width: 100%;
    padding: 10px;
    margin: 6px 0;
    border-radius: 8px;
    border: 1px solid #ccc;
}
button {
    background: #b30000;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 10px;
    cursor: pointer;
    font-size: 16px;
}
button:hover {
    background: #8b0000;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}
th {
    background: #006400;
    color: white;
    padding: 8px;
}
td {
    background: #f8f8f8;
    padding: 8px;
}
.footer {
    margin-top: 20px;
    font-size: 14px;
    color: #eee;
}
</style>
"""

# ---------------- ADMIN: CREATE GROUP ----------------
@app.route('/admin/create')
def admin_create():
    code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
    with db() as con:
        con.execute("INSERT INTO groups VALUES (?,0)", (code,))
    return render_template_string(STYLE + f"""
    <div class="card">
        <h2>🎄 Group Created!</h2>
        <p><b>Group Code:</b> {code}</p>
        <p>Give this code to members</p>
        <a href="/admin/group/{code}">
            <button>Go to Admin Page</button>
        </a>
    </div>
    """)

# ---------------- ADMIN: MANUAL PAIRING ----------------
@app.route('/admin/group/<code>', methods=['GET','POST'])
def admin_group(code):
    with db() as con:
        g = con.execute("SELECT paired FROM groups WHERE code=?", (code,)).fetchone()
        if not g:
            return "Invalid group"

        if request.method == 'POST' and g[0] == 0:
            users = con.execute("SELECT id FROM users WHERE group_code=?", (code,)).fetchall()
            if len(users) < 2:
                return "Need at least 2 members"
            con.execute("DELETE FROM pairs WHERE group_code=?", (code,))
            ids = [u[0] for u in users]
            random.shuffle(ids)
            for i in range(len(ids)):
                con.execute("INSERT INTO pairs VALUES (?,?,?)",
                            (ids[i], ids[(i+1)%len(ids)], code))
            con.execute("UPDATE groups SET paired=1 WHERE code=?", (code,))

        table = con.execute("""
            SELECT u.codename, m.codename
            FROM pairs p
            JOIN users u ON u.id=p.giver
            JOIN users m ON m.id=p.receiver
            WHERE p.group_code=?
        """, (code,)).fetchall()

    return render_template_string(STYLE + """
    <div class="card">
        <h2>🎅 Admin Panel</h2>
        {% if not table %}
        <p>Members are joining...</p>
        <form method="post">
            <button>🎁 Pair Members</button>
        </form>
        {% else %}
        <h3>🎄 Pairing Table</h3>
        <table>
            <tr><th>Monita</th><th>Monito</th></tr>
            {% for r in table %}
            <tr><td>{{r[0]}}</td><td>{{r[1]}}</td></tr>
            {% endfor %}
        </table>
        {% endif %}
    </div>
    """, table=table)

# ---------------- USER: JOIN ----------------
@app.route('/', methods=['GET','POST'])
def join():
    if request.method == 'POST':
        real = request.form['real']
        codename = request.form['codename']
        group = request.form['group']
        with db() as con:
            if not con.execute("SELECT 1 FROM groups WHERE code=?", (group,)).fetchone():
                return "Invalid group code"
            con.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                        (real, codename, group))
            uid = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        session['uid'] = uid
        return redirect('/dashboard')

    return render_template_string(STYLE + """
    <div class="card">
        <h2>🎄 Join Monita–Monito</h2>

        <form method="post">
            <input name="real" placeholder="Real Name" required>
            <input name="codename" placeholder="Code Name" required>
            <input name="group" placeholder="Group Code" required>
            <button>🎁 Join</button>
        </form>

        <hr style="margin:20px 0;">

        <a href="/admin/create">
            <button style="background:#006400;">🎅 Admin Panel</button>
        </a>

        <div class="footer">Merry Christmas 🎄</div>
    </div>
    """)

# ---------------- USER: DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    uid = session.get('uid')
    if not uid:
        return redirect('/')

    with db() as con:
        pair = con.execute("SELECT receiver FROM pairs WHERE giver=?", (uid,)).fetchone()
        if not pair:
            return render_template_string(STYLE + """
            <div class="card">
                <h3>⏳ Waiting for pairing...</h3>
                <p>Please check back later 🎄</p>
            </div>
            """)
        monito = con.execute("SELECT codename FROM users WHERE id=?", (pair[0],)).fetchone()[0]
        monita = con.execute(
            "SELECT codename FROM users WHERE id=(SELECT giver FROM pairs WHERE receiver=?)",
            (uid,)).fetchone()[0]

    return render_template_string(STYLE + """
    <div class="card">
        <h2>🎁 Your Assignment</h2>
        <p>🌸 Your Monita: <b>{{monita}}</b></p>
        <p>🎁 Your Monito: <b>{{monito}}</b></p>
        <div class="footer">Secret until Christmas 🎄</div>
    </div>
    """, monita=monita, monito=monito)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)
