(function (window, document) {
  "use strict";
  var config = document.getElementById("kidsmap-yandex-metrica");
  if (!config || window.kidsMapYandexMetricaStarted) return;
  var id = config.dataset.counterId || "";
  if (!/^[1-9][0-9]*$/.test(id) || !Number.isSafeInteger(Number(id))) return;

  function start() {
    if (!document.body || document.body.hasAttribute("data-site-preview")) return;
    if (window.kidsMapYandexMetricaStarted) return;
    window.kidsMapYandexMetricaStarted = true;

    function maskInputs() {
      document.querySelectorAll("form, #reviews").forEach(function (element) {
        if (!element.classList.contains("ym-hide-content")) element.classList.add("ym-hide-content");
      });
      document.querySelectorAll("input, textarea, select, [contenteditable]").forEach(function (element) {
        if (!element.classList.contains("ym-disable-keys")) element.classList.add("ym-disable-keys");
      });
    }
    maskInputs();
    if (window.MutationObserver) {
      new window.MutationObserver(maskInputs).observe(document.documentElement, {
        childList: true, subtree: true, attributes: true, attributeFilter: ["contenteditable"],
      });
    }

    var current = new URL(window.location.href);
    var clean = new URL(current.origin + current.pathname);
    var marketingKeys = ["utm_source", "utm_medium", "utm_campaign"];
    var replaySafe = !current.hash;
    current.searchParams.forEach(function (value, key) {
      if (marketingKeys.indexOf(key) !== -1) clean.searchParams.set(key, value);
      else replaySafe = false;
    });
    var referrer = "";
    try {
      var previous = new URL(document.referrer);
      if (/^https?:$/.test(previous.protocol) && !/(?:^|\/)(?:account|accounts|admin|login|auth|owner|volunteer|dashboard)(?:\/|$)/i.test(previous.pathname)) {
        referrer = previous.origin + previous.pathname;
      }
    } catch (_) { /* Empty or invalid referrer. */ }

    window.ym = window.ym || function () {
      (window.ym.a = window.ym.a || []).push(arguments);
    };
    window.ym.l = window.ym.l || Date.now();
    var counterId = Number(id);
    window.ym(counterId, "init", {
      defer: true, clickmap: true, trackLinks: false, accurateTrackBounce: true,
      sendTitle: false, ecommerce: false, trackHash: false,
      url: clean.href, referrer: referrer,
      webvisor: config.dataset.webvisor === "true" && replaySafe,
    });
    // hit uses `referer` (one r); init uses `referrer` in the current tag API.
    window.ym(counterId, "hit", clean.href, { referer: referrer, title: "KidsMap" });
    window.kidsMapTrackYandexMetricaEvent = function (name) {
      if (name !== "phone_click" && name !== "whatsapp_click") return;
      try { window.ym(counterId, "reachGoal", name); } catch (_) { /* Analytics must not interrupt a contact action. */ }
    };
    var tag = document.createElement("script");
    tag.async = true;
    tag.referrerPolicy = "no-referrer";
    tag.src = "https://mc.yandex.ru/metrika/tag.js";
    document.head.appendChild(tag);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start, { once: true });
  else start();
})(window, document);
