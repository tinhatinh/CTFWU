/* Chuyen ngon ngu VI/EN khong tai lai trang.
   Logic chinh: fetch HTML ban doi ung, replaceChild(<html>), chay lai script.
   Nang cap 2026-10-02: fade-out/in mua sat truoc/sau swap de tranh nhay man hinh;
   spinner tren pill trong luc fetch; khong the view-transition API vi Chirpy chen SW
   va cache co the tra HTML cu. */

(function () {
  "use strict";

  if (window.ctfwLang) return;
  window.ctfwLang = true;

  /* Lay URL cua ngon ngu doi ung tu pill #ctfw-lang */
  function otherHref() {
    var pill = document.getElementById("ctfw-lang");
    if (!pill) return null;
    var here = location.pathname;
    var links = pill.querySelectorAll("a");
    for (var i = 0; i < links.length; i++) {
      var path = links[i].getAttribute("href").split("?")[0];
      if (path !== here) return path + location.search;
    }
    return null;
  }

  /* Chay lai toan bo <script> sau khi swap documentElement.
     Script chen qua DOM khong tu chay -> phai tao node moi. */
  function runScripts(root) {
    var chain = Promise.resolve();
    [].slice.call(root.querySelectorAll("script")).forEach(function (old) {
      chain = chain.then(function () {
        var fresh = document.createElement("script");
        [].forEach.call(old.attributes, function (a) {
          fresh.setAttribute(a.name, a.value);
        });
        if (!fresh.src) fresh.textContent = old.textContent;
        old.parentNode.replaceChild(fresh, old);
        if (!fresh.src) return;
        return new Promise(function (done) { fresh.onload = fresh.onerror = done; });
      });
    });
    return chain;
  }

  /* Khoi phuc vi tri cuon, tat smooth truoc khi set de tranh dong cuon. */
  function restoreScroll(top) {
    var root = document.documentElement;
    root.style.scrollBehavior = "auto";
    window.scrollTo(0, top);
    setTimeout(function () {
      window.scrollTo(0, top);
      root.style.scrollBehavior = "";
    }, 80);
  }

  /* Them CSS transition 1 lan duy nhat vao <head> */
  var STYLE_ID = "ctfw-fade-style";
  function ensureFadeStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = [
      "#ctfw-lang a { transition: background 150ms, color 150ms, opacity 150ms; }",
      "#ctfw-lang a.ctfw-loading { opacity: .5; pointer-events: none; cursor: wait; }",
      "@keyframes ctfw-spin { to { transform: rotate(360deg); } }",
      "#ctfw-lang a.ctfw-loading::after {",
      "  content: '';",
      "  display: inline-block;",
      "  width: 10px; height: 10px;",
      "  border: 2px solid currentColor;",
      "  border-top-color: transparent;",
      "  border-radius: 50%;",
      "  margin-left: 6px;",
      "  animation: ctfw-spin .6s linear infinite;",
      "  vertical-align: middle;",
      "}",
      /* Fade overlay tren <body> */
      "#ctfw-fade {",
      "  position: fixed; inset: 0; z-index: 99999;",
      "  background: var(--bg, #f5f7fa);",
      "  opacity: 0; pointer-events: none;",
      "  transition: opacity 120ms ease;",
      "}",
      "#ctfw-fade.ctfw-out { opacity: 1; pointer-events: all; }"
    ].join("\n");
    document.head.appendChild(s);
  }

  /* Tao hoac lay overlay fade */
  function getFade() {
    var el = document.getElementById("ctfw-fade");
    if (!el) {
      el = document.createElement("div");
      el.id = "ctfw-fade";
      document.body.appendChild(el);
    }
    return el;
  }

  /* Fade out -> fetch -> swap -> fade in */
  function swap(url, push) {
    ensureFadeStyle();

    /* Hien thi spinner tren nut vua click */
    var pill = document.getElementById("ctfw-lang");
    var loadingLink = pill && pill.querySelector("a:not([aria-current=true])");
    if (loadingLink) loadingLink.classList.add("ctfw-loading");

    /* Fade out body (120ms) truoc khi fetch de tranh flicker */
    var fade = getFade();
    var top = window.scrollY;

    /* Bat dau fade out */
    requestAnimationFrame(function () {
      fade.classList.add("ctfw-out");
    });

    /* Fetch song song voi fade (fetch thuong mat 50-300ms, fade mat 120ms) */
    var fetchP = fetch(url, { credentials: "same-origin", cache: "no-cache" })
      .then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.text();
      });

    /* Doi ca fade ra lan fetch xong (min 130ms) truoc khi swap */
    Promise.all([
      fetchP,
      new Promise(function (res) { setTimeout(res, 130); })
    ])
    .then(function (results) {
      var text = results[0];
      var parsed = new DOMParser().parseFromString(text, "text/html");
      if (!parsed.getElementById("ctfw-lang")) throw new Error("not CTFWU page");

      /* Swap */
      document.replaceChild(
        document.importNode(parsed.documentElement, true),
        document.documentElement
      );
      return runScripts(document);
    })
    .then(function () {
      if (push) history.pushState({ ctfwLang: true }, "", url);
      restoreScroll(top);

      /* Fade in */
      var newFade = document.getElementById("ctfw-fade");
      if (newFade) {
        /* Bao dam opacity=1 truoc khi animate ve 0 */
        newFade.style.transition = "none";
        newFade.classList.add("ctfw-out");
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            newFade.style.transition = "";
            newFade.classList.remove("ctfw-out");
          });
        });
      }

      warm();
    })
    .catch(function () {
      /* Fallback: tai lai binh thuong */
      location.assign(url);
    });
  }

  /* Prefetch trang doi ung de lan bam dau tien khong phai cho. */
  function warm() {
    var url = otherHref();
    if (!url) return;
    var link = document.createElement("link");
    link.rel = "prefetch";
    link.href = url;
    document.head.appendChild(link);
  }

  document.addEventListener("click", function (ev) {
    if (ev.defaultPrevented || ev.button !== 0 ||
        ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    var link = ev.target.closest && ev.target.closest("#ctfw-lang a");
    if (!link) return;
    var url = link.getAttribute("href");
    if (!url || url.split("?")[0] === location.pathname) return;
    ev.preventDefault();
    swap(url, true);
  });

  window.addEventListener("popstate", function () {
    var pill = document.getElementById("ctfw-lang");
    var current = pill && [].slice.call(pill.querySelectorAll("a")).some(function (a) {
      return a.getAttribute("href").split("?")[0] === location.pathname;
    });
    if (current) swap(location.pathname, false);
  });

  if (window.requestIdleCallback) requestIdleCallback(warm);
  else setTimeout(warm, 1200);
})();
