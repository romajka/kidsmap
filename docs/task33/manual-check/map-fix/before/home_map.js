(function () {
  const DEFAULT_CENTER = { lat: 40.4093, lng: 49.8671 };
  const DEFAULT_ZOOM = 11;
  const BRAND_MARKER_COLOR = "#136f38";
  const BRAND_MARKER_INNER_COLOR = "#a8d59b";
  const SCRIPT_CONFIG = (function () {
    const scriptEl = document.currentScript;
    if (!scriptEl) return {};

    return {
      googleMapsApiKey: (scriptEl.dataset.homeMapGoogleKey || "").trim(),
      googleMapsMapId: (scriptEl.dataset.homeMapGoogleMapId || "").trim(),
      leafletCss: (scriptEl.dataset.homeMapLeafletCss || "").trim(),
      leafletCssIntegrity: (scriptEl.dataset.homeMapLeafletCssIntegrity || "").trim(),
      leafletJs: (scriptEl.dataset.homeMapLeafletJs || "").trim(),
      leafletJsIntegrity: (scriptEl.dataset.homeMapLeafletJsIntegrity || "").trim(),
      routeLabel: (scriptEl.dataset.homeMapRouteLabel || "Route").trim(),
      language: (scriptEl.dataset.homeMapLanguage || "az").trim(),
      unavailableLabel: (scriptEl.dataset.homeMapUnavailableLabel || "Map is temporarily unavailable.").trim(),
    };
  })();

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, function (char) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[char];
    });
  }

  function normalizeValue(value) {
    return String(value || "").trim();
  }

  function normalizeLocaleSearch(value) {
    const translitMap = {
      "ə": "e",
      "Ə": "e",
      "ı": "i",
      "I": "i",
      "İ": "i",
      "ö": "o",
      "Ö": "o",
      "ü": "u",
      "Ü": "u",
      "ş": "s",
      "Ş": "s",
      "ç": "c",
      "Ç": "c",
      "ğ": "g",
      "Ğ": "g"
    };

    return normalizeValue(value)
      .replace(/[ƏəIİıÖöÜüŞşÇçĞğ]/g, function (char) {
        return translitMap[char] || char;
      })
      .toLocaleLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "");
  }

  function normalizeSearch(value) {
    return normalizeLocaleSearch(value);
  }

  function getDistrictOptions(form) {
    const districtOptionsEl = form.querySelector("#home-district-options");
    if (!districtOptionsEl) return [];

    return Array.from(districtOptionsEl.querySelectorAll("option"))
      .map(function (option) {
        const displayLabel = normalizeValue(option.value);

        return {
          label: displayLabel,
          value: normalizeValue(option.dataset.value || option.value),
          searchTerms: normalizeSearch([
            option.value,
            option.dataset.value,
            option.dataset.labelCurrent,
            option.dataset.labelAz,
            option.dataset.labelRu,
            option.dataset.labelEn
          ].join(" "))
        };
      })
      .filter(function (option) {
        return option.value && option.label;
      });
  }

  function resolveDistrictValue(value, options) {
    const current = normalizeValue(value);
    if (!current) return null;

    const normalizedCurrent = normalizeSearch(current);
    const exactMatch = options.find(function (option) {
      return normalizeSearch(option.label) === normalizedCurrent || option.searchTerms.includes(normalizedCurrent);
    });
    if (exactMatch) return exactMatch;

    const prefixMatches = options.filter(function (option) {
      return normalizeSearch(option.label).startsWith(normalizedCurrent) || option.searchTerms.includes(normalizedCurrent);
    });
    if (prefixMatches.length === 1) {
      return prefixMatches[0];
    }

    return null;
  }

  function getAgeInput(form) {
    return form.querySelector('[name="age"]');
  }

  function getAgeButtons(form) {
    return Array.from(form.querySelectorAll("[data-home-age-chip]"));
  }

  function syncAgeButtons(form) {
    const ageInput = getAgeInput(form);
    if (!ageInput) return;

    const currentValue = normalizeValue(ageInput.value);
    getAgeButtons(form).forEach(function (button) {
      const isActive = normalizeValue(button.dataset.ageValue) === currentValue;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  function setAgeValue(form, nextValue) {
    const ageInput = getAgeInput(form);
    if (!ageInput) return;

    ageInput.value = nextValue;
    syncAgeButtons(form);
  }

  function parsePlaces() {
    const dataEl = document.getElementById("home-map-data");
    if (!dataEl) return [];

    try {
      return JSON.parse(dataEl.textContent || "[]");
    } catch (_error) {
      return [];
    }
  }

  function getFilterState() {
    const form = document.querySelector("[data-home-map-filter-form]");
    if (!form) {
      return {
        query: "",
        category: "",
        district: "",
        metro: "",
        age: "",
      };
    }

    return {
      query: normalizeSearch(form.querySelector('[name="q"]')?.value),
      category: normalizeValue(form.querySelector('[name="category"]')?.value),
      district: normalizeValue(form.querySelector('[name="district"]')?.value),
      metro: normalizeValue(form.querySelector('[name="metro"]')?.value),
      age: normalizeValue(form.querySelector('[name="age"]')?.value),
    };
  }

  function isPlaceInBaku(place) {
    // The payload supplies a canonical location key; addresses and map bounds
    // are not evidence of a district (e.g. Sumgait also lies in the old bbox).
    const district = normalizeValue(place && place.district).toLowerCase();
    return district === "baku" || district.startsWith("baku_");
  }

  function pointMembers(point) {
    return Array.isArray(point.members) ? point.members : [point];
  }

  function businessCount(points) {
    return points.reduce((count, point) => count + pointMembers(point).length, 0);
  }

  async function fetchFilteredPoints(signal) {
    const form = document.querySelector("[data-home-map-filter-form]");
    const mapEl = document.getElementById("home-map");
    const params = new URLSearchParams(form ? new FormData(form) : undefined);
    const response = await fetch(mapEl.dataset.mapEndpoint + "?" + params.toString(), {
      signal: signal, credentials: "same-origin", headers: {Accept: "application/json"},
    });
    if (!response.ok) throw new Error("Map filter request failed");
    const payload = await response.json();
    return payload.points.filter(hasValidCoordinates);
  }

  function serverFilterUpdater(apply, closePopup, onError) {
    let controller = null;
    let generation = 0;
    return async function () {
      const current = ++generation;
      if (controller) controller.abort();
      controller = new AbortController();
      closePopup();
      apply([]);
      try {
        const points = await fetchFilteredPoints(controller.signal);
        if (current === generation) apply(points);
      } catch (error) {
        if (current !== generation || error.name === "AbortError") return;
        apply([]);
        onError();
      }
    };
  }

  function interpolateAgeLabel(template, from, to) {
    return String(template || "")
      .replaceAll("{from}", String(from === null || from === undefined ? "" : from))
      .replaceAll("{to}", String(to === null || to === undefined ? "" : to));
  }

  function formatAgeBadge(place, labels) {
    const from = place.age_from;
    const to = place.age_to;
    if (from !== null && from !== undefined && to !== null && to !== undefined) {
      return interpolateAgeLabel(labels.range, from, to);
    } else if (from !== null && from !== undefined) {
      return interpolateAgeLabel(labels.from, from, to);
    } else if (to !== null && to !== undefined) {
      return interpolateAgeLabel(labels.to, from, to);
    }
    return "";
  }

  function renderPopupContent(point, detailsLabel, ageLabels) {
    return '<div class="home-map-popup-members" style="max-height: min(60vh, 480px); overflow-y: auto">' +
      pointMembers(point).map(place => renderMemberPopup(place, detailsLabel, ageLabels)).join("") + "</div>";
  }

  function renderMemberPopup(place, detailsLabel, ageLabels) {
    const ageBadgeText = place.age || "";
    const priceBadgeText = place.price || "";
    const categoryName = place.category || "";
    const categoryColor = place.category_color_text || "var(--brand-turf)";

    const imageHtml = place.image_url
      ? '<a class="home-map-popup-thumb-link" href="' +
      escapeHtml(place.url || "") +
      '">' +
      '<img class="home-map-popup-thumb-blur" src="' +
      escapeHtml(place.image_url) +
      '" alt="" aria-hidden="true" />' +
      '<img class="home-map-popup-thumb" src="' +
      escapeHtml(place.image_url) +
      '" alt="' +
      escapeHtml(place.name || "") +
      '" loading="lazy" decoding="async" />' +
      (priceBadgeText ? '<span class="home-map-popup-price">' + escapeHtml(priceBadgeText) + "</span>" : "") +
      '<div class="home-map-popup-badges">' +
      (categoryName
        ? '<span class="home-map-popup-badge-cat" style="color: ' +
        escapeHtml(categoryColor) +
        ';">' +
        escapeHtml(categoryName) +
        "</span>"
        : "") +
      (ageBadgeText ? '<span class="home-map-popup-badge-age">' + escapeHtml(ageBadgeText) + "</span>" : "") +
      "</div>" +
      "</a>"
      : '<div class="home-map-popup-no-thumb-header">' +
      '<div class="home-map-popup-badges home-map-popup-badges-standalone">' +
      (categoryName
        ? '<span class="home-map-popup-badge-cat" style="color: ' +
        escapeHtml(categoryColor) +
        ';">' +
        escapeHtml(categoryName) +
        "</span>"
        : "") +
      (ageBadgeText ? '<span class="home-map-popup-badge-age">' + escapeHtml(ageBadgeText) + "</span>" : "") +
      "</div>" +
      "</div>";

    const displayAddress = place.address || place.district_label || place.district || "";
    const addressHtml = displayAddress
      ? '<div class="home-map-popup-info-row">' +
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="popup-info-icon"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>' +
      '<span class="home-map-popup-info-text">' +
      escapeHtml(displayAddress) +
      "</span>" +
      "</div>"
      : "";

    const scheduleHtml = place.schedule
      ? '<div class="home-map-popup-info-row">' +
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="popup-info-icon"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>' +
      '<span class="home-map-popup-info-text">' +
      escapeHtml(place.schedule) +
      "</span>" +
      "</div>"
      : "";

    const phoneHtml = place.has_phone ? window.kidsMapPhoneButton(place.id, "home-map-popup-phone-link") : "";

    return (
      '<div class="home-map-popup">' +
      imageHtml +
      '<div class="home-map-popup-body">' +
      '<a href="' +
      escapeHtml(place.url || "") +
      '" class="home-map-popup-title-link">' +
      '<strong class="home-map-popup-title" lang="' + escapeHtml(place.content_language || '') + '">' +
      escapeHtml(place.name) +
      "</strong>" +
      "</a>" +
      (place.translation_fallback ? '<p class="meta" data-translation-fallback>' + escapeHtml(place.translation_label || 'AZ') + '</p>' : '') +
      '<div class="home-map-popup-details">' +
      addressHtml +
      (place.matched_offers || []).map(offer => '<a class="home-map-popup-info-row" href="' + escapeHtml(offer.url) + '">' + escapeHtml(offer.name) + '</a>' + (offer.groups || []).map(group => '<div class="home-map-popup-info-row">' + escapeHtml(group.name) + '</div>').join("")).join("") +
      scheduleHtml +
      (Number.isFinite(place.lat) && Number.isFinite(place.lng) ? '<a class="home-map-popup-info-row" target="_blank" rel="noopener noreferrer" href="https://www.google.com/maps/dir/?api=1&amp;destination=' + encodeURIComponent(place.lat + ',' + place.lng) + '">' + escapeHtml(SCRIPT_CONFIG.routeLabel || "Route") + '</a>' : "") +
      phoneHtml +
      "</div>" +
      '<a class="home-map-popup-link-btn" href="' +
      escapeHtml(place.url || "") +
      '">' +
      escapeHtml(detailsLabel) +
      ' <span class="arrow">→</span>' +
      "</a>" +
      "</div>" +
      "</div>"
    );
  }

  const CATEGORY_SVGS = {
    CAMP: '<path d="M19 21 10 4 1 21"></path><path d="M1 21h22"></path><path d="m14 21-4-8-4 8"></path>',
    camp: '<path d="M19 21 10 4 1 21"></path><path d="M1 21h22"></path><path d="m14 21-4-8-4 8"></path>',
    SPRT: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7c0 6 4 9 6 9s6-3 6-9V2Z"></path>',
    sprt: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7c0 6 4 9 6 9s6-3 6-9V2Z"></path>',
    MUS: '<path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle>',
    mus: '<path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle>',
    TECH: '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>',
    tech: '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>',
    EDU: '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>',
    edu: '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>',
    ART: '<circle cx="13.5" cy="6.5" r=".5"></circle><circle cx="17.5" cy="10.5" r=".5"></circle><circle cx="8.5" cy="7.5" r=".5"></circle><circle cx="6.5" cy="12.5" r=".5"></circle><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"></path>',
    art: '<circle cx="13.5" cy="6.5" r=".5"></circle><circle cx="17.5" cy="10.5" r=".5"></circle><circle cx="8.5" cy="7.5" r=".5"></circle><circle cx="6.5" cy="12.5" r=".5"></circle><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"></path>',
    FUN: '<rect x="2" y="6" width="20" height="12" rx="2"></rect><path d="M6 12h4"></path><path d="M8 10v4"></path><circle cx="15" cy="13" r="1"></circle><circle cx="18" cy="11" r="1"></circle>',
    fun: '<rect x="2" y="6" width="20" height="12" rx="2"></rect><path d="M6 12h4"></path><path d="M8 10v4"></path><circle cx="15" cy="13" r="1"></circle><circle cx="18" cy="11" r="1"></circle>',
    'early-development': '<path d="M12 22V12"></path><path d="M12 12C12 12 10 6 5 6C5 6 4 10 12 12Z"></path><path d="M12 16C12 16 15 10 19 10C19 10 20 14 12 16Z"></path>',
    DANCE: '<circle cx="12" cy="4" r="2" /><path d="M6 10c2-3 4-4 6-4s4 1 6 4" /><path d="M12 8c-3 4-5 7-6 11h12c-1-4-3-7-6-11z" /><path d="M10 19v3" /><path d="M14 19v3" />',
    dance: '<circle cx="12" cy="4" r="2" /><path d="M6 10c2-3 4-4 6-4s4 1 6 4" /><path d="M12 8c-3 4-5 7-6 11h12c-1-4-3-7-6-11z" /><path d="M10 19v3" /><path d="M14 19v3" />',
    'intellect-skills': '<path d="M20 7H17.8486C17.3511 7 17 6.49751 17 6C17 4.34315 15.6569 3 14 3C12.3431 3 11 4.34315 11 6C11 6.49751 10.6488 7 10.1513 7H8C7.44771 7 7 7.44772 7 8V10.1513C7 10.6488 6.49751 11 6 11C4.34315 11 3 12.3431 3 14C3 15.6569 4.34315 17 6 17C6.49751 17 7 17.3511 7 17.8486V20C7 20.5523 7.44771 21 8 21L20 21C20.5523 21 21 20.5523 21 20V17.8486C21 17.3511 20.4975 17 20 17C18.3431 17 17 15.6569 17 14C17 12.3431 18.3431 11 20 11C20.4975 11 21 10.6488 21 10.1513L21 8C21 7.44772 20.5523 7 20 7Z"/>',
    'parks-playgrounds': '<path d="M10 22v-6.5M18 22v-5M10 15.5a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9Z" /><path d="M18 17a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7Z" />,',
    PARK: '<path d="M10 22v-6.5M18 22v-5M10 15.5a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9Z" /><path d="M18 17a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7Z" />',
    park: '<path d="M10 22v-6.5M18 22v-5M10 15.5a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9Z" /><path d="M18 17a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7Z" />',
    BEACH: '<path d="M4 11c1.8-3.7 5.1-6 8-6s6.2 2.3 8 6" /><path d="M12 5v14" /><path d="M8 11c.8-2.3 2.2-4.2 4-6 1.8 1.8 3.2 3.7 4 6" /><path d="M4 18c1.4-1 2.8-.5 4 0s2.6 1 4 0 2.8-1 4 0 2.6 1 4 0" />',
    beach: '<path d="M4 11c1.8-3.7 5.1-6 8-6s6.2 2.3 8 6" /><path d="M12 5v14" /><path d="M8 11c.8-2.3 2.2-4.2 4-6 1.8 1.8 3.2 3.7 4 6" /><path d="M4 18c1.4-1 2.8-.5 4 0s2.6 1 4 0 2.8-1 4 0 2.6 1 4 0" />',
    'water-leisure': '<path d="M4 17V3h3"></path><path d="M4 7h3M4 11h3M4 15h3"></path><path d="M7 3c1.5 0 3 .5 4 2l4 6c1 1.5 2.5 2.5 4.5 2.5h2.5"></path><path d="M2 20c1.5-1 3.5-1 5 0s3.5 1 5 0s3.5-1 5 0s3.5 1 5 0"></path>',
    WATERPARK: '<path d="M4 17V3h3"></path><path d="M4 7h3M4 11h3M4 15h3"></path><path d="M7 3c1.5 0 3 .5 4 2l4 6c1 1.5 2.5 2.5 4.5 2.5h2.5"></path><path d="M2 20c1.5-1 3.5-1 5 0s3.5 1 5 0s3.5-1 5 0s3.5 1 5 0"></path>',
    waterpark: '<path d="M4 17V3h3"></path><path d="M4 7h3M4 11h3M4 15h3"></path><path d="M7 3c1.5 0 3 .5 4 2l4 6c1 1.5 2.5 2.5 4.5 2.5h2.5"></path><path d="M2 20c1.5-1 3.5-1 5 0s3.5 1 5 0s3.5-1 5 0s3.5 1 5 0"></path>',
    ZOO: '<path d="M12 12.5c-3 0-5.5 1.8-5.5 4 0 1.8 2 3.5 5.5 3.5s5.5-1.7 5.5-3.5c0-2.2-2.5-4-5.5-4Z"></path><circle cx="6.5" cy="10" r="1.8"></circle><circle cx="10" cy="6.5" r="1.8"></circle><circle cx="14" cy="6.5" r="1.8"></circle><circle cx="17.5" cy="10" r="1.8"></circle>',
    zoo: '<path d="M12 12.5c-3 0-5.5 1.8-5.5 4 0 1.8 2 3.5 5.5 3.5s5.5-1.7 5.5-3.5c0-2.2-2.5-4-5.5-4Z"></path><circle cx="6.5" cy="10" r="1.8"></circle><circle cx="10" cy="6.5" r="1.8"></circle><circle cx="14" cy="6.5" r="1.8"></circle><circle cx="17.5" cy="10" r="1.8"></circle>',
    'museums-culture': '<path d="m3 9 9-5 9 5" /><path d="M5 10h14M4 20h16M6.5 10v7M10.2 10v7M13.8 10v7M17.5 10v7" /><path d="M3 22h18" />',
    'theater-stage': '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" x2="12" y1="19" y2="22" />',
    'development-support': '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />',
    'excursions-tours': '<circle cx="12" cy="12" r="10" /><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" />'
  };

  function categoryIconDataUrl(place, color) {
    const source = place && place.category_icon_svg;
    if (!source) return "";
    const coloredSource = String(source).replace(/currentColor/g, color || "#6B7280");
    return "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(coloredSource);
  }

  function buildMarkerGlyph(place, colorText) {
    const iconDataUrl = categoryIconDataUrl(place, colorText);
    if (iconDataUrl) {
      return '<image href="' + iconDataUrl + '" x="11" y="10" width="16" height="16" />';
    }
    const categoryCode = place && place.category_code;
    const normalizedCode = String(categoryCode || '').toLowerCase();
    const iconSvgContent = CATEGORY_SVGS[categoryCode] || CATEGORY_SVGS[normalizedCode] || '<circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>';
    return (
      '<g transform="translate(11, 10) scale(0.667)">' +
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="' + colorText + '" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
      iconSvgContent +
      "</svg>" +
      "</g>"
    );
  }

  function buildDynamicMarkerSvg(place) {
    const bg = (place && place.category_color_bg) || "#F3F4F6";
    const text = (place && place.category_color_text) || "#6B7280";

    return '<svg xmlns="http://www.w3.org/2000/svg" width="38" height="48" viewBox="0 0 38 48" fill="none">' +
      '<path d="M19 47C13.5 39 3 31 3 18C3 8.5 10 1 19 1C28 1 35 8.5 35 18C35 31 24.5 39 19 47Z" fill="' + text + '" stroke="white" stroke-width="2.2"/>' +
      '<circle cx="19" cy="18" r="11" fill="' + bg + '" />' +
      buildMarkerGlyph(place, text) +
      '</svg>';
  }

  function buildGoogleMarkerIcon(place) {
    const svg = buildDynamicMarkerSvg(place);
    return {
      url: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
      scaledSize: new google.maps.Size(38, 48),
      anchor: new google.maps.Point(19, 48),
    };
  }

  function buildGoogleClusterSvg(count) {
    return '<svg xmlns="http://www.w3.org/2000/svg" width="54" height="54" viewBox="0 0 54 54" fill="none">' +
      '<circle cx="27" cy="27" r="27" fill="rgba(17, 117, 67, 0.10)"/>' +
      '<circle cx="27" cy="27" r="25" fill="rgba(17, 117, 67, 0.18)"/>' +
      '<circle cx="27" cy="27" r="19" fill="#087443" stroke="white" stroke-width="3"/>' +
      '<text x="27" y="27" text-anchor="middle" dominant-baseline="central" fill="white" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif" font-size="15px" font-weight="800">' + count + '</text>' +
      '</svg>';
  }

  function renderFallback(mapEl, mapNoteEl) {
    if (!mapEl) return;

    if (mapNoteEl) {
      mapNoteEl.hidden = true;
      mapNoteEl.textContent = "";
    }

    const title = mapEl.dataset.fallbackTitle || "Map";
    mapEl.innerHTML =
      '<iframe class="home-map home-map-fallback" src="https://maps.google.com/maps?q=Baku%2C%20Azerbaijan&z=11&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="' +
      escapeHtml(title) +
      '"></iframe>';
  }

  function renderMapUnavailable(mapEl, mapNoteEl) {
    if (!mapEl) return;
    const catalogUrl = mapEl.dataset.catalogUrl || "/catalog/";
    const catalogLabel = mapEl.dataset.catalogLabel || "Открыть каталог";
    const msg = escapeHtml(SCRIPT_CONFIG.unavailableLabel);
    mapEl.innerHTML =
      '<div class="home-map-empty">' +
        '<div class="home-map-empty-inner">' +
          '<div class="home-map-empty-icon" aria-hidden="true">' +
            '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
              '<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>' +
              '<circle cx="12" cy="10" r="3"></circle>' +
            '</svg>' +
          '</div>' +
          '<p class="home-map-empty-title">' + msg + '</p>' +
          '<a class="home-map-empty-action" href="' + escapeHtml(catalogUrl) + '">' +
            '<span>' + escapeHtml(catalogLabel) + '</span>' +
            '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>' +
          '</a>' +
        '</div>' +
      '</div>';
    setMapNote(mapNoteEl, "", true);
  }

  function loadStylesheet(href, integrity) {
    return new Promise(function (resolve, reject) {
      const existing = document.querySelector('link[rel="stylesheet"][href="' + href + '"]');
      if (existing) {
        if (existing.dataset.kmLoaded === "1") {
          resolve(existing);
          return;
        }

        existing.addEventListener("load", function () {
          existing.dataset.kmLoaded = "1";
          resolve(existing);
        }, { once: true });
        existing.addEventListener("error", function () {
          reject(new Error("Failed to load stylesheet: " + href));
        }, { once: true });
        return;
      }

      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      if (integrity) {
        link.integrity = integrity;
        link.crossOrigin = "anonymous";
      }
      link.addEventListener("load", function () {
        link.dataset.kmLoaded = "1";
        resolve(link);
      }, { once: true });
      link.addEventListener("error", function () {
        reject(new Error("Failed to load stylesheet: " + href));
      }, { once: true });
      document.head.appendChild(link);
    });
  }

  function loadScript(href, integrity) {
    return new Promise(function (resolve, reject) {
      const existing = document.querySelector('script[src="' + href + '"]');
      if (existing) {
        if (existing.dataset.kmLoaded === "1") {
          resolve(existing);
          return;
        }

        existing.addEventListener("load", function () {
          existing.dataset.kmLoaded = "1";
          resolve(existing);
        }, { once: true });
        existing.addEventListener("error", function () {
          reject(new Error("Failed to load script: " + href));
        }, { once: true });
        return;
      }

      const script = document.createElement("script");
      script.src = href;
      if (integrity) {
        script.integrity = integrity;
        script.crossOrigin = "anonymous";
      }
      script.addEventListener("load", function () {
        script.dataset.kmLoaded = "1";
        resolve(script);
      }, { once: true });
      script.addEventListener("error", function () {
        reject(new Error("Failed to load script: " + href));
      }, { once: true });
      document.head.appendChild(script);
    });
  }

  function buildSharedState(mapEl, mapNoteEl) {
    const places = parsePlaces();
    const validPlaces = places.filter(function (place) {
      return typeof place.lat === "number" && typeof place.lng === "number";
    });

    return {
      places: validPlaces,
      detailsLabel: mapEl.dataset.detailsLabel || "Details",
      ageLabels: {
        range: mapEl.dataset.ageRangeLabel || "{from}–{to}",
        from: mapEl.dataset.ageFromLabel || "{from}+",
        to: mapEl.dataset.ageToLabel || "0–{to}",
      },
      mapEl: mapEl,
      mapNoteEl: mapNoteEl,
    };
  }

  function setMapNote(mapNoteEl, emptyLabel, hasVisiblePlaces) {
    if (!mapNoteEl) return;
    mapNoteEl.hidden = hasVisiblePlaces;
    mapNoteEl.textContent = hasVisiblePlaces ? "" : emptyLabel || "";
  }

  function updateLiveCount(count) {
    const counterEls = document.querySelectorAll("[data-home-map-live-count]");
    counterEls.forEach(function (el) {
      if (el.textContent.trim() === String(count)) return;
      el.textContent = count;
      if (typeof el.animate === "function" &&
          !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        el.getAnimations().forEach(function (animation) { animation.cancel(); });
        el.animate([{ opacity: 0.45 }, { opacity: 1 }], { duration: 180, easing: "ease-out" });
      }
    });
  }

  let pendingFocusPlaceId = null;
  let activeMapFocusHandler = null;

  function scrollToMap() {
    const mapSection = document.getElementById("home-map-section");
    if (mapSection) {
      mapSection.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start"
      });
      mapSection.classList.remove("is-highlighted");
      void mapSection.offsetWidth;
      mapSection.classList.add("is-highlighted");
    }
  }

  function requestFocusPlace(placeId) {
    scrollToMap();
    if (typeof activeMapFocusHandler === "function") {
      activeMapFocusHandler(placeId);
    } else {
      pendingFocusPlaceId = placeId;
      if (typeof window.kidsMapTriggerHomeMapLoad === "function") {
        window.kidsMapTriggerHomeMapLoad();
      }
    }
  }
  window.kidsMapFocusPlaceOnHomeMap = requestFocusPlace;

  function highlightMatch(text, query) {
    if (!text) return "";
    if (!query) return escapeHtml(text);

    const normText = normalizeSearch(text);
    const normQ = normalizeSearch(query);
    const idx = normText.indexOf(normQ);
    if (idx === -1) {
      return escapeHtml(text);
    }
    const matchLen = query.length;
    const before = text.slice(0, idx);
    const matched = text.slice(idx, idx + matchLen);
    const after = text.slice(idx + matchLen);
    return escapeHtml(before) + "<b>" + escapeHtml(matched) + "</b>" + escapeHtml(after);
  }

  function initHomeSearchAutocomplete(updateMap) {
    const form = document.querySelector("[data-home-map-filter-form]");
    if (!form) return;

    const queryInput = form.querySelector('[name="q"]');
    const autocompleteEl = document.getElementById("home-search-autocomplete");
    if (!queryInput || !autocompleteEl) return;

    const listEl = autocompleteEl.querySelector("[data-hs-ac-list]");
    const emptyEl = autocompleteEl.querySelector("[data-hs-ac-empty]");
    const footerEl = autocompleteEl.querySelector("[data-hs-ac-footer]");
    const showAllBtn = autocompleteEl.querySelector("[data-hs-ac-show-all]");
    const showAllText = autocompleteEl.querySelector("[data-hs-ac-show-all-text]");
    const clearBtn = form.querySelector("[data-home-search-clear]");

    let allPlaces = parsePlaces().flatMap(pointMembers);
    let autocompleteGeneration = 0;
    let selectedIndex = -1;
    let currentMatches = [];

    function hideAutocomplete() {
      autocompleteGeneration += 1;
      autocompleteEl.hidden = true;
      selectedIndex = -1;
    }

    async function showAutocomplete() {
      const generation = ++autocompleteGeneration;
      const q = normalizeSearch(queryInput.value);
      if (!q) {
        hideAutocomplete();
        return;
      }

      try {
        const points = await fetchFilteredPoints();
        if (generation !== autocompleteGeneration || !normalizeSearch(queryInput.value)) return;
        allPlaces = points.flatMap(pointMembers);
        currentMatches = allPlaces;
      } catch (_error) { hideAutocomplete(); return; }

      selectedIndex = -1;

      if (!currentMatches.length) {
        if (listEl) listEl.innerHTML = "";
        if (emptyEl) emptyEl.hidden = false;
        if (footerEl) footerEl.hidden = true;
        autocompleteEl.hidden = false;
        return;
      }

      if (emptyEl) emptyEl.hidden = true;

      const displayList = currentMatches.slice(0, 7);
      if (listEl) {
        listEl.innerHTML = displayList.map(function (place, idx) {
          const iconHtml = place.category_icon_svg
            ? place.category_icon_svg
            : (place.category_icon_url
              ? '<img src="' + escapeHtml(place.category_icon_url) + '" alt="" />'
              : '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>');

          const ageBadge = formatAgeBadge(place, {
            range: "{from}–{to}",
            from: "{from}+",
            to: "0–{to}"
          });

          const highlightedName = highlightMatch(place.name, queryInput.value);
          const onMapLabel = autocompleteEl.dataset.labelOnMap || "На карте";

          return (
            '<li role="option" class="hs-ac-item" data-place-id="' + escapeHtml(place.id || place.url || place.name) + '" data-index="' + idx + '" tabindex="0">' +
              '<div class="hs-ac-item-icon" style="background:' + escapeHtml(place.category_color_bg || '#f1f5f9') + ';color:' + escapeHtml(place.category_color_text || '#136f38') + ';">' +
                iconHtml +
              '</div>' +
              '<div class="hs-ac-item-content">' +
                '<div class="hs-ac-item-top">' +
                  '<span class="hs-ac-item-name">' + highlightedName + '</span>' +
                  (place.price ? '<span class="hs-ac-item-price">' + escapeHtml(place.price) + '</span>' : '') +
                '</div>' +
                '<div class="hs-ac-item-meta">' +
                  (place.category ? '<span class="hs-ac-item-cat">' + escapeHtml(place.category) + '</span>' : '') +
                  (place.district_label ? '<span class="hs-ac-item-sep">•</span><span class="hs-ac-item-dist">' + escapeHtml(place.district_label) + '</span>' : '') +
                  (ageBadge ? '<span class="hs-ac-item-sep">•</span><span class="hs-ac-item-age">' + escapeHtml(ageBadge) + '</span>' : '') +
                '</div>' +
              '</div>' +
              '<div class="hs-ac-item-badge">' +
                '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>' +
                '<span>' + escapeHtml(onMapLabel) + '</span>' +
              '</div>' +
            '</li>'
          );
        }).join('');
      }

      if (currentMatches.length > 7 && footerEl && showAllText) {
        footerEl.hidden = false;
        const pattern = autocompleteEl.dataset.labelShowAll || "Показать все {count} мест на карте";
        showAllText.textContent = pattern.replace("{count}", String(currentMatches.length));
      } else if (footerEl) {
        footerEl.hidden = true;
      }

      autocompleteEl.hidden = false;
    }

    function selectPlaceById(placeId) {
      const place = allPlaces.find(function (p) {
        return (placeId && String(p.id) === String(placeId)) ||
               (p.url && p.url === placeId) ||
               (p.name && p.name === placeId);
      });
      if (!place) return;

      hideAutocomplete();
      queryInput.value = place.name;
      if (clearBtn) clearBtn.hidden = false;
      if (typeof updateMap === "function") {
        updateMap();
      }
      pendingFocusPlaceId = place.id;
    }

    queryInput.addEventListener("input", function () {
      showAutocomplete();
    });

    queryInput.addEventListener("focus", function () {
      if (queryInput.value.trim()) {
        showAutocomplete();
      }
    });

    if (listEl) {
      listEl.addEventListener("click", function (e) {
        const item = e.target.closest(".hs-ac-item");
        if (item && item.dataset.placeId) {
          selectPlaceById(item.dataset.placeId);
        }
      });
    }

    if (showAllBtn) {
      showAllBtn.addEventListener("click", function () {
        hideAutocomplete();
        if (typeof updateMap === "function") {
          updateMap();
        }
        scrollToMap();
      });
    }

    // Keyboard navigation
    queryInput.addEventListener("keydown", function (e) {
      if (autocompleteEl.hidden) return;

      const items = listEl ? Array.from(listEl.querySelectorAll(".hs-ac-item")) : [];
      if (!items.length) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        selectedIndex = (selectedIndex + 1) % items.length;
        updateItemSelection(items);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        selectedIndex = (selectedIndex - 1 + items.length) % items.length;
        updateItemSelection(items);
      } else if (e.key === "Enter" && selectedIndex >= 0 && items[selectedIndex]) {
        e.preventDefault();
        const selectedPlaceId = items[selectedIndex].dataset.placeId;
        selectPlaceById(selectedPlaceId);
      } else if (e.key === "Escape") {
        hideAutocomplete();
      }
    });

    function updateItemSelection(items) {
      items.forEach(function (el, idx) {
        const isSel = idx === selectedIndex;
        el.classList.toggle("is-selected", isSel);
        el.setAttribute("aria-selected", isSel ? "true" : "false");
        if (isSel) {
          el.scrollIntoView({ block: "nearest" });
        }
      });
    }

    document.addEventListener("click", function (e) {
      if (!autocompleteEl.contains(e.target) && e.target !== queryInput) {
        hideAutocomplete();
      }
    });
  }

  function bindFilterListeners(updateMap) {
    const form = document.querySelector("[data-home-map-filter-form]");
    if (!form || typeof updateMap !== "function") return;

    let searchTimer = null;
    const queryInput = form.querySelector('[name="q"]');
    const clearBtn = form.querySelector("[data-home-search-clear]");
    const districtInput = form.querySelector('[name="district"]');
    const districtVisibleInput = form.querySelector("[data-home-district-input]");
    const districtOptions = getDistrictOptions(form);
    const categorySelect = form.querySelector('select[name="category"]');
    const ageInput = getAgeInput(form);
    const ageButtons = getAgeButtons(form);
    const resetBtn = form.querySelector("[data-home-search-reset]");

    function scheduleUpdate() {
      if (searchTimer) {
        window.clearTimeout(searchTimer);
      }
      searchTimer = window.setTimeout(updateMap, 120);
    }

    if (queryInput) {
      function syncClearBtn() {
        if (clearBtn) clearBtn.hidden = !queryInput.value;
      }
      queryInput.addEventListener("input", function () {
        syncClearBtn();
        scheduleUpdate();
      });
      syncClearBtn();

      if (clearBtn) {
        clearBtn.addEventListener("click", function () {
          queryInput.value = "";
          syncClearBtn();
          scheduleUpdate();
          queryInput.focus();
        });
      }
    }

    if (districtInput) {
      if (districtVisibleInput) {
        districtVisibleInput.addEventListener("input", function () {
          const resolvedOption = resolveDistrictValue(districtVisibleInput.value, districtOptions);
          districtInput.value = resolvedOption ? resolvedOption.value : "";
          if (!normalizeValue(districtVisibleInput.value) || resolvedOption) {
            scheduleUpdate();
          }
        });

        districtVisibleInput.addEventListener("change", function () {
          const resolvedOption = resolveDistrictValue(districtVisibleInput.value, districtOptions);
          districtInput.value = resolvedOption ? resolvedOption.value : "";
          districtVisibleInput.value = resolvedOption ? resolvedOption.label : "";
          scheduleUpdate();
        });
      } else {
        districtInput.addEventListener("change", function () {
          scheduleUpdate();
        });
      }
    }

    if (categorySelect) {
      categorySelect.addEventListener("change", updateMap);
    }

    if (ageInput) {
      ageInput.addEventListener("change", updateMap);
      if (ageButtons.length) {
        syncAgeButtons(form);
      }
    }

    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        if (queryInput) {
          queryInput.value = "";
          if (clearBtn) clearBtn.hidden = true;
        }
        if (districtInput) districtInput.value = "";
        if (districtVisibleInput) districtVisibleInput.value = "";
        const districtTriggerText = form.querySelector(".km-tree-trigger-text");
        if (districtTriggerText) {
          const defaultLabel = form.querySelector(".km-tree-dropdown")?.dataset?.defaultLabel || "Регион / район";
          districtTriggerText.textContent = defaultLabel;
        }
        form.querySelector(".km-location-tree")?.classList?.remove("is-active");

        if (categorySelect) categorySelect.value = "";
        if (ageInput) ageInput.value = "";
        syncAgeButtons(form);

        // Keep the existing category presentation handler in sync with reset.
        if (categorySelect) {
          categorySelect.dispatchEvent(new Event("change", { bubbles: true }));
        } else {
          scheduleUpdate();
        }
      });
    }

    /* Prevent page reload on submit, update map and smoothly focus/scroll to it */
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      updateMap();
      scrollToMap();
    });

    const showMapBtn = form.querySelector("[data-home-show-map-btn]");
    if (showMapBtn) {
      showMapBtn.addEventListener("click", function (e) {
        e.preventDefault();
        updateMap();
        scrollToMap();
      });
    }

    const metroInput = form.querySelector('[name="metro"]');
    if (metroInput) metroInput.addEventListener("change", updateMap);
    initHomeSearchAutocomplete(updateMap);
  }

  function mountGoogleMap(sharedState) {
    if (!window.google || !window.google.maps || !sharedState) return false;

    const { mapEl, mapNoteEl, places, detailsLabel, ageLabels } = sharedState;
    if (mapEl.dataset.mapInitialized === "1") return true;

    mapEl.dataset.mapInitialized = "1";

    const mapOptions = {
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      gestureHandling: "cooperative",
      cameraControl: false,
      zoomControl: true,
      zoomControlOptions: {position: google.maps.ControlPosition.RIGHT_TOP},
      tilt: 0, heading: 0,
    };
    if (SCRIPT_CONFIG.googleMapsMapId) mapOptions.mapId = SCRIPT_CONFIG.googleMapsMapId;
    const map = new google.maps.Map(mapEl, mapOptions);
    const infoWindow = new google.maps.InfoWindow();

    const motion = window.KidsMapGoogleMotion.create(map);
    const choice = window.KidsMapGoogleMotion.chooser(mapEl, openPlace);
    let selectedMarker = null;
    let syncPending = false;
    function closePlace() {
      infoWindow.close();
      motion.select(null);
      selectedMarker = null;
    }
    function openPlace(place, marker) {
      motion.cancel();
      choice.close(false);
      selectedMarker = marker;
      motion.select(marker);
      infoWindow.setOptions({maxWidth: Math.min(320, mapEl.clientWidth - 48), disableAutoPan: window.KidsMapGoogleMotion.reduced()});
      infoWindow.setContent(renderPopupContent(place, detailsLabel, ageLabels));
      infoWindow.open({anchor: marker, map: map, shouldFocus: true});
    }
    infoWindow.addListener('closeclick', () => { const marker = selectedMarker; motion.select(null); selectedMarker = null; marker?.getElement?.().focus(); });
    map.addListener('click', () => { closePlace(); choice.close(false); });
    map.addListener('zoom_changed', () => { closePlace(); choice.close(false); });
    mapEl.addEventListener('keydown', event => {
      if (event.key === 'Escape' && selectedMarker) {
        const marker = selectedMarker; closePlace(); marker.getElement?.().focus();
      }
    });
    const previousClusterKeys = new Set();

    // ── Cluster Group ────────────────────────────────────────────────────────
    let markerCluster = null;
    if (window.markerClusterer && window.markerClusterer.MarkerClusterer && !window.markerClusterer.dummy) {
      var clusterAlgorithm = (window.markerClusterer.SuperClusterAlgorithm)
        // Keep a single nearby pin out of the visual footprint of a cluster.
        // 100 px also prevents a count badge from covering a neighbouring pin.
        ? new window.markerClusterer.SuperClusterAlgorithm({ maxZoom: 18, radius: 100 })
        : undefined;
      markerCluster = new window.markerClusterer.MarkerClusterer({
        map: map,
        markers: [],
        algorithm: clusterAlgorithm,
        renderer: {
          render: function (cluster, stats, mapInstance) {
            const count = cluster.count;
            const position = cluster.position;
            const svg = buildGoogleClusterSvg(count);
            const key = cluster.markers.map(m => m.__kidsMapPointKey || m.__kidsMapPlace?.id || m.__kidsMapPlace?.url).sort().join('|');
            const skipEntrance = previousClusterKeys.has(key);
            previousClusterKeys.add(key);
            return window.kidsMapCreateGoogleMarker({
              position: position,
              title: window.KidsMapGoogleMotion.clusterTitle(count),
              publicVisual: true, ownerMap: map, skipEntrance: skipEntrance,
              icon: {
                url: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
                scaledSize: new google.maps.Size(54, 54),
                anchor: new google.maps.Point(27, 27),
              },
              zIndex: 1000000 + count,
              mapId: SCRIPT_CONFIG.googleMapsMapId,
            });
          }
        },
        onClusterClick: function (event, cluster) {
          closePlace(); choice.close(false);
          motion.expand(cluster, markers => choice.show(markers, cluster.marker));
        },
      });
    }

    // ── Build markers ───────────────────────────────────────────────────────
    const markerItems = [];

    function rebuildMarkers(points) {
      markerItems.forEach(item => item.marker.setMap(null));
      markerItems.length = 0;
    points.forEach(function (place) {
      if (!hasValidCoordinates(place)) return;
      const position = {lat: place.lat, lng: place.lng};
      const marker = window.kidsMapCreateGoogleMarker({
        position: position,
        title: place.name || "",
        icon: buildGoogleMarkerIcon(place),
        publicVisual: true, ownerMap: map,
        mapId: SCRIPT_CONFIG.googleMapsMapId,
      });

      marker.__kidsMapPlace = place;
      marker.__kidsMapPointKey = place.key;
      marker.addListener("click", function () {
        const peers = markerItems.filter(item => visibleMarkers.has(item.marker) && item.position.lat === place.lat && item.position.lng === place.lng).map(item => item.marker);
        if (peers.length > 1) { closePlace(); motion.cancel(); choice.show(peers, marker); }
        else openPlace(place, marker);
      });

      markerItems.push({
        marker: marker,
        place: place,
        position: position,
      });
    });

    }
    rebuildMarkers(places);

    // ── Core sync ───────────────────────────────────────────────────────────
    function syncVisibleMarkers() {
      if (syncPending) return;
      syncPending = true;
      window.setTimeout(function () {
        syncPending = false;
        _doSync();
      }, 0);
    }

    const updateMembership = markerCluster ? window.KidsMapGoogleMotion.membership(markerCluster) : null;
    let visibleMarkers = new Set();
    function _doSync() {
      const filters = getFilterState();
      const activeMarkers = markerItems.map(item => item.marker);
      const next = new Set(activeMarkers);
      if (selectedMarker && !next.has(selectedMarker)) closePlace();
      if (updateMembership) updateMembership(activeMarkers);
      else {
        visibleMarkers.forEach(marker => { if (!next.has(marker)) marker.setMap(null); });
        next.forEach(marker => { if (!visibleMarkers.has(marker)) marker.setMap(map); });
      }
      visibleMarkers = next;
      setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || '', activeMarkers.length > 0);
      updateLiveCount(businessCount(markerItems.map(item => item.place)));
    }
    function syncVisibleMarkersFromFilter() {
      updateFromServer();
    }
    const updateFromServer = serverFilterUpdater(points => {
      rebuildMarkers(points);
      _doSync();
      if (pendingFocusPlaceId && points.length) {
        const target = pendingFocusPlaceId;
        pendingFocusPlaceId = null;
        activeMapFocusHandler(target);
      }
    }, () => { closePlace(); motion.cancel(); choice.close(false); }, () => {
      setMapNote(mapNoteEl, SCRIPT_CONFIG.unavailableLabel, false);
    });

    const filterForm = document.querySelector('[data-home-map-filter-form]');
    if (filterForm) filterForm.addEventListener('input', () => { closePlace(); motion.cancel(); choice.close(false); });
    bindFilterListeners(syncVisibleMarkersFromFilter);
    syncVisibleMarkers();

    function focusGooglePlace(placeId) {
      const item = markerItems.find(function (m) {
        return (placeId && pointMembers(m.place).some(member => String(member.id) === String(placeId))) ||
               (m.place.url && m.place.url === placeId) ||
               (m.place.name && m.place.name === placeId);
      });
      if (!item) return;

      scrollToMap();
      if (!visibleMarkers.has(item.marker)) {
        item.marker.setMap(map);
      }
      map.setCenter({ lat: item.place.lat, lng: item.place.lng });
      map.setZoom(16);
      openPlace(item.place, item.marker);
    }

    activeMapFocusHandler = focusGooglePlace;
    if (pendingFocusPlaceId) {
      const targetId = pendingFocusPlaceId;
      pendingFocusPlaceId = null;
      window.setTimeout(function () {
        focusGooglePlace(targetId);
      }, 350);
    }

    return true;
  }

  // ── Coordinate helpers ──────────────────────────────────────────────────────

  function hasValidCoordinates(place) {
    if (!place) return false;
    const lat = place.lat, lng = place.lng;
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return false;
    if (Math.abs(lat) < 0.001 && Math.abs(lng) < 0.001) return false; // null-island
    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) return false;
    return true;
  }

  function hasActiveFilters(filters) {
    return !!(filters.query || filters.category || filters.district || filters.metro || filters.age);
  }

  // Baku bounding box — used to choose fitBounds maxZoom
  var BAKU_LAT_MIN = 40.28, BAKU_LAT_MAX = 40.55;
  var BAKU_LNG_MIN = 49.65, BAKU_LNG_MAX = 50.15;

  function allInBaku(items) {
    return items.every(function (item) {
      return item.place.lat >= BAKU_LAT_MIN && item.place.lat <= BAKU_LAT_MAX &&
        item.place.lng >= BAKU_LNG_MIN && item.place.lng <= BAKU_LNG_MAX;
    });
  }

  // ── Leaflet map ─────────────────────────────────────────────────────────────

  function mountLeafletMap(sharedState) {
    if (!window.L || !window.L.markerClusterGroup || !sharedState) return false;

    const { mapEl, mapNoteEl, places } = sharedState;
    if (mapEl.dataset.mapInitialized === "1") return true;

    mapEl.dataset.mapInitialized = "1";
    mapEl.innerHTML = "";

    const map = L.map(mapEl, {
      center: [DEFAULT_CENTER.lat, DEFAULT_CENTER.lng],
      zoom: DEFAULT_ZOOM,
      scrollWheelZoom: false,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    // ── Cluster group ───────────────────────────────────────────────────────
    const markerClusterGroup = L.markerClusterGroup({
      showCoverageOnHover: false,
      // Let MarkerCluster handle click: zoom → then spiderfy if needed
      zoomToBoundsOnClick: false,
      spiderfyOnMaxZoom: true,
      maxClusterRadius: function (zoom) {
        if (zoom >= 15) return 30;
        if (zoom >= 13) return 55;
        if (zoom >= 11) return 70;
        return 90;
      },

      iconCreateFunction: function (cluster) {
        const count = cluster.getChildCount();
        return L.divIcon({
          className: "kidsmap-map-cluster",
          html: "<span class=\"kidsmap-map-cluster__count\">" + count + "</span>",
          iconSize: [54, 54],
          iconAnchor: [27, 27],
        });
      }
    });
    map.addLayer(markerClusterGroup);

    function handleHomeClusterClick(event) {
      userInteracted = true;
      const childMarkers = event.layer.getAllChildMarkers();

      let allSameCoords = true;
      if (childMarkers.length > 0) {
        const firstLatLng = childMarkers[0].getLatLng();
        for (let i = 1; i < childMarkers.length; i++) {
          const latLng = childMarkers[i].getLatLng();
          if (latLng.lat !== firstLatLng.lat || latLng.lng !== firstLatLng.lng) {
            allSameCoords = false;
            break;
          }
        }
      }

      if (allSameCoords && childMarkers.length > 0) {
        map.setView(childMarkers[0].getLatLng(), 18, { animate: true });
        event.layer.spiderfy();
      } else {
        map.fitBounds(event.layer.getBounds(), {
          padding: [40, 40],
          animate: true,
          duration: 0.45
        });
      }
    }

    markerClusterGroup.on("clusterclick", handleHomeClusterClick);

    // ── Interaction tracking ────────────────────────────────────────────────
    // userInteracted: true after any user gesture — prevents auto fitBounds
    var userInteracted = false;
    // syncPending: collapses rapid successive sync calls into one
    var syncPending = false;

    map.on("zoomstart movestart", function (e) {
      if (e.originalEvent) { userInteracted = true; }
    });

    // ── Build markers ───────────────────────────────────────────────────────
    const markerItems = [];

    function rebuildMarkers(points) {
      markerClusterGroup.clearLayers();
      markerItems.length = 0;
    points.forEach(function (place) {
      if (!hasValidCoordinates(place)) return;

      const position = [place.lat, place.lng];
      const markerLabel = (mapEl.dataset.markerLabel || "{name}").replace("{name}", place.name || "");
      const marker = L.marker(position, {
        icon: L.divIcon({
          html: buildDynamicMarkerSvg(place),
          className: "custom-leaflet-marker",
          iconSize: [38, 48],
          iconAnchor: [19, 48],
          popupAnchor: [0, -42],
        }),
        title: place.name || "",
        alt: markerLabel,
      });

      marker.on("add", function () {
        window.requestAnimationFrame(function () {
          var el = marker.getElement();
          if (!el) return;
          el.setAttribute("role", "button");
          el.setAttribute("aria-label", markerLabel);
          el.setAttribute("title", markerLabel);
        });
      });

      marker.bindPopup(renderPopupContent(place, mapEl.dataset.detailsLabel || "Details", {
        range: mapEl.dataset.ageRangeLabel || "{from}–{to}",
        from: mapEl.dataset.ageFromLabel || "{from}+",
        to: mapEl.dataset.ageToLabel || "0–{to}",
      }));
      markerItems.push({ marker: marker, place: place, position: position });
    });

    }
    rebuildMarkers(places);

    // ── Core sync ───────────────────────────────────────────────────────────
    function syncVisibleMarkers() {
      if (syncPending) return;
      syncPending = true;
      window.setTimeout(function () {
        syncPending = false;
        _doSync();
      }, 0);
    }

    function _doSync() {
      const filters = getFilterState();
      const layersToAdd = [];
      const visibleItems = [];

      map.closePopup();

      // Atomic clear + add (no chunkedLoading → no race condition)
      markerClusterGroup.clearLayers();

      markerItems.forEach(function (item) {
        if (!hasValidCoordinates(item.place)) return;
        layersToAdd.push(item.marker);
        visibleItems.push(item);
      });

      if (layersToAdd.length) {
        markerClusterGroup.addLayers(layersToAdd);
        markerClusterGroup.refreshClusters();
      }

      markerClusterGroup.off("clusterclick", handleHomeClusterClick);
      markerClusterGroup.on("clusterclick", handleHomeClusterClick);

      // No results
      updateLiveCount(businessCount(visibleItems.map(item => item.place)));
      if (!visibleItems.length) {
        userInteracted = false;
        map.setView([DEFAULT_CENTER.lat, DEFAULT_CENTER.lng], DEFAULT_ZOOM, { animate: false });
        setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", false);
        return;
      }

      setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", true);

      // Don't override zoom after user has manually navigated
      if (userInteracted) return;

      map.invalidateSize({ pan: false });

      // No active filters → show default Baku overview (don't fitBounds all 33+ places)
      if (!hasActiveFilters(filters)) {
        map.setView([DEFAULT_CENTER.lat, DEFAULT_CENTER.lng], DEFAULT_ZOOM, { animate: false });
        return;
      }

      // Single filtered result
      if (visibleItems.length === 1) {
        map.setView(visibleItems[0].position, 15, { animate: true });
        return;
      }

      // Multiple filtered results → fitBounds
      var bounds = L.latLngBounds([]);
      visibleItems.forEach(function (item) { bounds.extend(item.position); });
      if (!bounds.isValid()) return;

      var maxZoom = allInBaku(visibleItems) ? 13 : 14;

      window.setTimeout(function () {
        if (userInteracted || !bounds.isValid()) return;
        map.fitBounds(bounds, {
          paddingTopLeft: [48, 48],
          paddingBottomRight: [48, 48],
          maxZoom: maxZoom,
          minZoom: 9,
          animate: true,
        });
      }, 80);
    }

    // Filter change: reset userInteracted so bounds recalculate for new results
    function syncVisibleMarkersFromFilter() {
      userInteracted = false;
      updateFromServer();
    }
    const updateFromServer = serverFilterUpdater(points => {
      rebuildMarkers(points);
      _doSync();
      if (pendingFocusPlaceId && points.length) {
        const target = pendingFocusPlaceId;
        pendingFocusPlaceId = null;
        activeMapFocusHandler(target);
      }
    }, () => map.closePopup(), () => {
      setMapNote(mapNoteEl, SCRIPT_CONFIG.unavailableLabel, false);
    });

    bindFilterListeners(syncVisibleMarkersFromFilter);
    const filterForm = document.querySelector('[data-home-map-filter-form]');
    if (filterForm) filterForm.addEventListener('input', () => map.closePopup());

    // Initial load — single deferred call, no double-sync
    window.setTimeout(function () {
      map.invalidateSize({ pan: false });
      _doSync();
    }, 0);

    // Resize: only fix tile seams, never refits bounds
    if (typeof window.ResizeObserver === "function") {
      new window.ResizeObserver(function () {
        map.invalidateSize({ pan: false });
      }).observe(mapEl);
    }

    function focusLeafletPlace(placeId) {
      const item = markerItems.find(function (m) {
        return (placeId && pointMembers(m.place).some(member => String(member.id) === String(placeId))) ||
               (m.place.url && m.place.url === placeId) ||
               (m.place.name && m.place.name === placeId);
      });
      if (!item) return;

      userInteracted = true;
      scrollToMap();

      if (!markerClusterGroup.hasLayer(item.marker)) {
        markerClusterGroup.addLayer(item.marker);
      }

      if (typeof markerClusterGroup.zoomToShowLayer === "function") {
        markerClusterGroup.zoomToShowLayer(item.marker, function () {
          item.marker.openPopup();
        });
      } else {
        map.setView([item.place.lat, item.place.lng], 16, { animate: true });
        item.marker.openPopup();
      }
    }

    activeMapFocusHandler = focusLeafletPlace;
    if (pendingFocusPlaceId) {
      const targetId = pendingFocusPlaceId;
      pendingFocusPlaceId = null;
      window.setTimeout(function () {
        focusLeafletPlace(targetId);
      }, 350);
    }

    return true;
  }


  function startMapBootstrap() {

    const mapSection = document.getElementById("home-map-section");
    const mapEl = document.getElementById("home-map");
    const mapNoteEl = document.getElementById("home-map-note");
    if (!mapSection || !mapEl || mapEl.dataset.mapBootstrapStarted === "1") return;

    mapEl.dataset.mapBootstrapStarted = "1";

    const sharedState = buildSharedState(mapEl, mapNoteEl);
    if (!sharedState) return;

    function tryMount() {
      if (mountGoogleMap(sharedState)) return true;
      if (mountLeafletMap(sharedState)) return true;
      return false;
    }

    function loadLeafletProvider() {
      const leafletCss = SCRIPT_CONFIG.leafletCss || mapEl.dataset.homeMapLeafletCss;
      const leafletCssIntegrity = SCRIPT_CONFIG.leafletCssIntegrity || mapEl.dataset.homeMapLeafletCssIntegrity;
      const leafletJs = SCRIPT_CONFIG.leafletJs || mapEl.dataset.homeMapLeafletJs;
      const leafletJsIntegrity = SCRIPT_CONFIG.leafletJsIntegrity || mapEl.dataset.homeMapLeafletJsIntegrity;
      const clusterCss = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css";
      const clusterDefaultCss = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css";
      const clusterJs = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js";

      if (!leafletCss || !leafletJs) return Promise.reject(new Error("Missing Leaflet assets"));

      return Promise.all([
        loadStylesheet(leafletCss, leafletCssIntegrity),
        loadStylesheet(clusterCss),
        loadStylesheet(clusterDefaultCss),
      ])
        .then(function () {
          return loadScript(leafletJs, leafletJsIntegrity);
        })
        .then(function () {
          return loadScript(clusterJs);
        })
        .then(function () {
          tryMount();
        });
    }

    function loadGoogleProvider() {
      if (!SCRIPT_CONFIG.googleMapsApiKey) return Promise.reject(new Error("Missing Google Maps API key"));
      const clusterJsHref = "https://unpkg.com/@googlemaps/markerclusterer/dist/index.min.js";

      window.kidsMapHomeMapGoogleLoaded = function () {
        const clusterReady = window.markerClusterer ? Promise.resolve() : loadScript(clusterJsHref);
        clusterReady
          .then(function () {
            tryMount();
          })
          .catch(function () {
            tryMount();
          });
      };

      const src =
        "https://maps.googleapis.com/maps/api/js?key=" +
        encodeURIComponent(SCRIPT_CONFIG.googleMapsApiKey) +
        "&loading=async&libraries=marker&language=" +
        encodeURIComponent(SCRIPT_CONFIG.language) +
        "&region=AZ&callback=kidsMapHomeMapGoogleLoaded";

      if (window.google && window.google.maps && window.google.maps.Map) {
        window.kidsMapHomeMapGoogleLoaded();
        return Promise.resolve();
      }
      return loadScript(src);
    }

    let loadStarted = false;
    let fallbackTimer = null;

    function clearFallbackTimer() {
      if (!fallbackTimer) return;
      window.clearTimeout(fallbackTimer);
      fallbackTimer = null;
    }

    function loadAndMount() {
      if (mapEl.dataset.mapInitialized === "1" || loadStarted) return;
      loadStarted = true;

      fallbackTimer = window.setTimeout(function () {
        if (mapEl.dataset.mapInitialized !== "1") {
          renderMapUnavailable(mapEl, mapNoteEl);
        }
      }, 7000);

      if (!SCRIPT_CONFIG.googleMapsApiKey) {
        loadLeafletProvider().catch(function () {
          clearFallbackTimer();
          renderMapUnavailable(mapEl, mapNoteEl);
        });
        return;
      }

      loadGoogleProvider().catch(function () {
        loadLeafletProvider().catch(function () {
          clearFallbackTimer();
          renderMapUnavailable(mapEl, mapNoteEl);
        });
      });
    }

    function triggerLoad() {
      loadAndMount();
      mapSection.removeEventListener("mouseenter", triggerLoad);
      mapSection.removeEventListener("touchstart", triggerLoad);
      window.removeEventListener("scroll", triggerLoad, true);
    }

    window.kidsMapTriggerHomeMapLoad = triggerLoad;

    if (typeof window.IntersectionObserver !== "function") {
      loadAndMount();
      return;
    }

    const observer = new IntersectionObserver(
      function (entries) {
        if (entries.some(function (entry) {
          return entry.isIntersecting;
        })) {
          observer.disconnect();
          triggerLoad();
        }
      },
      {
        rootMargin: "280px 0px",
        threshold: 0.01,
      }
    );

    observer.observe(mapSection);
    mapSection.addEventListener("mouseenter", triggerLoad, { passive: true });
    mapSection.addEventListener("touchstart", triggerLoad, { passive: true, once: true });
    window.addEventListener("scroll", triggerLoad, { passive: true, capture: true, once: true });
    window.setTimeout(triggerLoad, 900);
  }

  startMapBootstrap();
})();
