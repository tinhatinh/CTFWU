/* CTFWU — điều khiển chuyển động cho preview.
   Không có vòng lặp rAF cho trang trí: sương/hạt là CSS animation,
   nên tạm dừng chỉ là đổi animation-play-state. */
(() => {
  "use strict";

  const root = document.documentElement;
  const KEY = "ctfwu-motion";
  const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  const toggle = document.querySelector(".motion-toggle");

  let pref = read();
  /* Chỉ đặt khi người dùng bấm nút trong phiên này. Không lưu, không lấn media query. */
  let override = null;
  let revealer = null;
  let heroWatcher = null;
  let heroVisible = true;
  let scheduled = false;

  function read() {
    try {
      const value = localStorage.getItem(KEY);
      return value === "on" ? true : value === "off" ? false : null;
    } catch (_) {
      return null;
    }
  }

  function save(value) {
    try {
      if (value === null) localStorage.removeItem(KEY);
      else localStorage.setItem(KEY, value ? "on" : "off");
    } catch (_) {
      /* Storage bị chặn: chỉ mất ghi nhớ, hiệu ứng vẫn chạy theo media query. */
    }
  }

  function enabled() {
    if (override !== null) return override;
    /* reduced-motion thắng khi tải, kể cả storage đã lưu "on". */
    if (mq.matches) return false;
    return pref !== false;
  }

  function mark(on) {
    root.classList.toggle("motion-on", on);
    root.classList.toggle("motion-off", !on);
    if (!toggle) return;
    toggle.setAttribute("aria-pressed", String(on));
    const label = on ? "Tắt chuyển động" : "Bật chuyển động";
    toggle.setAttribute("aria-label", label);
    toggle.title = label;
  }

  function revealAll() {
    document.querySelectorAll(".reveal:not(.is-in)").forEach((node) => node.classList.add("is-in"));
  }

  function onReveal(entries) {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-in");
      revealer.unobserve(entry.target);
    });
  }

  function startReveal() {
    if (!("IntersectionObserver" in window)) return false;
    if (!revealer) {
      revealer = new IntersectionObserver(onReveal, {
        rootMargin: "0px 0px -6% 0px",
        threshold: 0.06
      });
    }
    document.querySelectorAll(".reveal:not(.is-in)").forEach((node) => revealer.observe(node));
    return true;
  }

  function pause() {
    root.classList.toggle("motion-paused", document.hidden || !heroVisible);
  }

  function watchHero(on) {
    const hero = document.querySelector(".hero");
    if (!hero || !("IntersectionObserver" in window)) return;
    if (on && !heroWatcher) {
      heroWatcher = new IntersectionObserver(
        (entries) => {
          heroVisible = entries[0].isIntersecting;
          pause();
        },
        { threshold: 0 }
      );
      heroWatcher.observe(hero);
      /* Không đọc layout ở đây: observer sẽ tự báo trạng thái ở frame kế tiếp. */
      heroVisible = true;
    } else if (!on && heroWatcher) {
      heroWatcher.disconnect();
      heroWatcher = null;
      heroVisible = true;
      pause();
    }
  }

  function revealVisible() {
    document.querySelectorAll(".reveal:not(.is-in)").forEach((node) => {
      const rect = node.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom > 0) node.classList.add("is-in");
    });
  }

  function apply() {
    const on = enabled();
    try {
      mark(on);
      if (on) {
        let ok = false;
        try {
          ok = startReveal();
        } catch (_) {
          ok = false;
        }
        root.classList.toggle("js-motion", ok);
        if (!ok) revealAll();
      } else {
        root.classList.remove("js-motion");
        revealAll();
      }
      watchHero(on);
    } catch (_) {
      /* Bất kỳ lỗi nào cũng không được để nội dung bị giấu. */
      root.classList.remove("js-motion");
      revealAll();
    }
  }

  if (toggle) {
    toggle.addEventListener("click", () => {
      override = !enabled();
      save(override);
      apply();
    });
  }

  /* Bàn phím đi vào một khối chưa reveal: hiện ngay khối đó. */
  document.addEventListener("focusin", (event) => {
    const node = event.target.closest && event.target.closest(".reveal");
    if (!node || node.classList.contains("is-in")) return;
    node.classList.add("is-in");
    if (revealer) revealer.unobserve(node);
  });

  /* Lỗi script bất kỳ: bỏ reveal, không để nội dung mất hút. */
  window.addEventListener("error", () => {
    root.classList.remove("js-motion");
    revealAll();
  });

  const onMedia = (event) => {
    /* Hệ thống bật giảm chuyển động: cắt ngay, bỏ lựa chọn trong phiên.
       Lựa chọn đã lưu vẫn giữ để dùng lại khi hệ thống tắt. */
    if (event.matches) override = null;
    apply();
  };
  if (mq.addEventListener) mq.addEventListener("change", onMedia);
  else if (mq.addListener) mq.addListener(onMedia);

  document.addEventListener("visibilitychange", pause);

  apply();
  root.classList.add("motion-init");

  /* Khối hero không nằm trong reveal: luôn hiện ngay, không phụ thuộc JS. */

  /* Lưới an toàn: sau khi ổn định, ép hiện những khối đang nằm trong màn hình. */
  window.setTimeout(revealVisible, 1200);

  /* ---------- thanh tiến độ + mục lục đang đọc ---------- */

  const bar = document.querySelector("#reading-progress");
  const article = document.querySelector("#article-content");
  const tocLinks = Array.from(document.querySelectorAll("#toc-links a"));
  const headings = article
    ? Array.from(article.querySelectorAll("h2, h3")).filter((h) => h.id)
    : [];

  function readingState() {
    scheduled = false;
    if (!article) return;
    const rect = article.getBoundingClientRect();
    const span = Math.max(1, rect.height - window.innerHeight + 130);
    const ratio = Math.min(1, Math.max(0, (130 - rect.top) / span));
    if (bar) bar.style.transform = "scaleX(" + ratio.toFixed(4) + ")";

    if (!tocLinks.length) return;
    let active = 0;
    for (let i = 0; i < headings.length; i += 1) {
      if (headings[i].getBoundingClientRect().top <= 170) active = i;
    }
    tocLinks.forEach((link, i) => {
      const on = i === active;
      link.classList.toggle("active", on);
      if (on) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  }

  if (article) {
    const request = () => {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(readingState);
    };
    window.addEventListener("scroll", request, { passive: true });
    window.addEventListener("resize", request);
    window.addEventListener("load", request);
    request();
  }
})();
