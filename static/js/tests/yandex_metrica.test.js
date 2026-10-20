"use strict";
const assert = require("node:assert/strict");
const test = require("node:test");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

function fixture({ id = "12345678", preview = false, webvisor = "true", search = "?q=private&email=x%40test.test&utm_source=telegram#secret" } = {}) {
  const events = [], scripts = [], classes = new Set(), fieldClasses = new Set();
  const fields = [{ classList: { add: (value) => fieldClasses.add(value), contains: value => fieldClasses.has(value) } }];
  const form = { classList: { add: (value) => classes.add(value), contains: value => classes.has(value) } };
  const config = { dataset: { counterId: id, webvisor } };
  const document = {
    readyState: "complete", referrer: "https://example.com/article?email=private#secret", title: "private search",
    body: { hasAttribute: () => preview }, documentElement: {},
    getElementById: () => config,
    querySelectorAll: (selector) => selector.includes("input") ? fields : [form],
    createElement: () => ({}),
    head: { appendChild: (script) => { assert.ok(classes.has("ym-hide-content")); assert.ok(fieldClasses.has("ym-disable-keys")); scripts.push(script); } },
  };
  const window = {
    document, location: { href: "https://kidsmap.az/ru/catalog/" + search },
    ym: (...args) => events.push(args),
    MutationObserver: class { constructor(callback) { this.callback = callback; window.observer = this; } observe() {} },
  };
  const context = vm.createContext({ window, document, URL, Date, Number });
  function run() { vm.runInContext(fs.readFileSync(path.join(__dirname, "../yandex_metrica.js"), "utf8"), context); }
  return { window, document, events, scripts, classes, fieldClasses, run };
}

test("one init and clean page hit; masks exist before loading; no automatic params", () => {
  const f = fixture(); f.run(); f.run();
  assert.equal(f.scripts.length, 1);
  assert.equal(f.scripts[0].src, "https://mc.yandex.ru/metrika/tag.js");
  assert.equal(f.scripts[0].referrerPolicy, "no-referrer");
  assert.equal(f.events.length, 2);
  assert.equal(f.events[0][1], "init");
  assert.equal(f.events[0][2].defer, true);
  assert.equal(f.events[0][2].trackLinks, false);
  assert.equal(f.events[0][2].sendTitle, false);
  assert.equal(f.events[0][2].webvisor, false, "free text query disables replay");
  assert.equal(f.events[1][2], "https://kidsmap.az/ru/catalog/?utm_source=telegram");
  assert.equal(f.events[1][3].referer, "https://example.com/article");
  assert.equal(f.events[1][3].title, "KidsMap");
  assert.ok(!JSON.stringify(f.events).includes("private"));
});

test("only two contact goals; no arbitrary payload or GA dependency", () => {
  const f = fixture({ search: "" }); f.run();
  ["phone_click", "whatsapp_click", "cta_call", "purchase", "__proto__", "constructor"].forEach(name => f.window.kidsMapTrackYandexMetricaEvent(name, { email: "private" }));
  const goals = f.events.filter(e => e[1] === "reachGoal");
  assert.deepEqual(goals.map(e => e.slice(1)), [["reachGoal", "phone_click"], ["reachGoal", "whatsapp_click"]]);
  assert.equal(f.events[0][2].webvisor, true);
});

test("preview and invalid IDs never load a tag", () => {
  for (const options of [{ preview: true }, { id: "" }, { id: "0" }, { id: "abc" }]) {
    const f = fixture(options); f.run(); assert.equal(f.scripts.length, 0); assert.equal(f.events.length, 0);
  }
});

test("queued ym works without installed tag, and dynamic fields are masked", () => {
  const f = fixture({ webvisor: "false", search: "?utm_campaign=launch" }); delete f.window.ym;
  f.document.referrer = "https://kidsmap.az/ru/account/?token=private";
  f.run();
  assert.equal(f.window.ym.a.length, 2);
  assert.equal(f.window.ym.a[1][3].referer, "");
  f.classes.clear(); f.fieldClasses.clear(); f.window.observer.callback([]);
  assert.ok(f.classes.has("ym-hide-content")); assert.ok(f.fieldClasses.has("ym-disable-keys"));
  assert.equal(f.window.ym.a[0][2].webvisor, false);
});

test("third-party tracker failure does not break contact actions", () => {
  const f = fixture(); f.run(); f.window.ym = () => { throw Error("blocked"); };
  assert.doesNotThrow(() => f.window.kidsMapTrackYandexMetricaEvent("phone_click"));
});

test("the actual shared emitter forwards once even when gtag is absent", () => {
  const source = fs.readFileSync(path.join(__dirname, "../../../src/catalog/templates/base.html"), "utf8");
  const emitter = source.match(/function emitAnalyticsEvent\(eventItem\) \{[\s\S]*?\n          \}/)[0];
  const f = fixture(); f.run();
  const context = vm.createContext({ window: f.window, sendGoogleAnalyticsEvent: () => {} });
  vm.runInContext(emitter + '; emitAnalyticsEvent({name:"phone_click",params:{email:"private"}});', context);
  assert.deepEqual(f.events.filter(e => e[1] === "reachGoal"), [[12345678, "reachGoal", "phone_click"]]);
});
