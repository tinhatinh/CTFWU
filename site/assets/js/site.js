/* Progressive enhancement: content and links work without JavaScript. */
(() => {
  "use strict";
  const vi = document.body.dataset.language === "vi";
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const runningMotion = new Set();
  const animate = (element, frames, options) => {
    if (reducedMotion.matches || !element.animate) return;
    const animation = element.animate(frames, options);
    runningMotion.add(animation);
    animation.finished.then(() => runningMotion.delete(animation), () => runningMotion.delete(animation));
  };
  reducedMotion.addEventListener("change", () => {
    if (reducedMotion.matches) runningMotion.forEach(animation => animation.cancel());
  });
  // Content stays visible even if motion or IntersectionObserver is unavailable.
  if ("IntersectionObserver" in window && !reducedMotion.matches) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        animate(entry.target, [
          { opacity: 0.45, transform: "translateY(14px)" },
          { opacity: 1, transform: "translateY(0)" }
        ], { duration: 440, easing: "cubic-bezier(.2,.7,.2,1)" });
      });
    }, { threshold: 0.08 });
    document.querySelectorAll(".page-heading, .stats-strip, .section-heading, .feature-card, .certificate-card").forEach(element => observer.observe(element));
  }
  const themeButton = document.querySelector("#theme-toggle");
  themeButton?.setAttribute("aria-pressed", String(document.documentElement.dataset.theme === "dark"));
  themeButton?.addEventListener("click", () => {
    const theme =
      document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = theme;
    themeButton.setAttribute("aria-pressed", String(theme === "dark"));
    animate(themeButton.querySelector("svg"), [
      { transform: "rotate(-70deg) scale(.85)" },
      { transform: "rotate(0) scale(1)" }
    ], { duration: 320, easing: "ease-out" });
    document.querySelector('meta[name="theme-color"]').content =
      theme === "dark" ? "#111411" : "#f5f5ef";
    try {
      localStorage.setItem("ctf-theme", theme);
    } catch (_) {
      /* Storage is optional. */
    }
  });

  const menu = document.querySelector(".menu-toggle");
  const nav = document.querySelector("#main-nav");
  const closeMenu = () => {
    menu?.setAttribute("aria-expanded", "false");
    nav?.classList.remove("is-open");
  };
  menu?.addEventListener("click", () => {
    const open = menu.getAttribute("aria-expanded") !== "true";
    menu.setAttribute("aria-expanded", String(open));
    nav.classList.toggle("is-open", open);
    if (open) animate(nav, [
      { opacity: 0, transform: "translateY(-8px)" },
      { opacity: 1, transform: "translateY(0)" }
    ], { duration: 200, easing: "ease-out" });
  });
  document.addEventListener("click", event => {
    if (!event.target.closest(".header-inner")) closeMenu();
  });
  nav?.addEventListener("click", event => {
    if (event.target.closest("a")) closeMenu();
  });
  document.addEventListener("focusin", event => {
    if (!event.target.closest(".header-inner")) closeMenu();
  });
  window.matchMedia("(min-width: 601px)").addEventListener("change", closeMenu);
  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Escape" &&
      menu?.getAttribute("aria-expanded") === "true"
    ) {
      closeMenu();
      menu.focus();
    }
  });

  const list = document.querySelector("#archive-list");
  if (list) {
    const rows = [...list.querySelectorAll(".writeup-row")];
    const categoriesByRow = new Map(rows.map(row => [row, JSON.parse(row.dataset.categories)]));
    const search = document.querySelector("#archive-search");
    const eventFilter = document.querySelector("#event-filter");
    const sort = document.querySelector("#sort-order");
    const chips = [...document.querySelectorAll("[data-filter]")];
    const count = document.querySelector("#result-count");
    const empty = document.querySelector("#empty-state");
    const normalize = (text) =>
      text
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/đ/g, "d")
        .replace(/Đ/g, "D")
        .toLowerCase();
    const searchable = new Map(
      rows.map((row) => [
        row,
        normalize(
          [
            row.dataset.title,
            categoriesByRow.get(row).join(" "),
            row.dataset.event,
            row.dataset.search,
          ].join(" "),
        ),
      ]),
    );
    let category = "";
    const update = (persist = true) => {
      const previous = new Map();
      if (persist && !reducedMotion.matches) {
        rows.forEach(row => {
          if (row.hidden) return;
          const rect = row.getBoundingClientRect();
          if (rect.bottom > 0 && rect.top < innerHeight) previous.set(row, rect.top);
        });
        runningMotion.forEach(animation => animation.cancel());
      }
      const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
      let visible = 0;
      for (const row of rows) {
        row.hidden = !!(
          (category && !categoriesByRow.get(row).includes(category)) ||
          (eventFilter.value && row.dataset.event !== eventFilter.value) ||
          !words.every((word) => searchable.get(row).includes(word))
        );
        if (!row.hidden) visible++;
      }
      const ordered = [...rows].sort((a, b) =>
        sort.value === "name"
          ? a.dataset.title.localeCompare(b.dataset.title, vi ? "vi" : "en")
          : (Number(b.dataset.date) - Number(a.dataset.date)) *
            (sort.value === "oldest" ? -1 : 1),
      );
      ordered.forEach((row) => list.append(row));
      chips.forEach((chip) =>
        chip.setAttribute(
          "aria-pressed",
          String(chip.dataset.filter === category),
        ),
      );
      count.textContent = visible;
      empty.hidden = visible !== 0;
      list.hidden = visible === 0;
      const clear = document.querySelector("#clear-filters");
      if (clear) clear.hidden = !search.value.trim() && !category && !eventFilter.value && sort.value === "newest";
      if (persist) {
        ordered.filter(row => !row.hidden).forEach(row => {
          const top = row.getBoundingClientRect().top;
          if (top < 0 || top > innerHeight) return;
          const from = previous.get(row);
          if (from !== undefined && Math.abs(from - top) < 1) return;
          animate(row, from === undefined ? [
            { opacity: .35, transform: "translateY(6px)" }, { opacity: 1, transform: "translateY(0)" }
          ] : [
            { transform: `translateY(${from - top}px)` }, { transform: "translateY(0)" }
          ], { duration: 230, easing: "cubic-bezier(.2,.7,.2,1)" });
        });
      }
      const params = new URLSearchParams();
      if (search.value.trim()) params.set("q", search.value.trim());
      if (category) params.set("category", category);
      if (eventFilter.value) params.set("event", eventFilter.value);
      if (sort.value !== "newest") params.set("sort", sort.value);
      const suffix = params.size ? "?" + params.toString() : "";
      if (persist) history.replaceState(null, "", location.pathname + suffix);
      document.querySelectorAll(".language-switch a").forEach((link) => {
        link.search = suffix;
      });
    };
    const restore = () => {
      const params = new URLSearchParams(location.search);
      search.value = params.get("q") || "";
      category = chips.some(
        (chip) => chip.dataset.filter === params.get("category"),
      )
        ? params.get("category")
        : "";
      eventFilter.value = [...eventFilter.options].some(
        (option) => option.value === params.get("event"),
      )
        ? params.get("event")
        : "";
      sort.value = ["newest", "oldest", "name"].includes(params.get("sort"))
        ? params.get("sort")
        : "newest";
      update(false);
    };
    search.addEventListener("input", () => update());
    eventFilter.addEventListener("change", () => update());
    sort.addEventListener("change", () => update());
    chips.forEach((chip) =>
      chip.addEventListener("click", () => {
        category = chip.dataset.filter;
        update();
      }),
    );
    const resetFilters = () => {
      search.value = "";
      eventFilter.value = "";
      sort.value = "newest";
      category = "";
      update();
      search.focus();
    };
    document.querySelector("#reset-filters").addEventListener("click", resetFilters);
    document.querySelector("#clear-filters")?.addEventListener("click", resetFilters);
    document.addEventListener("keydown", (event) => {
      if (
        event.key === "/" &&
        !event.ctrlKey &&
        !event.metaKey &&
        !event.altKey &&
        !["INPUT", "TEXTAREA", "SELECT"].includes(
          document.activeElement.tagName,
        ) &&
        !document.activeElement.isContentEditable
      ) {
        event.preventDefault();
        search.focus();
      }
    });
    window.addEventListener("popstate", restore);
    restore();
  }

  document.querySelectorAll(".prose table").forEach((table) => {
    const wrapper = document.createElement("div");
    wrapper.className = "table-scroll";
    wrapper.tabIndex = 0;
    wrapper.setAttribute("role", "region");
    wrapper.setAttribute("aria-label", vi ? "Bảng dữ liệu" : "Data table");
    table.before(wrapper);
    wrapper.append(table);
  });
  document.querySelectorAll(".prose pre").forEach((pre) => {
    const parent = pre.parentElement;
    const host = parent.classList.contains("highlight") ? parent : pre;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy-code";
    const label = vi ? "Sao chép" : "Copy";
    button.textContent = label;
    button.setAttribute(
      "aria-label",
      vi ? "Sao chép đoạn code" : "Copy code block",
    );
    button.addEventListener("click", async () => {
      try {
        const code = pre.querySelector("code");
        const clone = pre.cloneNode(true);
        clone.querySelectorAll("button").forEach((node) => node.remove());
        await navigator.clipboard.writeText(
          code ? code.textContent : clone.textContent,
        );
        button.textContent = vi ? "Đã sao chép" : "Copied";
      } catch (_) {
        button.textContent = vi
          ? "Chọn code để sao chép"
          : "Select code to copy";
      }
      setTimeout(() => {
        button.textContent = label;
      }, 2000);
    });
    host.append(button);
  });

  const certificates = [...document.querySelectorAll('.certificate-card')];
  if (certificates.length) {
    const controls = document.querySelector('.certificate-controls');
    const search = document.querySelector('#certificate-search');
    const type = document.querySelector('#certificate-type');
    const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,'d').toLowerCase();
    if (certificates.length > 3 || type.options.length > 2) controls.hidden = false;
    const filter = () => {
      const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
      certificates.forEach(card => { card.hidden = !!((type.value && card.dataset.type !== type.value) || !words.every(word=>normalize(card.dataset.search).includes(word))); });
      document.querySelector('#certificate-empty').hidden = certificates.some(card=>!card.hidden);
    };
    search.addEventListener('input',filter);type.addEventListener('change',filter);
    document.querySelectorAll('.copy-certificate').forEach(button=>button.addEventListener('click',async()=>{
      const status=document.querySelector('#certificate-copy-status');
      try { await navigator.clipboard.writeText(button.dataset.copy);status.textContent=vi?'Đã sao chép mã chứng nhận.':'Certificate ID copied.'; }
      catch (_) { status.textContent=vi?'Không sao chép được. Hãy chọn mã để sao chép thủ công.':'Could not copy. Select the ID to copy manually.'; }
    }));
  }
  const topLink = document.querySelector('#back-to-top');
  const topRing = document.querySelector('#top-progress');
  if (topLink && topRing) {
    let scheduled = false;
    const updateTop = () => {
      scheduled = false;
      const range = document.documentElement.scrollHeight - window.innerHeight;
      const percent = range > 0 ? Math.min(100, Math.max(0, window.scrollY / range * 100)) : 0;
      topRing.style.strokeDashoffset = String(100 - percent);
      topLink.classList.toggle('is-scrolled', window.scrollY > 200);
    };
    window.addEventListener('scroll', () => { if (!scheduled) { scheduled = true; requestAnimationFrame(updateTop); } }, {passive:true});
    window.addEventListener('resize', updateTop);
    window.addEventListener('load', updateTop);
    updateTop();
  }
  const article = document.querySelector("#article-content");
  if (article) {
    const headings = [...article.querySelectorAll("h2, h3")];
    const toc = document.querySelector("#toc-links");
    headings.forEach((heading, index) => {
      if (!heading.id) heading.id = "section-" + index;
      const item = document.createElement("li");
      if (heading.tagName === "H3") item.className = "toc-sub";
      const anchor = document.createElement("a");
      anchor.href = "#" + encodeURIComponent(heading.id);
      anchor.textContent = heading.textContent;
      item.append(anchor);
      toc.append(item);
    });
    if (!headings.length) document.querySelector("#toc").hidden = true;
    const links = [...toc.querySelectorAll("a")];
    const bar = document.querySelector("#reading-progress");
    let pending = false;
    const progress = () => {
      pending = false;
      const rect = article.getBoundingClientRect();
      const range = Math.max(1, rect.height - window.innerHeight + 130);
      bar.style.width =
        Math.min(100, Math.max(0, ((130 - rect.top) / range) * 100)) + "%";
      let active = 0;
      headings.forEach((heading, i) => {
        if (heading.getBoundingClientRect().top <= 160) active = i;
      });
      links.forEach((link, i) => {
        link.classList.toggle("active", i === active);
        if (i === active) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    };
    window.addEventListener(
      "scroll",
      () => {
        if (!pending) {
          pending = true;
          requestAnimationFrame(progress);
        }
      },
      { passive: true },
    );
    window.addEventListener("resize", progress);
    progress();
  }
})();
