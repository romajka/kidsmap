(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  if (!root || !root.document) return;
  root.kidsMapAIReferral = api;
  api.trackCurrentVisit(root);
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";

  const AI_DOMAINS = Object.freeze({
    "chatgpt.com": "chatgpt",
    "chat.openai.com": "chatgpt",
    "perplexity.ai": "perplexity",
    "gemini.google.com": "gemini",
    "copilot.microsoft.com": "copilot",
    "claude.ai": "claude",
    "poe.com": "poe",
    "chat.deepseek.com": "deepseek",
    "deepseek.com": "deepseek",
    "grok.com": "grok",
    "meta.ai": "meta_ai",
    "chat.mistral.ai": "mistral",
    "mistral.ai": "mistral",
    "phind.com": "phind",
    "you.com": "youcom",
  });

  const UTM_SOURCES = Object.freeze({
    chatgpt: "chatgpt",
    "chatgpt.com": "chatgpt",
    "chat.openai.com": "chatgpt",
    openai: "chatgpt",
    perplexity: "perplexity",
    "perplexity.ai": "perplexity",
    gemini: "gemini",
    google_gemini: "gemini",
    copilot: "copilot",
    microsoft_copilot: "copilot",
    claude: "claude",
    anthropic: "claude",
    poe: "poe",
    quora_poe: "poe",
    deepseek: "deepseek",
    grok: "grok",
    meta_ai: "meta_ai",
    mistral: "mistral",
    phind: "phind",
    youcom: "youcom",
    "you.com": "youcom",
  });

  function normalizedHostname(value) {
    return String(value || "").trim().toLowerCase().replace(/^www\./, "");
  }

  function isInternalHostname(hostname, currentHostname) {
    const normalized = normalizedHostname(hostname);
    const current = normalizedHostname(currentHostname);
    return Boolean(normalized) && (
      normalized === current ||
      normalized === "kidsmap.az" ||
      normalized.endsWith(".kidsmap.az")
    );
  }

  function sourceForHostname(hostname) {
    const normalized = normalizedHostname(hostname);
    for (const domain of Object.keys(AI_DOMAINS)) {
      if (normalized === domain || normalized.endsWith("." + domain)) {
        return AI_DOMAINS[domain];
      }
    }
    return "";
  }

  function sourceFromUtm(search) {
    let value = "";
    try {
      value = new URLSearchParams(String(search || "")).get("utm_source") || "";
    } catch (err) {
      return "";
    }
    return UTM_SOURCES[value.trim().toLowerCase()] || "";
  }

  function detectAIReferral(options) {
    const referrer = String(options && options.referrer || "").trim();
    const currentHostname = String(options && options.currentHostname || "");
    if (referrer) {
      try {
        const hostname = new URL(referrer).hostname;
        if (isInternalHostname(hostname, currentHostname)) return "";
        return sourceForHostname(hostname);
      } catch (err) {
        return "";
      }
    }
    return sourceFromUtm(options && options.search || "");
  }

  function trackCurrentVisit(browser) {
    const body = browser.document.body;
    const pageType = body && body.dataset.analyticsPageType || "";
    const language = body && body.dataset.pageLanguage || "";
    if (!pageType || !language || typeof browser.kidsMapTrackEvent !== "function") return false;

    const aiSource = detectAIReferral({
      referrer: browser.document.referrer,
      search: browser.location.search,
      currentHostname: browser.location.hostname,
    });
    if (!aiSource) return false;

    const landingPath = browser.location.pathname || "/";
    const storageKey = "kidsmap:ai-referral:" + aiSource + ":" + landingPath;
    try {
      if (browser.sessionStorage.getItem(storageKey)) return false;
      browser.sessionStorage.setItem(storageKey, "1");
    } catch (err) {}

    browser.kidsMapTrackEvent({
      event_type: "ai_referral_visit",
      ai_source: aiSource,
      landing_path: landingPath,
      page_type: pageType,
      language: language,
    });
    return true;
  }

  return {
    detectAIReferral: detectAIReferral,
    isInternalHostname: isInternalHostname,
    sourceForHostname: sourceForHostname,
    sourceFromUtm: sourceFromUtm,
    trackCurrentVisit: trackCurrentVisit,
  };
});
