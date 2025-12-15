from __future__ import annotations
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from pathlib import Path
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# Windows pode não ter base de fusos (tzdata). Tentamos carregar e, se faltar,
# usamos horário local do sistema.
try:
    TZ = ZoneInfo("America/Sao_Paulo")
except Exception:
    TZ = None
BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
ALERTS_FILE = BASE_DIR / "alerts.log"
STATE_FILE = BASE_DIR / "state.json"

app = Flask(__name__)
app.secret_key = "aurora_v21_ultra_estavel"

def now_br_str() -> str:
    if TZ is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

def ensure_files():
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({
            "admin": {"password": "admin123", "role": "admin", "name": "Admin Aurora"}
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("", encoding="utf-8")
    if not STATE_FILE.exists():
        STATE_FILE.write_text(json.dumps({"last_id": 0}, indent=2, ensure_ascii=False), encoding="utf-8")

def load_users() -> dict:
    ensure_files()
    try:
        data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    if "admin" not in data:
        data["admin"] = {"password": "admin123", "role": "admin", "name": "Admin Aurora"}
    return data

def save_users(data: dict) -> None:
    USERS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def list_trusted_names() -> list[str]:
    users = load_users()
    arr = [info.get("name") or u for u, info in users.items() if info.get("role") == "trusted"]
    arr.sort(key=lambda s: s.lower())
    return arr

def next_alert_id() -> int:
    ensure_files()
    try:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        st = {"last_id": 0}
    st["last_id"] = int(st.get("last_id", 0)) + 1
    STATE_FILE.write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")
    return st["last_id"]

def log_alert(payload: dict) -> None:
    ensure_files()
    with ALERTS_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

def read_last_alert():
    ensure_files()
    txt = ALERTS_FILE.read_text(encoding="utf-8").strip()
    if not txt:
        return None
    lines = [ln for ln in txt.split("\n") if ln.strip()]
    try:
        return json.loads(lines[-1])
    except Exception:
        return None

@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "server_time_br": now_br_str(),
        "tz": "America/Sao_Paulo" if TZ is not None else "LOCAL_SYSTEM_TIME",
        "css_ok": (BASE_DIR / "static" / "css" / "style.css").exists(),
        "js_ok": (BASE_DIR / "static" / "js" / "panic.js").exists(),
        "mp3_ok": (BASE_DIR / "static" / "audio" / "sirene.mp3").exists(),
        "template_panic_ok": (BASE_DIR / "templates" / "panic_button.html").exists(),
        "template_trusted_ok": (BASE_DIR / "templates" / "panel_trusted.html").exists(),
        "users_json_ok": USERS_FILE.exists(),
        "alerts_log_ok": ALERTS_FILE.exists(),
    })

@app.get("/")
def index():
    return redirect(url_for("panic_button"))

@app.get("/panic")
def panic_button():
    trusted = list_trusted_names()
    return render_template("panic_button.html", trusted=trusted)

@app.post("/api/send_alert")
def send_alert():
    data = request.get_json(silent=True) or {}
    payload = {
        "id": next_alert_id(),
        "ts": now_br_str(),
        "name": (data.get("name") or "Não informado"),
        "situation": (data.get("situation") or "Não especificado"),
        "message": (data.get("message") or ""),
        "location": data.get("location"),
    }
    log_alert(payload)
    return jsonify({"ok": True, "id": payload["id"]})

@app.get("/api/last_alert")
def last_alert():
    return jsonify({"ok": True, "last": read_last_alert()})

# ===== ADMIN =====
@app.route("/panel/login", methods=["GET", "POST"])
def admin_login():
    users = load_users()
    error = False
    if request.method == "POST":
        u = (request.form.get("user") or "").strip()
        p = (request.form.get("password") or "")
        info = users.get(u)
        if info and info.get("role") == "admin" and info.get("password") == p:
            session.clear()
            session["role"] = "admin"
            session["user"] = u
            return redirect(url_for("admin_panel"))
        error = True
    return render_template("login_admin.html", error=error)

@app.get("/panel")
def admin_panel():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))
    users = load_users()
    trusted = {u: info for u, info in users.items() if info.get("role") == "trusted"}
    msg = request.args.get("msg", "")
    err = request.args.get("err", "")
    return render_template("panel_admin.html", trusted=trusted, msg=msg, err=err)

@app.post("/panel/add_trusted")
def admin_add_trusted():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))
    name = (request.form.get("trusted_name") or "").strip()
    username = (request.form.get("trusted_user") or "").strip().lower()
    password = (request.form.get("trusted_password") or "").strip()

    if not name or not username or not password:
        return redirect("/panel?err=Preencha+nome,+usuario+e+senha")

    users = load_users()
    if username in users:
        return redirect("/panel?err=Este+usuario+ja+existe")

    trusted_users = [u for u, info in users.items() if info.get("role") == "trusted"]
    if len(trusted_users) >= 3:
        return redirect("/panel?err=Limite+de+3+pessoas+de+confianca+atingido")

    users[username] = {"password": password, "role": "trusted", "name": name}
    save_users(users)
    return redirect("/panel?msg=Pessoa+de+confianca+cadastrada")

@app.post("/panel/delete_trusted")
def admin_delete_trusted():
    if session.get("role") != "admin":
        return redirect(url_for("admin_login"))
    username = (request.form.get("username") or "").strip()
    users = load_users()
    if username in users and users[username].get("role") == "trusted":
        users.pop(username)
        save_users(users)
        return redirect("/panel?msg=Pessoa+removida")
    return redirect("/panel?err=Nao+foi+possivel+remover")

@app.get("/logout_admin")
def logout_admin():
    session.clear()
    return redirect(url_for("admin_login"))

# ===== TRUSTED =====
@app.route("/trusted/login", methods=["GET", "POST"])
def trusted_login():
    users = load_users()
    error = False
    if request.method == "POST":
        u = (request.form.get("user") or "").strip().lower()
        p = (request.form.get("password") or "")
        info = users.get(u)
        if info and info.get("role") == "trusted" and info.get("password") == p:
            session.clear()
            session["role"] = "trusted"
            session["trusted"] = u
            return redirect(url_for("trusted_panel"))
        error = True
    return render_template("login_trusted.html", error=error)

@app.get("/trusted/panel")
def trusted_panel():
    if session.get("role") != "trusted":
        return redirect(url_for("trusted_login"))
    users = load_users()
    u = session.get("trusted")
    display_name = users.get(u, {}).get("name") or u
    return render_template("panel_trusted.html", display_name=display_name)

@app.get("/logout_trusted")
def logout_trusted():
    session.clear()
    return redirect(url_for("trusted_login"))

@app.route("/trusted/change_password", methods=["GET", "POST"])
def trusted_change_password():
    if session.get("role") != "trusted":
        return redirect(url_for("trusted_login"))
    msg, err = "", ""
    if request.method == "POST":
        old = request.form.get("old_password") or ""
        new = (request.form.get("new_password") or "").strip()
        users = load_users()
        u = session.get("trusted")
        info = users.get(u)
        if not info or info.get("password") != old:
            err = "Senha atual incorreta."
        elif len(new) < 4:
            err = "Nova senha muito curta (mínimo 4)."
        else:
            users[u]["password"] = new
            save_users(users)
            msg = "Senha alterada com sucesso."
    return render_template("trusted_change_password.html", msg=msg, err=err)

@app.route("/trusted/recover", methods=["GET", "POST"])
def trusted_recover():
    msg, err = "", ""
    if request.method == "POST":
        u = (request.form.get("user") or "").strip().lower()
        new = (request.form.get("new_password") or "").strip()
        users = load_users()
        info = users.get(u)
        if not info or info.get("role") != "trusted":
            err = "Usuário não encontrado."
        elif len(new) < 4:
            err = "Senha muito curta (mínimo 4)."
        else:
            users[u]["password"] = new
            save_users(users)
            msg = "Senha redefinida. Faça login."
    return render_template("trusted_recover.html", msg=msg, err=err)

if __name__ == "__main__":
    ensure_files()
    app.run(host="0.0.0.0", port=5000, debug=True)
    