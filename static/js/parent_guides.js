/* Deep links and optional motion. Native disclosures also work without JS. */
(() => {
  "use strict";

  const guide = document.querySelector(".parent-guide");
  if (!guide) return;

  function openLinkedAnswer() {
    const id = window.location.hash.slice(1);
    if (!/^(guide-faq-[a-z-]+|park-area-[a-z_-]+)$/.test(id)) return;
    const answer = document.getElementById(id);
    if (answer && guide.contains(answer) && answer.matches(".pg-faq details, details.pg-district")) {
      answer.open = true;
    }
  }
  openLinkedAnswer();
  window.addEventListener("hashchange", openLinkedAnswer);

  // Progressive interactive filter chips for places
  function initPlacesFilterBar() {
    const section = guide.querySelector("#guide-places");
    if (!section) return;
    const grid = section.querySelector(".pg-places__grid");
    if (!grid) return;
    const places = Array.from(grid.querySelectorAll(".pg-place"));
    if (places.length < 3) return;

    const lang = document.documentElement.lang || "ru";
    const allLabel = lang.startsWith("az") ? "Bütün məkanlar" : (lang.startsWith("en") ? "All places" : "Все места");

    const categoriesMap = new Map();

    places.forEach((p) => {
      const loc = p.querySelector(".pg-place__location")?.textContent.trim() || "";
      const topicSpans = Array.from(p.querySelectorAll(".pg-place__topics > span"));
      const topics = topicSpans.map((s) => s.textContent.trim()).filter(Boolean);

      const placeTokens = new Set();

      if (loc) {
        const parts = loc.split(",").map((s) => s.trim()).filter(Boolean);
        parts.forEach((part) => {
          if (parts.length > 1 && /^(баку|bakı|baku)$/i.test(part)) return;
          if (part.length > 2) {
            const key = "loc:" + part.toLowerCase();
            placeTokens.add(key);
            if (!categoriesMap.has(key)) {
              categoriesMap.set(key, { key, label: part, count: 0, priority: 1 });
            }
            categoriesMap.get(key).count += 1;
          }
        });
      }

      topics.forEach((t) => {
        if (t.length > 2) {
          const key = "topic:" + t.toLowerCase();
          placeTokens.add(key);
          if (!categoriesMap.has(key)) {
            categoriesMap.set(key, { key, label: t, count: 0, priority: 2 });
          }
          categoriesMap.get(key).count += 1;
        }
      });

      p.dataset.filterTokens = Array.from(placeTokens).join("|");
    });

    if (categoriesMap.size < 2) return;

    const filterList = Array.from(categoriesMap.values())
      .filter((c) => c.count < places.length && (places.length <= 4 || c.count < places.length - 1) && c.count > 0)
      .sort((a, b) => b.count - a.count);

    if (filterList.length < 2) return;

    const visibleChips = filterList.slice(0, 6);

    const filterBar = document.createElement("nav");
    filterBar.className = "pg-places-filter-bar";
    filterBar.setAttribute("aria-label", allLabel);

    const allBtn = document.createElement("button");
    allBtn.type = "button";
    allBtn.className = "pg-filter-chip is-active";
    allBtn.setAttribute("data-target", "all");
    allBtn.setAttribute("aria-pressed", "true");
    allBtn.innerHTML = `<span>${allLabel}</span><span class="pg-filter-chip__count">${places.length}</span>`;
    filterBar.appendChild(allBtn);

    visibleChips.forEach((chip) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "pg-filter-chip";
      btn.setAttribute("data-target", chip.key);
      btn.setAttribute("aria-pressed", "false");
      btn.innerHTML = `<span>${chip.label}</span><span class="pg-filter-chip__count">${chip.count}</span>`;
      filterBar.appendChild(btn);
    });

    section.insertBefore(filterBar, grid);

    const prefersReducedMotion = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    filterBar.addEventListener("click", (e) => {
      const btn = e.target.closest(".pg-filter-chip");
      if (!btn || btn.classList.contains("is-active")) return;

      filterBar.querySelectorAll(".pg-filter-chip").forEach((b) => {
        b.classList.remove("is-active");
        b.setAttribute("aria-pressed", "false");
      });
      btn.classList.add("is-active");
      btn.setAttribute("aria-pressed", "true");
      const target = btn.getAttribute("data-target");

      places.forEach((p) => {
        if (p._filterTimeout) {
          clearTimeout(p._filterTimeout);
          p._filterTimeout = null;
        }

        const tokens = (p.dataset.filterTokens || "").split("|");
        const matches = target === "all" || tokens.includes(target);

        if (matches) {
          p.hidden = false;
          p.style.display = "flex";
          if (!prefersReducedMotion) {
            p.style.opacity = "0";
            p.style.transform = "translateY(12px) scale(0.98)";
            requestAnimationFrame(() => {
              p.style.transition = "opacity 0.28s cubic-bezier(0.2, 0.65, 0.3, 1), transform 0.28s cubic-bezier(0.2, 0.65, 0.3, 1)";
              p.style.opacity = "1";
              p.style.transform = "translateY(0) scale(1)";
            });
          } else {
            p.style.opacity = "1";
            p.style.transform = "none";
          }
        } else {
          if (!prefersReducedMotion) {
            p.style.transition = "opacity 0.2s ease, transform 0.2s ease";
            p.style.opacity = "0";
            p.style.transform = "scale(0.95)";
            p._filterTimeout = setTimeout(() => {
              if (btn.classList.contains("is-active") && btn.getAttribute("data-target") === target) {
                p.style.display = "none";
                p.hidden = true;
              }
            }, 200);
          } else {
            p.style.display = "none";
            p.hidden = true;
          }
        }
      });
    });
  }
  initPlacesFilterBar();

  if (typeof window.matchMedia !== "function") return;

  const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (motion.matches || typeof Element.prototype.animate !== "function") return;

  const activeAnimations = new Set();
  let observer;
  let enabled = true;

  function animate(element, distance = 10, duration = 260, delay = 0) {
    if (!enabled || motion.matches || !element) return;
    try {
      const animation = element.animate(
        [
          { opacity: 0, transform: `translateY(${distance}px)` },
          { opacity: 1, transform: "translateY(0)" },
        ],
        { duration, delay, easing: "cubic-bezier(.2,.65,.3,1)", fill: "none" },
      );
      activeAnimations.add(animation);
      const forget = () => activeAnimations.delete(animation);
      animation.addEventListener("finish", forget, { once: true });
      animation.addEventListener("cancel", forget, { once: true });
    } catch (_) {
      // Content remains visible if animate fails.
    }
  }

  // Smooth accordion height expand/collapse animation for details disclosures
  class AnimatedDisclosure {
    constructor(el) {
      this.el = el;
      this.summary = el.querySelector("summary");
      this.content = el.querySelector(".pg-district__body, .pg-advice__body, .pg-faq__answer");
      if (!this.summary) return;
      this.animation = null;
      this.isClosing = false;
      this.isExpanding = false;

      this.summary.addEventListener("click", (e) => this.onClick(e));
    }

    onClick(e) {
      if (!enabled || motion.matches || typeof Element.prototype.animate !== "function") return;
      e.preventDefault();
      this.el.style.overflow = "hidden";

      if (this.isClosing || !this.el.open) {
        this.open();
      } else if (this.isExpanding || this.el.open) {
        this.shrink();
      }
    }

    shrink() {
      this.isClosing = true;
      const startHeight = this.el.getBoundingClientRect().height;
      const summaryHeight = this.summary.getBoundingClientRect().height;
      const borderY = this.el.offsetHeight - this.el.clientHeight;
      const endHeight = summaryHeight + borderY;

      if (this.animation) this.animation.cancel();

      try {
        this.animation = this.el.animate(
          { height: [`${startHeight}px`, `${endHeight}px`] },
          { duration: 250, easing: "cubic-bezier(.25, 1, .5, 1)" }
        );
        activeAnimations.add(this.animation);

        if (this.content) {
          this.content.animate(
            [
              { opacity: 1, transform: "translateY(0)" },
              { opacity: 0, transform: "translateY(-6px)" },
            ],
            { duration: 180, easing: "ease-in" }
          );
        }

        this.animation.onfinish = () => this.onAnimationFinish(false);
        this.animation.oncancel = () => {
          activeAnimations.delete(this.animation);
          this.isClosing = false;
        };
      } catch (_) {
        this.el.open = false;
        this.isClosing = false;
        this.el.style.height = "";
        this.el.style.overflow = "";
      }
    }

    open() {
      const startHeight = this.el.getBoundingClientRect().height;
      this.el.open = true;
      const endHeight = this.el.getBoundingClientRect().height;

      if (this.animation) this.animation.cancel();

      try {
        this.animation = this.el.animate(
          { height: [`${startHeight}px`, `${endHeight}px`] },
          { duration: 300, easing: "cubic-bezier(.25, 1, .5, 1)" }
        );
        activeAnimations.add(this.animation);

        if (this.content) {
          this.content.animate(
            [
              { opacity: 0, transform: "translateY(-8px)" },
              { opacity: 1, transform: "translateY(0)" },
            ],
            { duration: 260, easing: "cubic-bezier(.2, .65, .3, 1)" }
          );
        }

        this.animation.onfinish = () => this.onAnimationFinish(true);
        this.animation.oncancel = () => {
          activeAnimations.delete(this.animation);
          this.isExpanding = false;
        };
      } catch (_) {
        this.onAnimationFinish(true);
      }
    }

    onAnimationFinish(open) {
      this.el.open = open;
      if (this.animation) activeAnimations.delete(this.animation);
      this.animation = null;
      this.isClosing = false;
      this.isExpanding = false;
      this.el.style.height = "";
      this.el.style.overflow = "";
    }
  }

  // Bind animated disclosures
  guide.querySelectorAll(".pg-district, .pg-advice, .pg-faq details").forEach((el) => {
    new AnimatedDisclosure(el);
  });

  function stopMotion(event) {
    if (!event.matches) return;
    enabled = false;
    if (observer) observer.disconnect();
    activeAnimations.forEach((animation) => animation.cancel());
    activeAnimations.clear();
    guide.querySelectorAll(".pg-district, .pg-advice, .pg-faq details").forEach((el) => {
      el.style.height = "";
      el.style.overflow = "";
    });
  }

  if (typeof motion.addEventListener === "function") {
    motion.addEventListener("change", stopMotion);
  } else if (typeof motion.addListener === "function") {
    motion.addListener(stopMotion);
  }

  // Smooth scroll for TOC links
  const tocLinks = guide.querySelectorAll(".pg-toc a[href^='#']");
  tocLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      const targetId = link.getAttribute("href");
      if (!targetId || targetId === "#") return;
      const targetEl = guide.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
        if (history.pushState) {
          history.pushState(null, "", targetId);
        }
      }
    });
  });

  if (typeof window.IntersectionObserver !== "function") return;

  try {
    observer = new IntersectionObserver((entries) => {
      let stagger = 0;
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        animate(entry.target, 12, 280, stagger);
        stagger = (stagger + 40) % 80;
      });
    }, { threshold: 0.08 });

    guide.querySelectorAll(
      ".pg-hero__copy, .pg-hero__art, .pg-topic, .pg-place, .pg-empty, .pg-advice, .pg-faq details, .pg-related, .pg-district, .pg-planning-card, .pg-situation",
    ).forEach((element) => observer.observe(element));
  } catch (_) {
    if (observer) observer.disconnect();
  }
})();
