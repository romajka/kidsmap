// Templates keep both the scripts and their configuration inert until a section is near.
(function () {
  for (const group of document.querySelectorAll("template[data-scripts-near]")) {
    const targets = Array.from(document.querySelectorAll(group.dataset.scriptsNear));
    if (!targets.length) continue;
    const sources = Array.from(group.content.querySelectorAll("script[src]"));
    let pending = false;
    let observer;

    async function load() {
      if (pending) return;
      pending = true;
      try {
        while (sources.length) {
          const source = sources[0];
          await new Promise((resolve, reject) => {
            const script = document.createElement("script");
            for (const {name, value} of source.attributes) script.setAttribute(name, value);
            script.onload = resolve;
            script.onerror = () => { script.remove(); reject(new Error("Script unavailable")); };
            document.head.appendChild(script);
          });
          sources.shift();
        }
        observer?.disconnect();
        for (const target of targets) {
          target.removeEventListener("focusin", load);
          target.removeEventListener("pointerdown", load);
        }
      } catch {
        // A later intersection or interaction retries the unfinished part of this group.
      } finally {
        pending = false;
      }
    }

    if (!("IntersectionObserver" in window)) { load(); continue; }
    observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting && entry.target.getClientRects().length)) load();
    }, {rootMargin: "160px 0px"});
    for (const target of targets) {
      observer.observe(target);
      target.addEventListener("focusin", load);
      target.addEventListener("pointerdown", load, {passive: true});
    }
  }
}());
