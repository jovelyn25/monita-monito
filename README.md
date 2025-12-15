# 🎄 Monita–Monito (Secret Santa App)

A simple web app for **Monita–Monito / Secret Santa** where:
- Members join using a **group code**
- Everyone uses a **codename**
- Only the **admin** can pair participants
- Pairings are shown **only in codenames**
- Real names are never revealed

Built with **Flask + SQLite** and deployed on **PythonAnywhere**.

---

## ✨ Features

- 🎁 Manual admin pairing (prevents late join issues)
- 🔐 Anonymous pairing using codenames
- 🎅 Admin-only pairing table
- 🎄 Christmas-themed UI
- 💻 Works on mobile and desktop

---

## 🚀 How to Use

### 1️⃣ Admin creates a group
Visit: /admin/create


Copy the **group code** and share it with members.

---

### 2️⃣ Members join
Members enter:
- Real Name
- Code Name (alias)
- Group Code

Then wait for pairing 🎄

---

### 3️⃣ Admin pairs members
Admin visits: /admin/group/GROUPCODE


Click **“Pair Members”** to generate pairings.

---

### 4️⃣ Members view their assignment
After pairing, members can see:
- Their **Monita**
- Their **Monito**

---

## 🛠 Local Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask
python app.py


OPEN: http://127.0.0.1:5001
LIVE DEMO- HOSTED ON PYTHONANYWHERE : https://jovelyn25.pythonanywhere.com


