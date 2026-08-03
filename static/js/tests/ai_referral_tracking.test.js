"use strict";

const assert = require("node:assert/strict");
const tracker = require("../ai_referral_tracking.js");


const knownReferrers = {
  "https://chatgpt.com/c/abc": "chatgpt",
  "https://chat.openai.com/c/legacy": "chatgpt",
  "https://www.perplexity.ai/search/test": "perplexity",
  "https://gemini.google.com/app/abc": "gemini",
  "https://copilot.microsoft.com/": "copilot",
  "https://claude.ai/chat/abc": "claude",
  "https://poe.com/SomeBot": "poe",
  "https://chat.deepseek.com/a/chat/s/abc": "deepseek",
  "https://grok.com/": "grok",
  "https://meta.ai/": "meta_ai",
  "https://chat.mistral.ai/chat/abc": "mistral",
  "https://www.phind.com/search/test": "phind",
  "https://you.com/search?q=test": "youcom",
};

Object.entries(knownReferrers).forEach(([referrer, expected]) => {
  assert.equal(
    tracker.detectAIReferral({
      referrer: referrer,
      currentHostname: "kidsmap.az",
      search: "",
    }),
    expected,
    referrer
  );
});

assert.equal(
  tracker.detectAIReferral({
    referrer: "https://kidsmap.az/ru/catalog/",
    currentHostname: "kidsmap.az",
    search: "?utm_source=chatgpt",
  }),
  "",
  "internal navigation must never become an AI referral"
);

assert.equal(
  tracker.detectAIReferral({
    referrer: "https://example.com/article",
    currentHostname: "kidsmap.az",
    search: "?utm_source=chatgpt",
  }),
  "",
  "an unknown external referrer must not fall back to UTM"
);

assert.equal(
  tracker.detectAIReferral({
    referrer: "",
    currentHostname: "kidsmap.az",
    search: "?utm_source=chatgpt&utm_campaign=private-value",
  }),
  "chatgpt",
  "UTM attribution is allowed only when referrer is absent"
);

assert.equal(
  tracker.detectAIReferral({
    referrer: "",
    currentHostname: "kidsmap.az",
    search: "",
  }),
  ""
);

const stored = new Map();
const emitted = [];
const browser = {
  document: {
    referrer: "https://chatgpt.com/c/abc",
    body: {
      dataset: {
        analyticsPageType: "catalog",
        pageLanguage: "ru",
      },
    },
  },
  location: {
    hostname: "kidsmap.az",
    pathname: "/ru/catalog/",
    search: "?email=must-not-leak@example.com",
  },
  sessionStorage: {
    getItem: (key) => stored.get(key) || null,
    setItem: (key, value) => stored.set(key, value),
  },
  kidsMapTrackEvent: (event) => emitted.push(event),
};

assert.equal(tracker.trackCurrentVisit(browser), true);
assert.deepEqual(emitted, [
  {
    event_type: "ai_referral_visit",
    ai_source: "chatgpt",
    landing_path: "/ru/catalog/",
    page_type: "catalog",
    language: "ru",
  },
]);
assert.equal(JSON.stringify(emitted).includes("must-not-leak"), false);
assert.equal(tracker.trackCurrentVisit(browser), false, "same landing must be emitted once");

console.log("AI referral tracking tests passed");
