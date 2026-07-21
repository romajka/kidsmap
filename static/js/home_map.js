(function () {
  const DEFAULT_CENTER = { lat: 40.4093, lng: 49.8671 };
  const DEFAULT_ZOOM = 11;
  const BRAND_MARKER_COLOR = "#136f38";
  const BRAND_MARKER_INNER_COLOR = "#a8d59b";
  const LEAFLET_DEFAULTS = {
    cssHref: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
    cssIntegrity: "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=",
    jsHref: "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
    jsIntegrity: "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=",
  };

  const SCRIPT_CONFIG = (function () {
    const scriptEl = document.currentScript;
    if (!scriptEl) return {};

    return {
      googleMapsApiKey: (scriptEl.dataset.homeMapGoogleKey || "").trim(),
      leafletCssHref: (scriptEl.dataset.homeMapLeafletCss || LEAFLET_DEFAULTS.cssHref).trim(),
      leafletCssIntegrity: (scriptEl.dataset.homeMapLeafletCssIntegrity || LEAFLET_DEFAULTS.cssIntegrity).trim(),
      leafletJsHref: (scriptEl.dataset.homeMapLeafletJs || LEAFLET_DEFAULTS.jsHref).trim(),
      leafletJsIntegrity: (scriptEl.dataset.homeMapLeafletJsIntegrity || LEAFLET_DEFAULTS.jsIntegrity).trim(),
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

  function placeMatchesFilters(place, filters) {
    if (filters.category && place.category_code !== filters.category) {
      return false;
    }

    if (filters.district) {
      const placeDist = normalizeValue(place.district || place.district_label);
      if (filters.district === "baku") {
        if (placeDist !== "baku" && !placeDist.startsWith("baku_")) {
          return false;
        }
      } else if (placeDist !== filters.district) {
        return false;
      }
    }

    if (filters.metro && normalizeValue(place.metro) !== filters.metro) {
      return false;
    }

    if (filters.age) {
      const selectedAge = Number(filters.age);
      const ageFrom = place.age_from === null || place.age_from === undefined ? null : Number(place.age_from);
      const ageTo = place.age_to === null || place.age_to === undefined ? null : Number(place.age_to);

      if ((ageFrom !== null && selectedAge < ageFrom) || (ageTo !== null && selectedAge > ageTo)) {
        return false;
      }

      if (ageFrom === null && ageTo === null) {
        return false;
      }
    }

    if (filters.query && !normalizeSearch(place.search_text || place.name).includes(filters.query)) {
      return false;
    }

    return true;
  }

  function renderPopupContent(place, detailsLabel) {
    const image = place.image_url
      ? '<a class="home-map-popup-thumb-link" href="' +
        escapeHtml(place.url || "") +
        '">' +
        '<img class="home-map-popup-thumb" src="' +
        escapeHtml(place.image_url) +
        '" alt="' +
        escapeHtml(place.name || "") +
        '" loading="lazy" decoding="async" />' +
        "</a>"
      : "";

    const addressHtml = place.address
      ? '<div class="home-map-popup-info-row">' +
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="popup-info-icon"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>' +
        '<span class="home-map-popup-info-text">' + escapeHtml(place.address) + '</span>' +
        '</div>'
      : "";

    const scheduleHtml = place.schedule
      ? '<div class="home-map-popup-info-row">' +
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="popup-info-icon"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>' +
        '<span class="home-map-popup-info-text">' + escapeHtml(place.schedule) + '</span>' +
        '</div>'
      : "";

    const phoneHtml = place.phone
      ? '<div class="home-map-popup-info-row">' +
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="popup-info-icon"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>' +
        '<a href="tel:' + escapeHtml(place.phone) + '" class="home-map-popup-phone-link">' + escapeHtml(place.phone) + '</a>' +
        '</div>'
      : "";

    return (
      '<div class="home-map-popup">' +
      image +
      '<div class="home-map-popup-body">' +
      '<span class="home-map-popup-category" style="color: ' + escapeHtml(place.category_color_text || "var(--brand-turf)") + ';">' +
      escapeHtml(place.category) +
      "</span>" +
      '<strong class="home-map-popup-title">' +
      escapeHtml(place.name) +
      "</strong>" +
      '<div class="home-map-popup-details">' +
      addressHtml +
      scheduleHtml +
      phoneHtml +
      '</div>' +
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
    CAMP: '<path d="m3 21 8.5-16.5a1 1 0 0 1 1 0L21 21"></path><path d="m8 12 4 8"></path><path d="m16 12-4 8"></path>',
    SPRT: '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7c0 6 4 9 6 9s6-3 6-9V2Z"></path>',
    MUS: '<path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle>',
    TECH: '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>',
    EDU: '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>',
    ART: '<circle cx="13.5" cy="6.5" r=".5"></circle><circle cx="17.5" cy="10.5" r=".5"></circle><circle cx="8.5" cy="7.5" r=".5"></circle><circle cx="6.5" cy="12.5" r=".5"></circle><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"></path>',
    FUN: '<rect x="2" y="6" width="20" height="12" rx="2"></rect><path d="M6 12h4"></path><path d="M8 10v4"></path><circle cx="15" cy="13" r="1"></circle><circle cx="18" cy="11" r="1"></circle>',
    'early-development': '<path d="M12 22V12"></path><path d="M12 12C12 12 10 6 5 6C5 6 4 10 12 12Z"></path><path d="M12 16C12 16 15 10 19 10C19 10 20 14 12 16Z"></path>',
    dance: '<circle cx="12" cy="4" r="2" /><path d="M6 10c2-3 4-4 6-4s4 1 6 4" /><path d="M12 8c-3 4-5 7-6 11h12c-1-4-3-7-6-11z" /><path d="M10 19v3" /><path d="M14 19v3" />',
    'intellect-skills': '<path d="M20 7H17.8486C17.3511 7 17 6.49751 17 6C17 4.34315 15.6569 3 14 3C12.3431 3 11 4.34315 11 6C11 6.49751 10.6488 7 10.1513 7H8C7.44771 7 7 7.44772 7 8V10.1513C7 10.6488 6.49751 11 6 11C4.34315 11 3 12.3431 3 14C3 15.6569 4.34315 17 6 17C6.49751 17 7 17.3511 7 17.8486V20C7 20.5523 7.44771 21 8 21L20 21C20.5523 21 21 20.5523 21 20V17.8486C21 17.3511 20.4975 17 20 17C18.3431 17 17 15.6569 17 14C17 12.3431 18.3431 11 20 11C20.4975 11 21 10.6488 21 10.1513L21 8C21 7.44772 20.5523 7 20 7Z"/>',
    PARK: '<path d="M10 22v-6.5M18 22v-5M10 15.5a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9Z" /><path d="M18 17a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7Z" />',
    BEACH: '<path d="M4 11c1.8-3.7 5.1-6 8-6s6.2 2.3 8 6" /><path d="M12 5v14" /><path d="M8 11c.8-2.3 2.2-4.2 4-6 1.8 1.8 3.2 3.7 4 6" /><path d="M4 18c1.4-1 2.8-.5 4 0s2.6 1 4 0 2.8-1 4 0 2.6 1 4 0" />',
    WATERPARK: '<path d="M4 17V3h3"></path><path d="M4 7h3M4 11h3M4 15h3"></path><path d="M7 3c1.5 0 3 .5 4 2l4 6c1 1.5 2.5 2.5 4.5 2.5h2.5"></path><path d="M2 20c1.5-1 3.5-1 5 0s3.5 1 5 0s3.5-1 5 0s3.5 1 5 0"></path>',
    ZOO: '<circle cx="8" cy="8" r="2"></circle><circle cx="16" cy="8" r="2"></circle><circle cx="6" cy="15" r="1.5"></circle><circle cx="18" cy="15" r="1.5"></circle><path d="M8.5 18.5c.8-2.2 2.1-3.5 3.5-3.5s2.7 1.3 3.5 3.5c.5 1.3-.4 2.5-1.8 2.5h-3.4c-1.4 0-2.3-1.2-1.8-2.5Z"></path>'
  };

  function buildMarkerGlyph(place, colorText) {
    const categoryCode = place && place.category_code;
    const iconSvgContent = CATEGORY_SVGS[categoryCode] || '<rect x="3" y="3" width="7" height="7" rx="1.5"></rect><rect x="14" y="3" width="7" height="7" rx="1.5"></rect><rect x="14" y="14" width="7" height="7" rx="1.5"></rect><rect x="3" y="14" width="7" height="7" rx="1.5"></rect>';
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

    if (!validPlaces.length) {
      renderFallback(mapEl, mapNoteEl);
      return null;
    }

    return {
      places: validPlaces,
      detailsLabel: mapEl.dataset.detailsLabel || "Details",
      mapEl: mapEl,
      mapNoteEl: mapNoteEl,
    };
  }

  function setMapNote(mapNoteEl, emptyLabel, hasVisiblePlaces) {
    if (!mapNoteEl) return;
    mapNoteEl.hidden = hasVisiblePlaces;
    mapNoteEl.textContent = hasVisiblePlaces ? "" : emptyLabel || "";
  }

  function bindFilterListeners(updateMap) {
    const form = document.querySelector("[data-home-map-filter-form]");
    if (!form || typeof updateMap !== "function") return;

    let searchTimer = null;
    const queryInput = form.querySelector('[name="q"]');
    const districtInput = form.querySelector('[name="district"]');
    const districtVisibleInput = form.querySelector("[data-home-district-input]");
    const districtOptions = getDistrictOptions(form);
    const categorySelect = form.querySelector('select[name="category"]');
    const ageInput = getAgeInput(form);
    const ageButtons = getAgeButtons(form);

    function scheduleUpdate() {
      if (searchTimer) {
        window.clearTimeout(searchTimer);
      }
      searchTimer = window.setTimeout(updateMap, 120);
    }

    if (queryInput) {
      queryInput.addEventListener("input", scheduleUpdate);
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

        form.addEventListener("submit", function () {
          const resolvedOption = resolveDistrictValue(districtVisibleInput.value, districtOptions);
          districtInput.value = resolvedOption ? resolvedOption.value : "";
          districtVisibleInput.value = resolvedOption ? resolvedOption.label : "";
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

    if (ageInput && ageButtons.length) {
      syncAgeButtons(form);

      ageButtons.forEach(function (button) {
        button.addEventListener("click", function () {
          const nextValue = normalizeValue(button.dataset.ageValue);
          const currentValue = normalizeValue(ageInput.value);
          setAgeValue(form, currentValue === nextValue ? "" : nextValue);
          updateMap();
        });
      });
    }
  }

  function mountGoogleMap(sharedState) {
    if (!window.google || !window.google.maps || !sharedState) return false;

    const { mapEl, mapNoteEl, places, detailsLabel } = sharedState;
    if (mapEl.dataset.mapInitialized === "1") return true;

    mapEl.dataset.mapInitialized = "1";

    const map = new google.maps.Map(mapEl, {
      center: DEFAULT_CENTER,
      zoom: DEFAULT_ZOOM,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
      gestureHandling: "cooperative",
    });
    const infoWindow = new google.maps.InfoWindow();

    // ── Interaction tracking ────────────────────────────────────────────────
    let userInteracted = false;
    let isProgrammatic = false;
    let syncPending = false;

    map.addListener("dragstart", function () {
      userInteracted = true;
    });
    map.addListener("zoom_changed", function () {
      if (!isProgrammatic) {
        userInteracted = true;
      }
    });

    function programmaticUpdate(action) {
      isProgrammatic = true;
      action();
      window.setTimeout(function () {
        isProgrammatic = false;
      }, 100);
    }

    // ── Cluster Group ────────────────────────────────────────────────────────
    let markerCluster = null;
    if (window.markerClusterer && window.markerClusterer.MarkerClusterer && !window.markerClusterer.dummy) {
      markerCluster = new window.markerClusterer.MarkerClusterer({
        map: map,
        markers: [],
        renderer: {
          render: function (cluster, stats, mapInstance) {
            const count = cluster.count;
            const position = cluster.position;
            const svg = buildGoogleClusterSvg(count);
            return new google.maps.Marker({
              position: position,
              icon: {
                url: "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(svg),
                scaledSize: new google.maps.Size(54, 54),
                anchor: new google.maps.Point(27, 27),
              },
              zIndex: Number(google.maps.Marker.MAX_ZINDEX) + count,
            });
          }
        },
        onClusterClick: function (event, cluster, mapInstance) {
          userInteracted = true;
          const bounds = new google.maps.LatLngBounds();
          const markers = cluster.markers || (cluster.getMarkers ? cluster.getMarkers() : []);
          if (markers && markers.length > 0) {
            markers.forEach(function (m) {
              bounds.extend(m.getPosition());
            });
            if (bounds.getNorthEast().equals(bounds.getSouthWest())) {
              mapInstance.setCenter(bounds.getCenter());
              mapInstance.setZoom(16);
            } else {
              mapInstance.fitBounds(bounds, 80);
            }
          }
        }
      });
    }

    // ── Build markers ───────────────────────────────────────────────────────
    const markerItems = [];

    places.forEach(function (place) {
      if (!hasValidCoordinates(place)) return;

      const position = { lat: place.lat, lng: place.lng };
      const marker = new google.maps.Marker({
        position: position,
        title: place.name || "",
        icon: buildGoogleMarkerIcon(place),
      });

      marker.addListener("click", function () {
        infoWindow.setContent(renderPopupContent(place, detailsLabel));
        infoWindow.open({
          anchor: marker,
          map: map,
        });
      });

      markerItems.push({
        marker: marker,
        place: place,
        position: position,
      });
    });

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
      const visibleItems = [];
      const bounds = new google.maps.LatLngBounds();

      infoWindow.close();

      if (markerCluster) {
        markerCluster.clearMarkers();
      }

      const activeMarkers = [];
      markerItems.forEach(function (item) {
        if (!hasValidCoordinates(item.place)) return;
        if (placeMatchesFilters(item.place, filters)) {
          visibleItems.push(item);
          bounds.extend(item.position);
          if (markerCluster) {
            activeMarkers.push(item.marker);
          } else {
            item.marker.setMap(map);
          }
        } else {
          if (!markerCluster) {
            item.marker.setMap(null);
          }
        }
      });

      if (markerCluster && activeMarkers.length) {
        markerCluster.addMarkers(activeMarkers);
      }

      // No results
      if (!visibleItems.length) {
        userInteracted = false;
        programmaticUpdate(function () {
          map.setCenter(DEFAULT_CENTER);
          map.setZoom(DEFAULT_ZOOM);
        });
        setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", false);
        return;
      }

      setMapNote(mapNoteEl, mapEl.dataset.emptyLabel || "", true);

      // Don't override zoom after user has manually navigated
      if (userInteracted) return;

      // No active filters → show default Baku overview
      if (!hasActiveFilters(filters)) {
        programmaticUpdate(function () {
          map.setCenter(DEFAULT_CENTER);
          map.setZoom(DEFAULT_ZOOM);
        });
        return;
      }

      // Single filtered result
      if (visibleItems.length === 1) {
        programmaticUpdate(function () {
          map.setCenter(visibleItems[0].position);
          map.setZoom(15);
        });
        return;
      }

      // Multiple filtered results → fitBounds
      const maxZoom = allInBaku(visibleItems) ? 13 : 14;
      window.setTimeout(function () {
        if (userInteracted) return;
        programmaticUpdate(function () {
          map.setOptions({ maxZoom: maxZoom });
          map.fitBounds(bounds, { top: 48, right: 48, bottom: 48, left: 48 });
          google.maps.event.addListenerOnce(map, "idle", function () {
            map.setOptions({ maxZoom: null });
          });
        });
      }, 80);
    }

    // Filter change: reset userInteracted so bounds recalculate for new results
    function syncVisibleMarkersFromFilter() {
      userInteracted = false;
      syncVisibleMarkers();
    }

    bindFilterListeners(syncVisibleMarkersFromFilter);
    syncVisibleMarkers();

    window.setTimeout(function () {
      if (window.google && window.google.maps) {
        google.maps.event.trigger(map, "resize");
      }
    }, 0);

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

    places.forEach(function (place) {
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

      marker.bindPopup(renderPopupContent(place, mapEl.dataset.detailsLabel || "Details"));
      markerItems.push({ marker: marker, place: place, position: position });
    });

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
        if (placeMatchesFilters(item.place, filters)) {
          layersToAdd.push(item.marker);
          visibleItems.push(item);
        }
      });

      if (layersToAdd.length) {
        markerClusterGroup.addLayers(layersToAdd);
        markerClusterGroup.refreshClusters();
      }

      markerClusterGroup.off("clusterclick", handleHomeClusterClick);
      markerClusterGroup.on("clusterclick", handleHomeClusterClick);

      // No results
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
      syncVisibleMarkers();
    }

    bindFilterListeners(syncVisibleMarkersFromFilter);

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

    mapEl.addEventListener("mouseenter", function () { map.scrollWheelZoom.enable(); });
    mapEl.addEventListener("mouseleave", function () { map.scrollWheelZoom.disable(); });

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

    function loadGoogleProvider() {
      if (!SCRIPT_CONFIG.googleMapsApiKey) return Promise.reject(new Error("Missing Google Maps API key"));
      const clusterJsHref = "https://unpkg.com/@googlemaps/markerclusterer/dist/index.min.js";

      window.kidsMapHomeMapGoogleLoaded = function () {
        loadScript(clusterJsHref)
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
        "&callback=kidsMapHomeMapGoogleLoaded";

      return loadScript(src);
    }

    function loadLeafletProvider() {
      const clusterCssHref = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css";
      const clusterDefaultCssHref = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css";
      const clusterJsHref = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js";

      return loadStylesheet(SCRIPT_CONFIG.leafletCssHref, SCRIPT_CONFIG.leafletCssIntegrity).then(function () {
        return loadScript(SCRIPT_CONFIG.leafletJsHref, SCRIPT_CONFIG.leafletJsIntegrity);
      }).then(function () {
        return Promise.all([
          loadStylesheet(clusterCssHref),
          loadStylesheet(clusterDefaultCssHref),
        ]);
      }).then(function () {
        return loadScript(clusterJsHref);
      }).then(function () {
        tryMount();
      });
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
          renderFallback(mapEl, mapNoteEl);
        }
      }, 5000);

      if (SCRIPT_CONFIG.googleMapsApiKey) {
        loadGoogleProvider().catch(function () {
          clearFallbackTimer();
          renderFallback(mapEl, mapNoteEl);
        });
        return;
      }

      loadLeafletProvider().catch(function () {
        clearFallbackTimer();
        renderFallback(mapEl, mapNoteEl);
      });
    }

    function triggerLoad() {
      loadAndMount();
      mapSection.removeEventListener("mouseenter", triggerLoad);
      mapSection.removeEventListener("touchstart", triggerLoad);
      window.removeEventListener("scroll", triggerLoad, true);
    }

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
