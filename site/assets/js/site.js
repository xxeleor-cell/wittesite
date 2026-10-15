/* VITTE-Рус — интерактивность сайта: меню, галерея, фильтры, поиск, форма запроса. */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- мега-меню (клавиатура и сенсорные экраны) ---------- */
  var navCat = $(".nav-cat");
  if (navCat) {
    var link = $(".nav-cat-link", navCat);
    link.addEventListener("click", function (e) {
      if (window.matchMedia("(hover: none)").matches && !navCat.classList.contains("open")) {
        e.preventDefault();
        navCat.classList.add("open");
        link.setAttribute("aria-expanded", "true");
      }
    });
    navCat.addEventListener("mouseenter", function () { link.setAttribute("aria-expanded", "true"); });
    navCat.addEventListener("mouseleave", function () { navCat.classList.remove("open"); link.setAttribute("aria-expanded", "false"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { navCat.classList.remove("open"); link.setAttribute("aria-expanded", "false"); }
    });
    document.addEventListener("click", function (e) { if (!navCat.contains(e.target)) navCat.classList.remove("open"); });
  }

  /* ---------- мобильное меню ---------- */
  var mnav = $("#mnav"), burger = $("[data-open-mnav]");
  function closeM() { mnav.hidden = true; document.body.classList.remove("mnav-open"); if (burger) { burger.setAttribute("aria-expanded", "false"); burger.focus(); } }
  if (mnav && burger) {
    burger.addEventListener("click", function () {
      mnav.hidden = false; document.body.classList.add("mnav-open"); burger.setAttribute("aria-expanded", "true");
      var cur = location.pathname;
      $$("details", mnav).forEach(function (d) {
        if ($$("a", d).some(function (a) { return cur.indexOf(a.getAttribute("href")) === 0 && a.getAttribute("href") !== "/"; })) d.open = true;
      });
      var first = $("input", mnav); if (first) first.focus({ preventScroll: true });
    });
    $("[data-close-mnav]", mnav).addEventListener("click", closeM);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !mnav.hidden) closeM(); });
    window.addEventListener("resize", function () { if (window.innerWidth > 1060 && !mnav.hidden) closeM(); });
  }

  /* ---------- лайтбокс и галерея ---------- */
  var lb = $("#lightbox"), lbImg = lb && $("img", lb), lbCap = lb && $(".lb-cap", lb), lbList = [], lbIdx = 0;
  function lbShow(i) {
    lbIdx = (i + lbList.length) % lbList.length;
    lbImg.src = lbList[lbIdx].src; lbCap.textContent = lbList[lbIdx].cap || (lbList.length > 1 ? (lbIdx + 1) + " / " + lbList.length : "");
    $(".lb-prev", lb).hidden = $(".lb-next", lb).hidden = lbList.length < 2;
  }
  function lbOpen(list, i) { lbList = list; lb.hidden = false; document.body.classList.add("mnav-open"); lbShow(i); $(".lb-close", lb).focus(); }
  function lbClose() { lb.hidden = true; document.body.classList.remove("mnav-open"); lbImg.removeAttribute("src"); }
  if (lb) {
    $("[data-lb-close]", lb).addEventListener("click", lbClose);
    $("[data-lb-prev]", lb).addEventListener("click", function () { lbShow(lbIdx - 1); });
    $("[data-lb-next]", lb).addEventListener("click", function () { lbShow(lbIdx + 1); });
    lb.addEventListener("click", function (e) { if (e.target === lb) lbClose(); });
    document.addEventListener("keydown", function (e) {
      if (lb.hidden) return;
      if (e.key === "Escape") lbClose();
      if (e.key === "ArrowLeft") lbShow(lbIdx - 1);
      if (e.key === "ArrowRight") lbShow(lbIdx + 1);
    });
    var tx = null;
    lb.addEventListener("touchstart", function (e) { tx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener("touchend", function (e) {
      if (tx === null) return; var dx = e.changedTouches[0].clientX - tx; tx = null;
      if (Math.abs(dx) > 50) lbShow(lbIdx + (dx < 0 ? 1 : -1));
    });
    $$("[data-lb-single]").forEach(function (b) {
      b.addEventListener("click", function () {
        var group = $$("[data-lb-single]", b.parentNode);
        lbOpen(group.map(function (x) { return { src: x.getAttribute("data-lb-single"), cap: x.getAttribute("data-cap") }; }), group.indexOf(b));
      });
    });
  }
  $$("[data-gallery]").forEach(function (g) {
    var imgs = JSON.parse(g.getAttribute("data-images") || "[]"), cur = 0, main = $(".gal-main img", g);
    $$(".gal-thumb", g).forEach(function (t) {
      t.addEventListener("click", function () {
        cur = +t.getAttribute("data-idx");
        main.src = t.getAttribute("data-src"); main.removeAttribute("width"); main.removeAttribute("height");
        $$(".gal-thumb", g).forEach(function (x) { x.classList.toggle("is-active", x === t); });
      });
    });
    var open = $("[data-lb-open]", g);
    if (open && lb) open.addEventListener("click", function () { lbOpen(imgs.map(function (s) { return { src: s }; }), cur); });
  });

  /* ---------- фильтры в списках ---------- */
  $$(".listing").forEach(function (box) {
    var f = $("[data-filters]", box); if (!f) return;
    var cards = $$(".pcard", box), count = $("[data-count]", f), empty = $("[data-empty]", box);
    var text = $("[data-text-filter]", f), air = $("[data-air-filter]", f), sels = $$("[data-facet]", f);
    var facetsOf = cards.map(function (c) { try { return JSON.parse(c.getAttribute("data-facets") || "{}"); } catch (e) { return {}; } });
    function apply() {
      var q = text ? text.value.trim().toLowerCase() : "", a = air && air.value ? +air.value : null, n = 0;
      cards.forEach(function (c, i) {
        var ok = true;
        if (q) ok = q.split(/\s+/).every(function (w) { return c.getAttribute("data-text").indexOf(w) >= 0; });
        sels.forEach(function (s) { if (ok && s.value && facetsOf[i][s.getAttribute("data-facet")] !== s.value) ok = false; });
        if (ok && a !== null) {
          var r = c.getAttribute("data-air");
          if (!r) ok = false; else { var p = r.split("-"); ok = a >= +p[0] && a <= +p[1]; }
        }
        c.hidden = !ok; if (ok) n++;
      });
      count.textContent = "Показано: " + n + " из " + cards.length;
      if (empty) empty.hidden = n > 0;
    }
    f.addEventListener("input", apply); f.addEventListener("change", apply);
    $("[data-reset]", f).addEventListener("click", function () { $$("input, select", f).forEach(function (el) { el.value = ""; }); apply(); });
    apply();
  });

  /* ---------- поиск ---------- */
  var index = null;
  function loadIndex() {
    if (index) return Promise.resolve(index);
    return fetch("/assets/search-index.json").then(function (r) { return r.json(); }).then(function (d) { index = d; return d; });
  }
  function norm(s) { return (s || "").toLowerCase().replace(/ё/g, "е").replace(/[×x*]/g, "x").replace(/[\s\-–_/.,]+/g, " "); }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function search(q) {
    var words = norm(q).split(" ").filter(Boolean);
    if (!words.length) return [];
    var compact = norm(q).replace(/ /g, "");
    return index.map(function (it) {
      var hay = norm(it.n + " " + it.m + " " + it.s + " " + it.p + " " + it.t), hayC = hay.replace(/ /g, ""), score = 0;
      for (var i = 0; i < words.length; i++) {
        var w = words[i];
        if (hay.indexOf(w) < 0 && hayC.indexOf(w) < 0) return null;
        if (norm(it.m).indexOf(w) >= 0) score += 5;
        if (norm(it.n).indexOf(w) >= 0) score += 3;
        score += 1;
      }
      if (compact.length > 2 && norm(it.m).replace(/ /g, "").indexOf(compact) >= 0) score += 10;
      return { it: it, score: score };
    }).filter(Boolean).sort(function (a, b) { return b.score - a.score; }).map(function (x) { return x.it; });
  }
  var sInput = $("[data-search-input]");
  if (sInput) {
    var res = $("[data-search-results]"), st = $("[data-search-status]");
    var params = new URLSearchParams(location.search); sInput.value = params.get("q") || "";
    function run() {
      var q = sInput.value.trim();
      if (!q) { res.innerHTML = ""; st.textContent = "Введите название, модель или артикул."; return; }
      loadIndex().then(function () {
        var r = search(q);
        st.textContent = r.length ? "Найдено: " + r.length : "Ничего не найдено по запросу «" + q + "». Попробуйте другое написание модели или выберите раздел в каталоге.";
        res.innerHTML = r.slice(0, 60).map(function (it) {
          return '<article class="pcard"><a class="pcard-img" href="' + it.u + '" tabindex="-1" aria-hidden="true">' +
            (it.i ? '<img src="' + it.i + '" alt="" loading="lazy">' : '<span class="noimg">Фото готовится</span>') +
            '</a><div class="pcard-body"><div class="pcard-model">' + esc(it.m) + '</div><h3 class="pcard-title"><a href="' + it.u + '">' + esc(it.n) +
            '</a></h3><p class="pcard-sum">' + esc(it.s) + '</p><p class="pcard-sum">' + esc(it.p) + '</p></div><div class="pcard-foot"><a class="link-more" href="' + it.u + '">Подробнее →</a></div></article>';
        }).join("");
      }).catch(function () { st.textContent = "Не удалось загрузить поисковый индекс."; });
    }
    var t; sInput.addEventListener("input", function () { clearTimeout(t); t = setTimeout(function () {
      var u = new URL(location.href); u.searchParams.set("q", sInput.value); history.replaceState(null, "", u); run(); }, 200); });
    sInput.form.addEventListener("submit", function (e) { e.preventDefault(); run(); });
    run();
  }

  /* ---------- форма запроса КП ---------- */
  var pid = new URLSearchParams(location.search).get("product");
  if (pid && /^[a-z0-9-]+$/.test(pid)) {
    loadIndex().then(function (idx) {
      var it = idx.filter(function (x) { return x.id === pid; })[0]; if (!it) return;
      $$("[data-products-field]").forEach(function (f) { if (!f.value) f.value = it.n + (it.m && it.n.indexOf(it.m) < 0 ? " (" + it.m + ")" : ""); });
      var box = $("[data-request-product]");
      if (box) box.innerHTML = '<a class="product-chip" href="' + it.u + '">' + (it.i ? '<img src="' + it.i + '" alt="">' : "") + "<span><small>Запрос по изделию</small><br><b>" + esc(it.n) + "</b></span></a>";
    }).catch(function () {});
  }
  $$("[data-request-form]").forEach(function (form) {
    var msg = $("[data-msg]", form), btn = $("button[type=submit]", form);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      msg.className = "rform-msg"; msg.textContent = "";
      var bad = $$("[required]", form).filter(function (el) {
        var ok = el.type === "checkbox" ? el.checked : el.value.trim() !== "";
        if (el.name === "phone" && ok) ok = el.value.replace(/\D/g, "").length >= 10;
        el.classList.toggle("is-invalid", !ok); return !ok;
      });
      var email = form.elements.email;
      if (email.value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value)) { email.classList.add("is-invalid"); bad.push(email); }
      if (bad.length) { msg.className = "rform-msg err"; msg.textContent = "Проверьте выделенные поля: имя, телефон (не менее 10 цифр) и согласие обязательны."; bad[0].focus(); return; }
      var data = {}; new FormData(form).forEach(function (v, k) { data[k] = v; });
      data.page = location.pathname + location.search;
      btn.disabled = true; btn.textContent = "Отправка…";
      fetch("/api/request", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (r) {
          if (!r.ok) throw new Error(r.j && r.j.error || "Ошибка");
          form.reset(); msg.className = "rform-msg ok"; msg.textContent = "Спасибо! Запрос № " + r.j.id + " принят.";
        })
        .catch(function (err) {
          msg.className = "rform-msg err";
          msg.textContent = "Не удалось отправить запрос: сервер приёма заявок недоступен. " + (err && err.message && err.message !== "Failed to fetch" ? err.message : "Запустите сайт командой python3 tools/server.py.");
        })
        .then(function () { btn.disabled = false; btn.textContent = "Отправить запрос"; });
    });
    $$("input, textarea, select", form).forEach(function (el) { el.addEventListener("input", function () { el.classList.remove("is-invalid"); }); });
  });
})();
