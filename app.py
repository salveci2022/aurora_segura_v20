from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)
app.secret_key = "aurora_v20_secret"

# --- HTML (tudo embutido para NÃO quebrar no Render) ---
BASE_CSS = """
<style>
  body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#0b1020;color:#fff}
  .wrap{max-width:980px;margin:0 auto;padding:24px}
  .card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:18px;margin:14px 0;backdrop-filter: blur(6px)}
  .title{font-size:28px;font-weight:800;margin:0 0 6px}
  .sub{opacity:.85;margin:0 0 14px}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
  a.btn, button.btn{display:flex;align-items:center;justify-content:center;text-decoration:none;
    background:#ff2d6f;border:none;color:#fff;padding:14px 16px;border-radius:14px;
    font-weight:800;cursor:pointer}
  a.btn.secondary, button.btn.secondary{background:#00c2ff;color:#001018}
  a.btn.dark{background:#121a33}
  input, select{width:100%;padding:12px;border-radius:12px;border:1px solid rgba(255,255,255,.18);
    background:#0f1733;color:#fff;outline:none}
  label{display:block;margin:10px 0 6px;font-weight:700}
  .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  .tag{display:inline-block;padding:6px 10px;border-radius:999px;background:#121a33;border:1px solid rgba(255,255,255,.12);opacity:.9}
  .ok{color:#7CFFB2}
  .warn{color:#FFD37C}
  .muted{opacity:.8}
</style>
"""

HOME_HTML = BASE_CSS + """
<div class="wrap">
  <div class="card">
    <div class="title">Aurora Segura V20</div>
    <p class="sub">Selecione o painel que deseja acessar.</p>
    <div class="grid">
      <a class="btn" href="/panic">🚨 Painel Mulher (Pânico)</a>
      <a class="btn secondary" href="/trusted">🛡️ Pessoa de Confiança</a>
      <a class="btn dark" href="/admin">👨‍💼 Painel Admin</a>
    </div>
    <p class="muted" style="margin-top:14px">
      Links oficiais: <span class="tag">/</span> <span class="tag">/panic</span> <span class="tag">/trusted</span> <span class="tag">/admin</span>
    </p>
  </div>
</div>
"""

PANIC_HTML = BASE_CSS + """
<div class="wrap">
  <div class="card">
    <div class="title">🚨 Painel de Pânico</div>
    <p class="sub">Preencha o básico e acione o alerta.</p>

    <form method="post" action="/panic">
      <div class="row">
        <div>
          <label>Nome da vítima</label>
          <input name="victim_name" placeholder="Ex: Maria" required>
        </div>
        <div>
          <label>Tipo de ocorrência</label>
          <select name="occurrence" required>
            <option value="Perseguição">Perseguição</option>
            <option value="Ameaça">Ameaça</option>
            <option value="Agressão">Agressão</option>
            <option value="Suspeita">Suspeita</option>
            <option value="Outro">Outro</option>
          </select>
        </div>
      </div>

      <label>Mensagem (opcional)</label>
      <input name="message" placeholder="Ex: estou em risco, preciso de ajuda agora">

      <div class="grid" style="margin-top:12px">
        <button class="btn" type="submit">🔊 ACIONAR ALERTA</button>
        <a class="btn dark" href="/">⬅️ Voltar</a>
      </div>
    </form>

    {% if sent %}
      <p class="ok" style="margin-top:14px;font-weight:800">✅ Alerta registrado com sucesso.</p>
      <p class="muted">Agora a Pessoa de Confiança pode abrir o painel <span class="tag">/trusted</span> para visualizar o alerta.</p>
    {% endif %}
  </div>
</div>
"""

TRUSTED_HTML = BASE_CSS + """
<div class="wrap">
  <div class="card">
    <div class="title">🛡️ Painel Pessoa de Confiança</div>
    <p class="sub">Visualização do último alerta recebido.</p>

    {% if last_alert %}
      <div class="card">
        <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
          <span class="tag">Vítima: <b>{{ last_alert["victim_name"] }}</b></span>
          <span class="tag">Ocorrência: <b>{{ last_alert["occurrence"] }}</b></span>
          <span class="tag">Status: <b class="warn">ATIVO</b></span>
        </div>
        <p style="margin-top:10px" class="muted">
          Mensagem: <b>{{ last_alert["message"] or "—" }}</b>
        </p>
      </div>

      <div class="grid">
        <a class="btn secondary" href="/trusted?refresh=1">🔄 Atualizar</a>
        <a class="btn dark" href="/trusted/clear">🧹 Limpar alerta</a>
        <a class="btn dark" href="/">⬅️ Voltar</a>
      </div>
    {% else %}
      <p class="muted">Nenhum alerta ativo no momento.</p>
      <div class="grid">
        <a class="btn secondary" href="/trusted?refresh=1">🔄 Atualizar</a>
        <a class="btn dark" href="/">⬅️ Voltar</a>
      </div>
    {% endif %}
  </div>
</div>
"""

ADMIN_HTML = BASE_CSS + """
<div class="wrap">
  <div class="card">
    <div class="title">👨‍💼 Painel Admin</div>
    <p class="sub">Estado do sistema (último alerta).</p>

    {% if last_alert %}
      <p class="ok"><b>✅ Existe alerta registrado.</b></p>
      <div class="card">
        <p><b>Vítima:</b> {{ last_alert["victim_name"] }}</p>
        <p><b>Ocorrência:</b> {{ last_alert["occurrence"] }}</p>
        <p><b>Mensagem:</b> {{ last_alert["message"] or "—" }}</p>
      </div>
      <div class="grid">
        <a class="btn dark" href="/trusted/clear">🧹 Limpar alerta</a>
        <a class="btn secondary" href="/admin">🔄 Atualizar</a>
        <a class="btn dark" href="/">⬅️ Voltar</a>
      </div>
    {% else %}
      <p class="muted">Nenhum alerta no momento.</p>
      <div class="grid">
        <a class="btn secondary" href="/admin">🔄 Atualizar</a>
        <a class="btn dark" href="/">⬅️ Voltar</a>
      </div>
    {% endif %}
  </div>
</div>
"""

# --- “banco” simples em memória (serve para validar rotas e painéis) ---
LAST_ALERT = None

@app.get("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/panic", methods=["GET", "POST"])
def panic():
    global LAST_ALERT
    sent = False
    if request.method == "POST":
        victim_name = request.form.get("victim_name", "").strip()
        occurrence = request.form.get("occurrence", "").strip()
        message = request.form.get("message", "").strip()
        LAST_ALERT = {"victim_name": victim_name, "occurrence": occurrence, "message": message}
        sent = True
    return render_template_string(PANIC_HTML, sent=sent)

@app.get("/trusted")
def trusted():
    return render_template_string(TRUSTED_HTML, last_alert=LAST_ALERT)

@app.get("/trusted/clear")
def trusted_clear():
    global LAST_ALERT
    LAST_ALERT = None
    return redirect(url_for("trusted"))

@app.get("/admin")
def admin():
    return render_template_string(ADMIN_HTML, last_alert=LAST_ALERT)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
