/* CTFWU — điều khiển chuyển động P0.
   Không có vòng lặp rAF cho trang trí: sương/hạt là CSS animation, nên tạm dừng
   chỉ là đổi animation-play-state.
   Thanh tiến độ và mục lục do site.js phụ trách; ở đây không làm lại. */
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
      /* Storage bị chặn: chỉ mất ghi nhớ, hiệu ứng vẫn theo media query. */
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
    const label = on ? toggle.dataset.labelActive : toggle.dataset.labelInactive;
    if (label) {
      toggle.setAttribute("aria-label", label);
      toggle.title = label;
    }
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
      /* Không đọc layout ở đây: observer sẽ báo trạng thái ở frame kế tiếp. */
      heroVisible = true;
    } else if (!on && heroWatcher) {
      heroWatcher.disconnect();
      heroWatcher = null;
      heroVisible = true;
      pause();
    }
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
        if (window.CTFWU && window.CTFWU.cancelMotion) window.CTFWU.cancelMotion();
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
      /* pref phải theo kịp lựa chọn mới, nếu không media change sẽ đọc lại giá trị lúc tải. */
      pref = override;
      save(pref);
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

  /* Đổi theme bằng nút: hero có thể xuất hiện hoặc biến mất. */
  if ("MutationObserver" in window) {
    new MutationObserver(apply).observe(root, {
      attributes: true,
      attributeFilter: ["data-theme"]
    });
  }

  apply();
  root.classList.add("motion-init");

  /* Lưới an toàn: sau khi ổn định, ép hiện những khối đang nằm trong màn hình. */
  window.setTimeout(() => {
    document.querySelectorAll(".reveal:not(.is-in)").forEach((node) => {
      const rect = node.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom > 0) node.classList.add("is-in");
    });
  }, 1200);
})();
