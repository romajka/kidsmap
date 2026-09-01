/*
 * KidsMap — motion behaviour.
 *
 * Two jobs:
 *   1. Pair the catalog card cover with the detail hero across a cross-document
 *      view transition, so the photo morphs instead of cutting.
 *   2. Fire the favourite burst on click.
 *
 * Everything here is progressive enhancement. Browsers without the View
 * Transition API navigate exactly as they did before.
 */
(() => {
  "use strict";

  const COVER_NAME = "place-cover";
  const PLACE_URL = /\/place\/\d+-/;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");

  /* The name has to be unique per document, so it is applied to a single
   * element for the duration of one navigation and cleared afterwards. */
  const tag = (el) => {
    if (!el) return null;
    el.style.viewTransitionName = COVER_NAME;
    return el;
  };

  const untag = (el) => {
    if (el) el.style.viewTransitionName = "";
  };

  /* ---- outgoing page: tag the cover of the card being opened ------------ */

  let pendingCover = null;

  document.addEventListener(
    "click",
    (event) => {
      if (reduced.matches) return;
      const link = event.target.closest("a[href]");
      if (!link || !PLACE_URL.test(link.getAttribute("href") || "")) return;

      const card = link.closest(".card, .place-card");
      if (!card) return;

      pendingCover =
        card.querySelector(".card-media-img") ||
        card.querySelector(".image-placeholder");
    },
    true
  );

  window.addEventListener("pageswap", (event) => {
    if (!event.viewTransition) return;
    const target = event.activation && event.activation.entry;
    if (!target || !PLACE_URL.test(target.url)) return;

    const el = tag(pendingCover);
    // Names must not leak into the back/forward cache snapshot.
    event.viewTransition.finished.then(() => untag(el));
  });

  /* ---- incoming page: tag the hero so the pair resolves ----------------- */

  window.addEventListener("pagereveal", (event) => {
    if (!event.viewTransition) return;
    if (!PLACE_URL.test(window.location.pathname)) return;

    const hero =
      document.querySelector(".place-gallery__image") ||
      document.querySelector(".detail-top-media img");

    const el = tag(hero);
    event.viewTransition.ready.finally(() => untag(el));
  });

  /* ---- favourite burst -------------------------------------------------- */

  document.addEventListener("click", (event) => {
    const btn = event.target.closest(".like-btn");
    if (!btn || reduced.matches) return;

    btn.classList.remove("is-bursting");
    // Force a reflow so the class can be re-applied within the same gesture.
    void btn.offsetWidth;
    btn.classList.add("is-bursting");

    btn.addEventListener(
      "animationend",
      () => btn.classList.remove("is-bursting"),
      { once: true }
    );
  });
})();
