/* Specialist form · visual layer.
 * 1. Single-choice fields → styled dropdown (bottom sheet on phones).
 *    The native select stays in the form as the source of truth: picking an
 *    option sets select.value and fires input/change, so existing scripts
 *    (visit area, locations) keep working.
 * 2. Document upload → drop zone with file previews.
 */
(function () {
  "use strict";

  var form = document.querySelector(".km-specialist-owner-form");
  if (!form) return;

  var LANG = (document.documentElement.lang || "az").slice(0, 2);
  var messages = {
    az: {select: "Seçin", search: "Axtar…", none: "Heç nə tapılmadı", drop: "Faylları bura sürükləyin", or: "və ya", pick: "kompüterdən seçin", hint: "PDF, JPG, PNG · 10 MB-a qədər", close: "Bağla"},
    ru: {select: "Выберите вариант", search: "Поиск…", none: "Ничего не найдено", drop: "Перетащите файлы сюда", or: "или", pick: "выберите на устройстве", hint: "PDF, JPG, PNG · до 10 МБ", close: "Закрыть"},
    en: {select: "Select an option", search: "Search…", none: "Nothing found", drop: "Drag files here", or: "or", pick: "choose from device", hint: "PDF, JPG, PNG · up to 10 MB", close: "Close"},
  };
  var T = messages[LANG] || messages.az;

  var phone = window.matchMedia("(max-width: 640px)");
  var uid = 0;

  /* ── 1. Dropdowns ────────────────────────────────────────────────── */
  var openMenu = null;

  function enhanceSelect(select) {
    if (select.dataset.kmfxSelect || select.multiple || select.size > 1) return;
    if (select.parentElement.closest(".km-custom-select, .km-tree-select, [data-kmfx-skip]")) return;
    select.dataset.kmfxSelect = "1";
    var id = "kmfx-sel-" + (++uid);

    var wrap = document.createElement("div");
    wrap.className = "kmfx-select";
    select.parentNode.insertBefore(wrap, select);
    wrap.appendChild(select);
    select.classList.add("kmfx-select__native");
    select.tabIndex = -1;
    select.setAttribute("aria-hidden", "true");

    var button = document.createElement("button");
    button.type = "button";
    button.className = "kmfx-select__button";
    button.setAttribute("aria-haspopup", "listbox");
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", id);
    var labelEl = select.labels[0];
    button.id = id + "-button";
    if (labelEl) {
      if (!labelEl.id) labelEl.id = id + "-label";
      button.setAttribute("aria-labelledby", labelEl.id + " " + id + "-value");
      labelEl.addEventListener("click", function (event) {
        if (wrap.contains(event.target)) return;
        event.preventDefault();
        button.focus();
        button.click();
      });
    }
    button.innerHTML = '<span class="kmfx-select__value" id="' + id + '-value"></span><span class="kmfx-select__chevron" aria-hidden="true"></span>';
    wrap.appendChild(button);

    var menu = document.createElement("div");
    menu.className = "kmfx-select__menu";
    menu.hidden = true;
    menu.innerHTML =
      '<div class="kmfx-select__sheet-head"><strong></strong><button type="button" class="kmfx-select__close">×</button></div>' +
      '<div class="kmfx-select__search" hidden><input type="search" autocomplete="off" spellcheck="false"></div>' +
      '<ul class="kmfx-select__list" role="listbox" id="' + id + '" tabindex="-1"></ul>' +
      '<p class="kmfx-select__empty" hidden></p>';
    wrap.appendChild(menu);
    var list = menu.querySelector("ul");
    var searchBox = menu.querySelector(".kmfx-select__search");
    var search = searchBox.querySelector("input");
    search.placeholder = T.search;
    search.setAttribute("aria-label", T.search);
    var emptyNote = menu.querySelector(".kmfx-select__empty");
    emptyNote.textContent = T.none;
    var valueEl = button.querySelector(".kmfx-select__value");
    var closeButton = menu.querySelector(".kmfx-select__close");
    closeButton.setAttribute("aria-label", T.close);
    var title = menu.querySelector(".kmfx-select__sheet-head strong");
    title.id = id + "-title";
    title.textContent = T.select;
    if (labelEl) {
      var labelCopy = labelEl.cloneNode(true);
      labelCopy.querySelectorAll('[aria-hidden="true"]').forEach(function (icon) { icon.remove(); });
      title.textContent = labelCopy.textContent.trim();
    }
    if (labelEl) list.setAttribute("aria-labelledby", labelEl.id);
    if (typeof menu.showPopover === "function") menu.setAttribute("popover", "manual");

    function options() { return Array.prototype.slice.call(select.options); }
    function optionText(option) {
      var text = option && option.textContent.trim();
      return text && !/^-+$/.test(text) ? text : T.select;
    }
    function syncButton() {
      var opt = select.options[select.selectedIndex];
      valueEl.textContent = optionText(opt);
      wrap.classList.toggle("is-placeholder", !opt || opt.value === "");
      button.disabled = select.disabled;
      wrap.classList.toggle("is-disabled", select.disabled);
      wrap.classList.toggle("is-invalid", select.getAttribute("aria-invalid") === "true");
      ["aria-invalid", "aria-describedby"].forEach(function (name) {
        if (select.hasAttribute(name)) button.setAttribute(name, select.getAttribute(name));
        else button.removeAttribute(name);
      });
    }
    function build() {
      list.replaceChildren();
      options().forEach(function (opt, index) {
        if (opt.hidden) return;
        var li = document.createElement("li");
        li.setAttribute("role", "option");
        li.id = id + "-o" + index;
        li.className = "kmfx-select__option";
        li.dataset.index = String(index);
        li.textContent = optionText(opt);
        if (opt.value === "") li.classList.add("is-placeholder");
        if (opt.disabled) li.setAttribute("aria-disabled", "true");
        li.setAttribute("aria-selected", String(index === select.selectedIndex));
        list.appendChild(li);
      });
      searchBox.hidden = list.children.length <= 8;
    }
    function visibleItems() {
      return Array.prototype.filter.call(list.children, function (li) { return !li.hidden && li.getAttribute("aria-disabled") !== "true"; });
    }
    function setActive(li) {
      list.querySelectorAll(".is-active").forEach(function (x) { x.classList.remove("is-active"); });
      if (!li) { list.removeAttribute("aria-activedescendant"); return; }
      li.classList.add("is-active");
      list.setAttribute("aria-activedescendant", li.id);
      var offset = li.getBoundingClientRect().top - list.getBoundingClientRect().top;
      if (offset < 0) list.scrollTop += offset;
      else if (offset + li.offsetHeight > list.clientHeight) list.scrollTop += offset + li.offsetHeight - list.clientHeight;
    }
    function filter() {
      var q = search.value.trim().toLocaleLowerCase();
      var shown = 0;
      Array.prototype.forEach.call(list.children, function (li) {
        var match = !q || li.textContent.toLocaleLowerCase().indexOf(q) !== -1;
        li.hidden = !match;
        if (match) shown++;
      });
      emptyNote.hidden = shown > 0;
      setActive(visibleItems()[0] || null);
    }
    function position() {
      if (!menu.hasAttribute("popover") || phone.matches) return;
      var box = button.getBoundingClientRect();
      var below = window.innerHeight - box.bottom - 12;
      var above = box.top - 12;
      var up = below < Math.min(menu.scrollHeight, 320) && above > below;
      menu.style.setProperty("--km-menu-x", box.left + "px");
      menu.style.setProperty("--km-menu-width", box.width + "px");
      menu.style.setProperty("--km-menu-top", up ? "auto" : (box.bottom + 5) + "px");
      menu.style.setProperty("--km-menu-bottom", up ? (window.innerHeight - box.top + 5) + "px" : "auto");
      menu.style.setProperty("--km-menu-height", Math.max(0, Math.min(320, up ? above : below)) + "px");
    }
    function open() {
      if (select.matches(":disabled") || openMenu === api) return;
      if (openMenu && openMenu !== api) openMenu.close(false);
      build();
      search.value = "";
      filter();
      menu.hidden = false;
      wrap.classList.add("is-open");
      button.setAttribute("aria-expanded", "true");
      var sheet = phone.matches;
      wrap.classList.toggle("is-sheet", sheet);
      if (sheet) {
        document.documentElement.classList.add("kmfx-sheet-lock");
        menu.setAttribute("role", "dialog");
        menu.setAttribute("aria-modal", "true");
        menu.setAttribute("aria-labelledby", title.id);
      }
      else if (!menu.hasAttribute("popover")) {
        // Open upwards when there is no room below.
        var box = button.getBoundingClientRect();
        wrap.classList.toggle("is-up", window.innerHeight - box.bottom < 300 && box.top > 300);
      }
      if (menu.hasAttribute("popover")) menu.showPopover();
      position();
      var current = list.querySelector('[aria-selected="true"]');
      setActive(current || visibleItems()[0] || null);
      openMenu = api;
      if (!searchBox.hidden && !sheet) search.focus({preventScroll: true});
      else list.focus({preventScroll: true});
    }
    function close(returnFocus) {
      if (menu.hidden) return;
      button.setAttribute("aria-expanded", "false");
      document.documentElement.classList.remove("kmfx-sheet-lock");
      if (menu.hasAttribute("popover")) menu.hidePopover();
      menu.hidden = true;
      menu.removeAttribute("role");
      menu.removeAttribute("aria-modal");
      menu.removeAttribute("aria-labelledby");
      wrap.classList.remove("is-open", "is-sheet", "is-up");
      if (openMenu === api) openMenu = null;
      if (returnFocus !== false) button.focus({preventScroll: true});
    }
    function choose(li) {
      if (!li || li.getAttribute("aria-disabled") === "true") return;
      var index = Number(li.dataset.index);
      if (select.selectedIndex !== index) {
        select.selectedIndex = index;
        select.dispatchEvent(new Event("input", {bubbles: true}));
        select.dispatchEvent(new Event("change", {bubbles: true}));
      }
      syncButton();
      wrap.classList.remove("is-picked"); void wrap.offsetWidth; wrap.classList.add("is-picked");
      close();
    }
    function move(step) {
      var items = visibleItems();
      if (!items.length) return;
      var current = items.indexOf(list.querySelector(".is-active"));
      var next = current === -1 ? 0 : Math.max(0, Math.min(items.length - 1, current + step));
      setActive(items[next]);
    }
    function keys(event) {
      if (event.key === "ArrowDown") { event.preventDefault(); move(1); }
      else if (event.key === "ArrowUp") { event.preventDefault(); move(-1); }
      else if (event.key === "Home" && event.target !== search) { event.preventDefault(); setActive(visibleItems()[0]); }
      else if (event.key === "End" && event.target !== search) { event.preventDefault(); var v = visibleItems(); setActive(v[v.length - 1]); }
      else if (event.key === "Enter" || (event.key === " " && event.target !== search)) { event.preventDefault(); choose(list.querySelector(".is-active")); }
      else if (event.key === "Escape") { event.preventDefault(); close(); }
      else if (event.key === "Tab") {
        if (wrap.classList.contains("is-sheet")) {
          event.preventDefault();
          var targets = searchBox.hidden ? [closeButton, list] : [closeButton, search, list];
          var next = targets.indexOf(document.activeElement) + (event.shiftKey ? -1 : 1);
          targets[(next + targets.length) % targets.length].focus();
        } else close();
      }
      else if (event.target !== search && event.key.length === 1 && !event.ctrlKey && !event.metaKey) {
        var ch = event.key.toLocaleLowerCase();
        var hit = visibleItems().find(function (li) { return li.textContent.trim().toLocaleLowerCase().indexOf(ch) === 0; });
        if (hit) setActive(hit);
      }
    }

    button.addEventListener("click", function () { if (menu.hidden) open(); else close(); });
    button.addEventListener("keydown", function (event) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].indexOf(event.key) !== -1) { event.preventDefault(); open(); }
    });
    list.addEventListener("keydown", keys);
    search.addEventListener("keydown", keys);
    search.addEventListener("input", filter);
    closeButton.addEventListener("click", function () { close(); });
    closeButton.addEventListener("keydown", function (event) {
      if (event.key === "Tab" || event.key === "Escape") keys(event);
    });
    list.addEventListener("click", function (event) { choose(event.target.closest(".kmfx-select__option")); });
    list.addEventListener("pointermove", function (event) {
      var li = event.target.closest(".kmfx-select__option");
      if (li && !li.classList.contains("is-active")) setActive(li);
    });
    menu.addEventListener("click", function (event) { if (event.target === menu) close(); }); // sheet backdrop
    select.addEventListener("change", syncButton);
    select.addEventListener("focus", function () { button.focus(); });
    select.addEventListener("kmfx:sync", syncButton);
    form.addEventListener("reset", function () { window.setTimeout(syncButton, 0); });
    window.addEventListener("pageshow", syncButton);
    // Other scripts refill options (region → districts) or toggle disabled.
    new MutationObserver(function () { syncButton(); if (!menu.hidden) { build(); filter(); position(); } })
      .observe(select, {childList: true, subtree: true, attributes: true, attributeFilter: ["disabled", "hidden", "aria-invalid", "aria-describedby", "selected"]});
    wrap.addEventListener("animationend", function () { wrap.classList.remove("is-picked"); });

    var api = {close: close, wrap: wrap, position: position};
    syncButton();
  }

  document.addEventListener("pointerdown", function (event) {
    if (openMenu && !openMenu.wrap.contains(event.target)) openMenu.close(false);
  }, true);
  // Programmatic value changes (no event) are caught on the next form change.
  function syncFields() {
    form.querySelectorAll("select[data-kmfx-select]").forEach(function (s) { s.dispatchEvent(new Event("kmfx:sync")); });
  }
  form.addEventListener("change", syncFields);
  form.addEventListener("input", function (event) {
    if (event.target === form) syncFields();
  });

  window.addEventListener("scroll", function (event) {
    if (openMenu && !openMenu.wrap.contains(event.target instanceof Node ? event.target : null)) openMenu.position();
  }, true);
  window.addEventListener("resize", function () {
    if (!openMenu) return;
    if (phone.matches !== openMenu.wrap.classList.contains("is-sheet")) openMenu.close();
    else openMenu.position();
  });
  form.querySelectorAll("select").forEach(enhanceSelect);
  var addedFields = new MutationObserver(function (changes) {
    changes.forEach(function (change) {
      change.addedNodes.forEach(function (node) {
        if (node.nodeType !== 1) return;
        node.querySelectorAll("select").forEach(enhanceSelect);
      });
    });
  });
  form.querySelectorAll("[data-qual-rows], [data-practice-rows]").forEach(function (rows) {
    addedFields.observe(rows, {childList: true});
  });

  /* ── 2. Document drop zone with previews ─────────────────────────── */
  form.querySelectorAll("[data-specialist-documents]").forEach(function (widget) {
    var input = widget.querySelector('input[type="file"]');
    var files = widget.querySelector("[data-document-files]");
    if (!input || !files || widget.dataset.kmfxDrop) return;
    widget.dataset.kmfxDrop = "1";
    widget.classList.add("kmfx-docs");

    var zone = document.createElement("div");
    zone.className = "kmfx-drop";
    zone.innerHTML =
      '<span class="kmfx-drop__icon" aria-hidden="true">cloud_upload</span>' +
      '<span class="kmfx-drop__title"></span>' +
      '<span class="kmfx-drop__sub"><span></span> <u></u></span>' +
      '<span class="kmfx-drop__hint"></span>';
    zone.querySelector(".kmfx-drop__title").textContent = T.drop;
    zone.querySelector(".kmfx-drop__sub span").textContent = T.or;
    zone.querySelector(".kmfx-drop__sub u").textContent = T.pick;
    zone.querySelector(".kmfx-drop__hint").textContent = T.hint;
    input.parentNode.insertBefore(zone, input);
    zone.appendChild(input); // the transparent input covers the zone: click and drop both work
    var hint = widget.querySelector(":scope > small");
    if (hint) hint.hidden = true;

    ["dragenter", "dragover"].forEach(function (type) {
      zone.addEventListener(type, function () { zone.classList.add("is-over"); });
    });
    ["dragleave", "drop"].forEach(function (type) {
      zone.addEventListener(type, function () { zone.classList.remove("is-over"); });
    });

    var urls = new Map(); // file key → object URL, released when the file leaves the list
    function formatSize(bytes) {
      if (bytes < 1024 * 1024) return Math.max(1, Math.round(bytes / 1024)) + " KB";
      return (bytes / 1024 / 1024).toFixed(1).replace(".0", "") + " MB";
    }
    function decorate() {
      var picked = Array.prototype.slice.call(input.files || []);
      var keep = new Set(picked.map(function (f) { return f.name + "|" + f.size + "|" + f.lastModified; }));
      urls.forEach(function (u, key) { if (!keep.has(key)) { URL.revokeObjectURL(u); urls.delete(key); } });
      Array.prototype.forEach.call(files.children, function (li, index) {
        var file = picked[index];
        if (!file || li.dataset.kmfxDecorated === file.name + file.size) return;
        li.dataset.kmfxDecorated = file.name + file.size;
        li.classList.add("kmfx-doc");
        var thumb = document.createElement("span");
        thumb.className = "kmfx-doc__thumb";
        thumb.setAttribute("aria-hidden", "true");
        if (/^image\//.test(file.type)) {
          var key = file.name + "|" + file.size + "|" + file.lastModified;
          var url = urls.get(key) || URL.createObjectURL(file);
          urls.set(key, url);
          var img = document.createElement("img");
          img.src = url; img.alt = "";
          thumb.appendChild(img);
        } else {
          thumb.classList.add("is-pdf");
          thumb.textContent = "picture_as_pdf";
        }
        var name = li.querySelector("span");
        var meta = document.createElement("small");
        meta.className = "kmfx-doc__meta";
        meta.textContent = formatSize(file.size);
        var body = document.createElement("span");
        body.className = "kmfx-doc__body";
        li.insertBefore(thumb, li.firstChild);
        li.insertBefore(body, thumb.nextSibling);
        if (name) body.appendChild(name);
        body.appendChild(meta);
        var remove = li.querySelector("button");
        if (remove) {
          remove.classList.add("kmfx-doc__remove");
          remove.innerHTML = '<span aria-hidden="true">delete</span>';
        }
      });
    }
    new MutationObserver(decorate).observe(files, {childList: true});
    decorate();
  });
})();
