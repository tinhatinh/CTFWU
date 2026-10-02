/* Progressive enhancement: content and links work without JavaScript. */
(() => {
  "use strict";
  const vi = document.body.dataset.language === "vi";
  const themeButton = document.querySelector("#theme-toggle");
  themeButton?.addEventListener("click", () => {
    const theme =
      document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = theme;
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
  menu?.addEventListener("click", () => {
    const open = menu.getAttribute("aria-expanded") !== "true";
    menu.setAttribute("aria-expanded", String(open));
    nav.classList.toggle("is-open", open);
  });
  document.addEventListener("keydown", (event) => {
    if (
      event.key === "Escape" &&
      menu?.getAttribute("aria-expanded") === "true"
    ) {
      menu.setAttribute("aria-expanded", "false");
      nav.classList.remove("is-open");
      menu.focus();
    }
  });

  const list = document.querySelector("#archive-list");
  if (list) {
    const rows = [...list.querySelectorAll(".writeup-row")];
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
            row.dataset.category,
            row.dataset.event,
            row.dataset.search,
          ].join(" "),
        ),
      ]),
    );
    let category = "";
    const update = (persist = true) => {
      const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
      let visible = 0;
      for (const row of rows) {
        row.hidden = !!(
          (category && row.dataset.category !== category) ||
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
    document.querySelector("#reset-filters").addEventListener("click", () => {
      search.value = "";
      eventFilter.value = "";
      sort.value = "newest";
      category = "";
      update();
      search.focus();
    });
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
