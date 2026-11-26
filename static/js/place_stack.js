/* Place photos as a hand-held stack (2026-11-26).
 * - drag or swipe the top photo away; it slides under the stack
 * - photos underneath peek out, turned a little, and come forward as you drag
 * - with a mouse the top photo leans towards the pointer, with a soft glare
 * - ← → keys, the arrow buttons and a counter; Enter / tap opens full screen
 * - full screen: swipe, ← → keys, Esc, tap outside to close
 * Without JS the photos are links in a scrolling row (see place_poster.css).
 */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  var EASE = "cubic-bezier(.2,.8,.2,1)";

  function mount(root) {
    var deck = root.querySelector(".km-pstack__deck");
    var cards = Array.prototype.slice.call(root.querySelectorAll("[data-km-pstack-card]"));
    if (!deck || !cards.length) return;
    var n = cards.length;
    var order = cards.map(function (_, i) { return i; });
    var current = root.querySelector("[data-km-pstack-current]");
    var busy = false;
    var suppressClick = false;
    root.classList.add("is-ready");

    function place(card, p, animate) {
      var depth = Math.min(p, 3);
      var side = p % 2 ? 1 : -1;
      var spread = Math.min(16, deck.clientWidth * 0.035); // narrower fan on phones
      var x = depth * spread * side;
      var y = depth * 9;
      var rot = depth ? side * (2.5 + depth * 1.6) : 0;
      var scale = 1 - depth * 0.05;
      card.style.transition = animate && !reduce ? "transform .5s " + EASE + ", opacity .35s ease, box-shadow .35s ease" : "none";
      card.style.transform = "translate3d(" + x + "px," + y + "px,0) rotate(" + rot + "deg) scale(" + scale + ")";
      card.style.opacity = p > 3 ? "0" : "1";
      card.style.zIndex = String(n - p);
      card.classList.toggle("is-top", p === 0);
      card.setAttribute("tabindex", p === 0 ? "0" : "-1");
      card.setAttribute("aria-hidden", p === 0 ? "false" : "true");
    }
    function layout(animate) {
      order.forEach(function (index, p) { place(cards[index], p, animate); });
      if (current) current.textContent = String(order[0] + 1);
    }
    function top() { return cards[order[0]]; }
    function touched() { root.classList.add("is-touched"); }

    function next(dir) {
      if (busy || n < 2) return;
      busy = true; touched();
      var card = top();
      var w = deck.clientWidth;
      dir = dir || -1;
      card.style.transition = reduce ? "none" : "transform .32s ease-in, opacity .32s ease-in";
      card.style.transform = "translate3d(" + dir * w * 1.15 + "px,-20px,0) rotate(" + dir * 16 + "deg)";
      card.style.opacity = "0";
      window.setTimeout(function () {
        order.push(order.shift());
        card.style.transition = "none";
        layout(true);
        busy = false;
      }, reduce ? 0 : 230);
    }
    function prev() {
      if (busy || n < 2) return;
      busy = true; touched();
      var w = deck.clientWidth;
      order.unshift(order.pop());
      var card = top();
      card.style.transition = "none";
      card.style.transform = "translate3d(" + -w * 1.15 + "px,-20px,0) rotate(-16deg)";
      card.style.opacity = "0";
      card.style.zIndex = String(n + 1);
      void card.offsetWidth;
      layout(true);
      window.setTimeout(function () { busy = false; }, reduce ? 0 : 320);
    }

    /* drag / swipe */
    var drag = null;
    deck.addEventListener("pointerdown", function (e) {
      var card = e.target.closest("[data-km-pstack-card]");
      if (!card || card !== top() || busy || (e.pointerType === "mouse" && e.button !== 0)) return;
      drag = { x: e.clientX, y: e.clientY, t: performance.now(), id: e.pointerId, moving: false, dx: 0, dy: 0 };
    });
    deck.addEventListener("pointermove", function (e) {
      var card = top();
      if (drag && e.pointerId === drag.id) {
        drag.dx = e.clientX - drag.x; drag.dy = e.clientY - drag.y;
        if (!drag.moving) {
          if (Math.abs(drag.dy) > 10 && Math.abs(drag.dy) > Math.abs(drag.dx)) { drag = null; return; } // a page scroll
          if (Math.abs(drag.dx) < 6 || n < 2) return;
          drag.moving = true; touched();
          try { deck.setPointerCapture(e.pointerId); } catch (err) {}
          card.classList.add("is-dragging");
        }
        e.preventDefault();
        var w = deck.clientWidth;
        var k = Math.min(1, Math.abs(drag.dx) / (w * 0.5));
        card.style.transition = "none";
        card.style.transform = "translate3d(" + drag.dx + "px," + drag.dy * 0.25 + "px,0) rotate(" + drag.dx * 0.045 + "deg)";
        var under = cards[order[1]];
        if (under) {
          under.style.transition = "none";
          under.style.transform = "translate3d(" + 16 * (1 - k) + "px," + 9 * (1 - k) + "px,0) rotate(" + 4.1 * (1 - k) + "deg) scale(" + (0.95 + 0.05 * k) + ")";
        }
        return;
      }
      if (finePointer && !busy && e.pointerType === "mouse" && e.target.closest(".km-pstack__card") === card) {
        var r = card.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width - 0.5, py = (e.clientY - r.top) / r.height - 0.5;
        card.style.transition = "transform .12s linear";
        card.style.transform = "perspective(900px) rotateY(" + px * 9 + "deg) rotateX(" + -py * 7 + "deg) scale(1.015)";
        card.style.setProperty("--gx", (px + 0.5) * 100 + "%");
        card.style.setProperty("--gy", (py + 0.5) * 100 + "%");
        card.classList.add("is-tilting");
      }
    });
    function endDrag(e) {
      if (!drag || (e && e.pointerId !== drag.id)) return;
      var d = drag; drag = null;
      var card = top();
      card.classList.remove("is-dragging");
      if (!d.moving) return;
      suppressClick = true;
      window.setTimeout(function () { suppressClick = false; }, 60);
      var v = d.dx / Math.max(1, performance.now() - d.t);
      if (Math.abs(d.dx) > deck.clientWidth * 0.22 || Math.abs(v) > 0.55) next(d.dx > 0 ? 1 : -1);
      else layout(true);
    }
    deck.addEventListener("pointerup", endDrag);
    deck.addEventListener("pointercancel", endDrag);
    deck.addEventListener("pointerleave", function (e) {
      var card = top();
      if (card.classList.contains("is-tilting") && !drag) { card.classList.remove("is-tilting"); layout(true); }
    });
    deck.addEventListener("click", function (e) {
      var card = e.target.closest("[data-km-pstack-card]");
      if (!card) return;
      e.preventDefault();
      if (suppressClick || busy) return;
      if (card !== top()) return;
      viewer.open(Number(card.dataset.index));
    });
    deck.addEventListener("dragstart", function (e) { e.preventDefault(); });

    var prevBtn = root.querySelector("[data-km-pstack-prev]");
    var nextBtn = root.querySelector("[data-km-pstack-next]");
    if (prevBtn) prevBtn.addEventListener("click", prev);
    if (nextBtn) nextBtn.addEventListener("click", function () { next(-1); });
    root.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); next(-1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); prev(); }
      else if ((e.key === "Enter" || e.key === " ") && e.target === root) { e.preventDefault(); viewer.open(order[0]); }
    });

    var urls = cards.map(function (c) { return c.getAttribute("href"); });
    var alts = cards.map(function (c) { var img = c.querySelector("img"); return img ? img.alt : ""; });
    var viewer = makeViewer(root, urls, alts, function (i) {
      // keep the stack in step with what was viewed
      while (order[0] !== i) order.push(order.shift());
      layout(false);
    });

    layout(false);
    if (n > 1 && !reduce) {
      // a small "these are cards" nudge once the stack is on screen
      var io = "IntersectionObserver" in window ? new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) { root.classList.add("is-nudge"); io.disconnect(); }
      }, { threshold: 0.6 }) : null;
      if (io) io.observe(root);
    }
  }

  function makeViewer(root, urls, alts, onChange) {
    var dlg = null, img, counter, index = 0;
    function build() {
      dlg = document.createElement("dialog");
      dlg.className = "km-pview";
      dlg.setAttribute("aria-label", root.getAttribute("aria-label") || "");
      dlg.innerHTML =
        '<button type="button" class="km-pview__close" aria-label="' + (root.dataset.lClose || "Close") + '"><span class="material-symbols-rounded" aria-hidden="true">close</span></button>' +
        (urls.length > 1 ? '<button type="button" class="km-pview__nav km-pview__nav--prev" aria-label="' + (root.dataset.lPrev || "") + '"><span class="material-symbols-rounded" aria-hidden="true">arrow_back</span></button>' +
        '<button type="button" class="km-pview__nav km-pview__nav--next" aria-label="' + (root.dataset.lNext || "") + '"><span class="material-symbols-rounded" aria-hidden="true">arrow_forward</span></button>' : "") +
        '<figure class="km-pview__stage"><img class="km-pview__img" alt="" draggable="false"></figure>' +
        (urls.length > 1 ? '<span class="km-pview__count" aria-live="polite"></span>' : "");
      document.body.appendChild(dlg);
      img = dlg.querySelector(".km-pview__img");
      counter = dlg.querySelector(".km-pview__count");
      dlg.querySelector(".km-pview__close").addEventListener("click", function () { dlg.close(); });
      var p = dlg.querySelector(".km-pview__nav--prev"), nx = dlg.querySelector(".km-pview__nav--next");
      if (p) p.addEventListener("click", function () { show(index - 1, 1); });
      if (nx) nx.addEventListener("click", function () { show(index + 1, -1); });
      dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
      dlg.addEventListener("keydown", function (e) {
        if (e.key === "ArrowRight") show(index + 1, -1);
        else if (e.key === "ArrowLeft") show(index - 1, 1);
      });
      dlg.addEventListener("close", function () { document.documentElement.classList.remove("km-pview-open"); root.focus({ preventScroll: true }); });
      var sx = null;
      img.addEventListener("pointerdown", function (e) { sx = e.clientX; });
      img.addEventListener("pointerup", function (e) {
        if (sx === null) return;
        var dx = e.clientX - sx; sx = null;
        if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1), dx < 0 ? -1 : 1);
      });
    }
    function show(i, dir) {
      index = (i + urls.length) % urls.length;
      img.classList.remove("is-in-left", "is-in-right");
      void img.offsetWidth;
      if (dir && !reduce) img.classList.add(dir < 0 ? "is-in-right" : "is-in-left");
      img.src = urls[index];
      img.alt = alts[index] || "";
      if (counter) counter.textContent = (index + 1) + " / " + urls.length;
      var pre = new Image(); pre.src = urls[(index + 1) % urls.length];
      onChange(index);
    }
    return {
      open: function (i) {
        if (!dlg) build();
        show(i, 0);
        document.documentElement.classList.add("km-pview-open");
        if (typeof dlg.showModal === "function") dlg.showModal(); else dlg.setAttribute("open", "");
      }
    };
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-km-pstack]"), mount);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
