(function () {
  function advancedMarkerAvailable(mapId) {
    return Boolean(
      mapId &&
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

  window.kidsMapCreateGoogleMarker = function (options) {
    const config = Object.assign({}, options || {});
    const mapId = String(config.mapId || "").trim();
    delete config.mapId;
    if (advancedMarkerAvailable(mapId)) {
      return createAdvancedMarker(config, mapId);
    }
    return new google.maps.Marker(config);
  };
})();
