/* Place cards: a ripple from the finger on the round buttons and a pop on the
 * heart (styles in css/components/km_card_refine.css). Delegated, so cards
 * that arrive later (pagination, map lists) get it too. */
(function () {
  "use strict";
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var BUTTONS = ".place-card .card-go-btn, .place-card .card-contact-toggle";

  document.addEventListener("pointerdown", function (e) {
    var btn = e.target.closest && e.target.closest(BUTTONS);
    if (!btn) return;
    var r = btn.getBoundingClientRect();
    var dot = document.createElement("span");
    dot.className = "km-ripple-dot";
    dot.style.setProperty("--rx", (e.clientX - r.left) + "px");
    dot.style.setProperty("--ry", (e.clientY - r.top) + "px");
    btn.appendChild(dot);
    window.setTimeout(function () { dot.remove(); }, 600);
  }, { passive: true });

  document.addEventListener("click", function (e) {
    var heart = e.target.closest && e.target.closest(".place-card .like-btn");
    if (!heart) return;
    heart.classList.remove("km-pop");
    void heart.offsetWidth;
    heart.classList.add("km-pop");
    window.setTimeout(function () { heart.classList.remove("km-pop"); }, 650);
  });
})();
