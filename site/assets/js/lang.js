/* Doi ngon ngu VI/EN khong tai lai trang: lay HTML cua trang doi ung, thay ca
   <html> roi chay lai cac <script>. Node <script> chen qua DOM API khong tu
   chay, nen phai tai tao chung. CSS/anh da co trong bo nho nen chuyen chi mat
   vai chuc ms va giu duoc vi tri cuon. */

(function () {
  "use strict";

  /* window song qua lan thay documentElement, nen neo co vao day chu khong
     vao attribute cua pill: script nay se chay lan nua sau khi swap. */
  if (window.ctfwLang) return;
  window.ctfwLang = true;

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
        return new Promise(function (done) {
          fresh.onload = fresh.onerror = done;
        });
      });
    });
    return chain;
  }

  function at(top) {
    /* Chirpy dat `scroll-behavior: smooth` tren <html> nen scrollTo bi hieu
       thanh dong cuon; tat no trong luc dat lai vi tri cu. setTimeout chu khong
       rAF de van chay duoc khi tab an. */
    var root = document.documentElement;
    root.style.scrollBehavior = "auto";
    window.scrollTo(0, top);
    setTimeout(function () {
      window.scrollTo(0, top);
      root.style.scrollBehavior = "";
    }, 80);
  }

  function swap(url, push) {
    var top = window.scrollY;
    return fetch(url, { credentials: "same-origin" })
      .then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.text();
      })
      .then(function (text) {
        var parsed = new DOMParser().parseFromString(text, "text/html");
        if (!parsed.getElementById("ctfw-lang")) throw new Error("khong phai trang CTFWU");
        document.replaceChild(document.importNode(parsed.documentElement, true), document.documentElement);
        return runScripts(document);
      })
      .then(function () {
        if (push) history.pushState({ ctfwLang: true }, "", url);
        at(top);
        warm();
      })
      .catch(function () {
        location.assign(url);
      });
  }

  /* Nap som trang doi ung vao bo nho dem de lan bam dau tien khong phai cho. */
  function warm() {
    var url = otherHref();
    if (!url) return;
    var link = document.createElement("link");
    link.rel = "prefetch";
    link.href = url;
    document.head.appendChild(link);
  }

  document.addEventListener("click", function (ev) {
    if (ev.defaultPrevented || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    var link = ev.target.closest && ev.target.closest("#ctfw-lang a");
    if (!link) return;
    var url = link.getAttribute("href");
    if (!url || url === location.pathname) return;
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
