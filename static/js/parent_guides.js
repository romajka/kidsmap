/* Optional motion. Native links/disclosures and every section work without it. */
(() => {
  "use strict";

  const guide = document.querySelector(".parent-guide");
  if (!guide || typeof window.matchMedia !== "function") return;

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

  function onToggle(event) {
    const details = event.target;
    if (!details.matches(".pg-advice, .pg-faq details") || !details.open) return;
    const content = details.querySelector(".pg-advice__body, .pg-faq__answer");
    if (content) {
      animate(content, 8, 220);
    }
  }

  function stopMotion(event) {
    if (!event.matches) return;
    enabled = false;
    if (observer) observer.disconnect();
    guide.removeEventListener("toggle", onToggle, true);
    activeAnimations.forEach((animation) => animation.cancel());
    activeAnimations.clear();
  }

  if (typeof motion.addEventListener === "function") {
    motion.addEventListener("change", stopMotion);
  } else if (typeof motion.addListener === "function") {
    motion.addListener(stopMotion);
  }

  guide.addEventListener("toggle", onToggle, true);

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
      ".pg-hero__copy, .pg-hero__art, .pg-topic, .pg-place, .pg-empty, .pg-advice, .pg-faq details, .pg-related",
    ).forEach((element) => observer.observe(element));
  } catch (_) {
    if (observer) observer.disconnect();
  }
})();
