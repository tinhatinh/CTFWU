/* CTFWU — bộ điều khiển chuyển động, Vân Hải, Parallax 3D & Chương mục (xian v2).
   - Giữ nguyên máy trạng thái ưu tiên: override phiên -> prefers-reduced-motion -> localStorage.
   - Parallax con trỏ dùng nội suy giảm chấn, tự ngắt rAF ngay khi hội tụ (0% CPU lúc đứng yên).
   - Tự động phát/tạm dừng video nền Tam Giới theo viewport, tab ẩn và nút chuyển động. */
(() => {
  "use strict";

  const root = document.documentElement;
  const KEY = "ctfwu-motion";
  const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(pointer: fine)");
  const toggle = document.querySelector(".motion-toggle");
  const hero = document.querySelector(".hero");
  const sideNav = document.querySelector(".xian-side-nav");
  const videos = [...document.querySelectorAll(".xian-bg-video")];

  let pref = read();
  let override = null;
  let revealer = null;
  let heroWatcher = null;
  let videoWatcher = null;
  let heroVisible = true;
  const visibleVideos = new Set();

  /* Trạng thái Parallax con trỏ cho Hero */
  let targetX = 0;
  let targetY = 0;
  let currentX = 0;
  let currentY = 0;
  let parallaxRaf = 0;

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
      /* Storage tùy chọn. */
    }
  }

  function isXian() {
    return root.dataset.theme === "xian";
  }

  function enabled() {
    if (override !== null) return override;
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

  function syncVideos() {
    const canPlay = enabled() && isXian() && !document.hidden;
    videos.forEach((video) => {
      if (canPlay && visibleVideos.has(video)) {
        const p = video.play();
        if (p && typeof p.catch === "function") p.catch(() => {});
      } else if (!video.paused) {
        video.pause();
      }
    });
  }

  function pauseState() {
    root.classList.toggle("motion-paused", document.hidden);
    root.classList.toggle("hero-offscreen", !heroVisible);
    if (document.hidden && parallaxRaf) {
      cancelAnimationFrame(parallaxRaf);
      parallaxRaf = 0;
    }
    syncVideos();
  }

  function watchViewports(on) {
    if (!("IntersectionObserver" in window)) return;
    if (hero) {
      if (on && !heroWatcher) {
        heroWatcher = new IntersectionObserver(
          (entries) => {
            heroVisible = entries[0].isIntersecting;
            pauseState();
          },
          { threshold: 0 }
        );
        heroWatcher.observe(hero);
        heroVisible = true;
      } else if (!on && heroWatcher) {
        heroWatcher.disconnect();
        heroWatcher = null;
        heroVisible = true;
      }
    }
    if (videos.length) {
      if (on && !videoWatcher) {
        videoWatcher = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) visibleVideos.add(entry.target);
              else visibleVideos.delete(entry.target);
            });
            syncVideos();
          },
          { rootMargin: "120px 0px", threshold: 0.02 }
        );
        videos.forEach((v) => videoWatcher.observe(v));
      } else if (!on && videoWatcher) {
        videoWatcher.disconnect();
        videoWatcher = null;
        visibleVideos.clear();
      }
    }
    pauseState();
  }

  /* ---------- Parallax 3D giảm chấn trên Hero ---------- */

  function stepParallax() {
    parallaxRaf = 0;
    if (!hero || !enabled() || !isXian() || document.hidden || !heroVisible) return;
    currentX += (targetX - currentX) * 0.085;
    currentY += (targetY - currentY) * 0.085;
    hero.style.setProperty("--px", currentX.toFixed(4));
    hero.style.setProperty("--py", currentY.toFixed(4));
    if (Math.abs(targetX - currentX) > 0.0015 || Math.abs(targetY - currentY) > 0.0015) {
      parallaxRaf = requestAnimationFrame(stepParallax);
    }
  }

  if (hero) {
    hero.addEventListener(
      "pointermove",
      (event) => {
        if (!finePointer.matches || !enabled() || !isXian() || !heroVisible) return;
        const w = window.innerWidth || 1;
        const h = window.innerHeight || 1;
        targetX = Math.max(-1, Math.min(1, (event.clientX / w - 0.5) * 2));
        targetY = Math.max(-1, Math.min(1, (event.clientY / h - 0.5) * 2));
        if (!parallaxRaf) parallaxRaf = requestAnimationFrame(stepParallax);
      },
      { passive: true }
    );
    hero.addEventListener(
      "pointerleave",
      () => {
        targetX = 0;
        targetY = 0;
        if (enabled() && isXian() && !parallaxRaf) {
          parallaxRaf = requestAnimationFrame(stepParallax);
        }
      },
      { passive: true }
    );
  }

  /* ---------- Ánh kim đèn lồng theo con trỏ trên thẻ ---------- */

  document.addEventListener(
    "pointermove",
    (event) => {
      if (!finePointer.matches || !enabled() || !isXian()) return;
      const card = event.target.closest && event.target.closest(".feature-card, .competition-card, .certificate-card");
      if (!card) return;
      const rect = card.getBoundingClientRect();
      card.style.setProperty("--mx", `${(event.clientX - rect.left).toFixed(0)}px`);
      card.style.setProperty("--my", `${(event.clientY - rect.top).toFixed(0)}px`);
    },
    { passive: true }
  );

  /* ---------- Chương mục dọc bên trái (.xian-side-nav) ---------- */

  if (sideNav) {
    const links = [...sideNav.querySelectorAll("a[data-chapter]")];
    const chapters = links
      .map((link) => document.getElementById(link.dataset.chapter))
      .filter(Boolean);

    if (chapters.length) {
      let navPending = false;
      const updateChapter = () => {
        navPending = false;
        if (!isXian()) return;
        const triggerY = window.innerHeight * 0.36;
        let activeIdx = 0;
        chapters.forEach((sec, idx) => {
          if (sec.getBoundingClientRect().top <= triggerY) activeIdx = idx;
        });
        sideNav.style.setProperty("--chapter-idx", String(activeIdx));
        links.forEach((link, idx) => {
          link.classList.toggle("is-active", idx === activeIdx);
          if (idx === activeIdx) link.setAttribute("aria-current", "location");
          else link.removeAttribute("aria-current");
        });
      };
      window.addEventListener(
        "scroll",
        () => {
          if (!navPending) {
            navPending = true;
            requestAnimationFrame(updateChapter);
          }
        },
        { passive: true }
      );
      window.addEventListener("resize", updateChapter);
      updateChapter();
    }
  }

  function resetParallax() {
    if (!hero) return;
    targetX = 0;
    targetY = 0;
    currentX = 0;
    currentY = 0;
    if (parallaxRaf) {
      cancelAnimationFrame(parallaxRaf);
      parallaxRaf = 0;
    }
    hero.style.removeProperty("--px");
    hero.style.removeProperty("--py");
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
        resetParallax();
        if (window.CTFWU && window.CTFWU.cancelMotion) window.CTFWU.cancelMotion();
      }
      watchViewports(on);
      syncVideos();
    } catch (_) {
      root.classList.remove("js-motion");
      revealAll();
    }
  }

  if (toggle) {
    toggle.addEventListener("click", () => {
      override = !enabled();
      pref = override;
      save(pref);
      apply();
    });
  }

  document.addEventListener("focusin", (event) => {
    const node = event.target.closest && event.target.closest(".reveal");
    if (!node || node.classList.contains("is-in")) return;
    node.classList.add("is-in");
    if (revealer) revealer.unobserve(node);
  });

  window.addEventListener("error", () => {
    root.classList.remove("js-motion");
    revealAll();
  });

  const onMedia = (event) => {
    if (event.matches) override = null;
    apply();
  };
  if (mq.addEventListener) mq.addEventListener("change", onMedia);
  else if (mq.addListener) mq.addListener(onMedia);

  document.addEventListener("visibilitychange", pauseState);

  apply();
  root.classList.add("motion-init");

  window.setTimeout(() => {
    document.querySelectorAll(".reveal:not(.is-in)").forEach((node) => {
      const rect = node.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom > 0) node.classList.add("is-in");
    });
  }, 1200);
})();
