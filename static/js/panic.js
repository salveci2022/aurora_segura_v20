(() => {
  const $ = (id) => document.getElementById(id);

  const sos = $("sosBtn");
  const statusEl = $("status");
  const nameEl = $("name");
  const msgEl = $("message");
  const chips = Array.from(document.querySelectorAll("[data-situation]"));

  let holdTimer = null;
  let selectedSituation = "Violência física";

  function setSituation(v){
    selectedSituation = v;
    chips.forEach(c => c.classList.toggle("active", c.dataset.situation === v));
  }
  chips.forEach(c => c.addEventListener("click", () => setSituation(c.dataset.situation)));
  setSituation(selectedSituation);

  function startHold(e){
    e.preventDefault();
    statusEl.textContent = "Mantenha pressionado...";
    sos.classList.add("holding");
    holdTimer = setTimeout(() => sendAlert(), 1200);
  }
  function endHold(){
    if (holdTimer) clearTimeout(holdTimer);
    holdTimer = null;
    sos.classList.remove("holding");
  }

  async function getLocationBestEffort(){
    if (!navigator.geolocation) return null;

    return await new Promise((resolve) => {
      let done = false;
      const finish = (v) => { if (!done){ done = true; resolve(v);} };

      // hard timeout (nunca trava)
      const t = setTimeout(() => finish(null), 1800);

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          clearTimeout(t);
          finish({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            accuracy_m: pos.coords.accuracy
          });
        },
        () => { clearTimeout(t); finish(null); },
        { enableHighAccuracy: true, timeout: 1500, maximumAge: 10000 }
      );
    });
  }

  async function sendAlert(){
    try{
      statusEl.textContent = "Enviando alerta...";
      const location = await getLocationBestEffort();

      const res = await fetch("/api/send_alert", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
          name: (nameEl.value || "").trim(),
          situation: selectedSituation,
          message: (msgEl.value || "").trim(),
          location
        })
      });

      const data = await res.json().catch(()=>({ok:true}));
      statusEl.textContent = (data && data.ok) ? "SOS enviado!" : "Falha ao enviar.";
      setTimeout(() => statusEl.textContent = "", 2200);
    }catch(e){
      statusEl.textContent = "Falha de conexão.";
      setTimeout(() => statusEl.textContent = "", 2200);
    }
  }

  sos.addEventListener("mousedown", startHold);
  sos.addEventListener("mouseup", endHold);
  sos.addEventListener("mouseleave", endHold);
  sos.addEventListener("touchstart", startHold, {passive:false});
  sos.addEventListener("touchend", endHold);
  sos.addEventListener("touchcancel", endHold);

  $("btnClear").addEventListener("click", () => {
    nameEl.value = "";
    msgEl.value = "";
    setSituation("Violência física");
    statusEl.textContent = "";
  });

  $("btnReset").addEventListener("click", () => window.location.reload());
  $("btnExit").addEventListener("click", () => window.location.href = "/");
})();
