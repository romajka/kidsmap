(function () {
  function advancedMarkerAvailable(mapId, map) {
    return Boolean(
      mapId &&
      (!map || (map.getMapCapabilities && map.getMapCapabilities().isAdvancedMarkersAvailable)) &&
      window.google &&
      google.maps &&
      google.maps.marker &&
      google.maps.marker.AdvancedMarkerElement
    );
  }

  function buildMarkerContent(icon, title, cursor) {
    if (!icon || !icon.url) return undefined;
    const image = document.createElement("img");
    image.src = icon.url;
    image.alt = "";
    image.setAttribute("aria-hidden", "true");
    image.draggable = false;
    image.style.display = "block";
    image.style.pointerEvents = "none";
    if (icon.scaledSize) {
      image.style.width = Number(icon.scaledSize.width) + "px";
      image.style.height = Number(icon.scaledSize.height) + "px";
    }
    if (title) image.title = title;
    if (cursor) image.style.cursor = cursor;
    return image;
  }

  function createAdvancedMarker(options, mapId) {
    const content = options.content || buildMarkerContent(options.icon, options.title, options.cursor);
    const marker = new google.maps.marker.AdvancedMarkerElement({
      map: options.map || null,
      position: options.position,
      title: options.title || "",
      zIndex: options.zIndex,
      content: content,
    });

    marker.setMap = function (map) {
      marker.map = map || null;
    };
    marker.getMap = function () { return marker.map || null; };
    marker.getPosition = function () {
      const position = marker.position;
      return position instanceof google.maps.LatLng ? position : new google.maps.LatLng(position);
    };
    marker.setAnimation = function (animation) {
      if (marker.__kidsMapAnimation) {
        marker.__kidsMapAnimation.cancel();
        marker.__kidsMapAnimation = null;
      }
      if (!animation || !content || typeof content.animate !== "function") return;
      marker.__kidsMapAnimation = content.animate(
        [
          { transform: "translateY(0)" },
          { transform: "translateY(-10px)" },
          { transform: "translateY(0)" },
        ],
        { duration: 350, iterations: 2, easing: "ease-out" }
      );
    };
    marker.__kidsMapAdvanced = true;
    marker.__kidsMapMapId = mapId;
    return marker;
  }

  // Public maps opt in; detail maps retain their existing marker behavior.
  function createPublicMarker(options, mapId, ownerMap) {
    const icon = options.icon;
    const width = icon.scaledSize.width, height = icon.scaledSize.height;
    const anchor = icon.anchor || {x: width / 2, y: height};
    const visual = document.createElement("span");
    visual.className = "kidsmap-marker-visual";
    const img = buildMarkerContent(icon, "", options.cursor);
    visual.append(img);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "kidsmap-marker-button";
    button.setAttribute("aria-label", options.title || "");
    button.style.width = width + "px";
    button.style.height = height + "px";
    button.append(visual);
    let marker, overlay;
    const advanced = advancedMarkerAvailable(mapId, ownerMap);
    if (advanced) {
      // Google owns its outer positioning; the inner visual alone animates.
      marker = createAdvancedMarker(Object.assign({}, options, {content: visual}), mapId);
      marker.anchorLeft = (-anchor.x - Math.max(0, 44 - width) / 2) + "px";
      marker.anchorTop = (-anchor.y) + "px";
      marker.gmpClickable = true;
      marker.classList.add("kidsmap-marker-button");
      marker.getElement = () => marker;
    } else {
      // Keep a real Marker for MarkerClusterer. OverlayView only paints its
      // accessible visual and follows map_changed; no second clustering layer.
      marker = new google.maps.Marker(Object.assign({}, options, {
        clickable: false, optimized: false, title: "",
        icon: {url: "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>'), scaledSize: icon.scaledSize, anchor: icon.anchor},
      }));
      // Google creates a second transparent hit target when its Marker has a
      // click listener, even with clickable:false. Keep events on an MVCObject
      // so the accessible visual button is the sole interaction target.
      const clicks = new google.maps.MVCObject();
      const addListener = marker.addListener.bind(marker);
      marker.addListener = (name, handler) => name === 'click'
        ? clicks.addListener(name, handler) : addListener(name, handler);
      overlay = new google.maps.OverlayView();
      overlay.onAdd = function () {
        overlay.getPanes().overlayMouseTarget.append(button);
      };
      overlay.draw = function () {
        const point = overlay.getProjection().fromLatLngToDivPixel(marker.getPosition());
        if (!point) return;
        button.style.left = (point.x - anchor.x - Math.max(0, 44 - width) / 2) + "px";
        button.style.top = (point.y - anchor.y) + "px";
        button.style.zIndex = String((marker.getZIndex() || Math.round(point.y)) + 1);
        const screen = overlay.getProjection().fromLatLngToContainerPixel(marker.getPosition());
        const mapEl = marker.getMap().getDiv();
        const inView = screen && screen.x >= 0 && screen.x <= mapEl.clientWidth && screen.y >= 0 && screen.y <= mapEl.clientHeight;
        button.tabIndex = inView ? 0 : -1;
        button.setAttribute('aria-hidden', String(!inView));
      };
      overlay.onRemove = () => button.remove();
      marker.addListener("map_changed", () => overlay.setMap(marker.getMap()));
      marker.addListener("zindex_changed", () => { if (marker.getMap()) overlay.draw(); });
      button.addEventListener("click", event => {
        event.stopPropagation();
        google.maps.event.trigger(clicks, "click", {domEvent: event, latLng: marker.getPosition()});
      });
      ['pointerdown', 'touchstart', 'dblclick', 'keydown'].forEach(name => button.addEventListener(name, event => event.stopPropagation()));
      ['mouseenter', 'mouseleave'].forEach((name, i) => button.addEventListener(name, () => google.maps.event.trigger(marker, i ? 'mouseout' : 'mouseover')));
      marker.getElement = () => button;
      if (marker.getMap()) overlay.setMap(marker.getMap());
    }
    marker.__kidsMapIcon = icon;
    const root = marker.getElement();
    const baseZ = options.zIndex;
    marker.setSelected = function (selected) {
      root.classList.toggle("is-selected", selected);
      root.setAttribute("aria-pressed", String(selected));
      if (advanced) marker.zIndex = selected ? 2000000 : baseZ;
      else marker.setZIndex(selected ? 2000000 : baseZ);
    };
    marker.setHighlighted = active => root.classList.toggle("is-highlighted", active);
    marker.setAnimation = function () {}; // Public markers never bounce.
    if (options.skipEntrance) visual.classList.add('kidsmap-marker-visual--stable');
    return marker;
  }

  window.kidsMapCreateGoogleMarker = function (options) {
    const config = Object.assign({}, options || {});
    const mapId = String(config.mapId || "").trim();
    delete config.mapId;
    const publicVisual = config.publicVisual;
    const ownerMap = config.ownerMap || config.map;
    delete config.publicVisual;
    delete config.ownerMap;
    if (publicVisual && config.icon) return createPublicMarker(config, mapId, ownerMap);
    delete config.skipEntrance;
    if (advancedMarkerAvailable(mapId)) {
      return createAdvancedMarker(config, mapId);
    }
    return new google.maps.Marker(config);
  };
})();
