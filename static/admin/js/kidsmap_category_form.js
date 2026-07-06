/* ==========================================================================
   KidsMap - Category form icon preview
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {
  const iconInput = document.getElementById("id_icon");
  const iconUploadInput = document.getElementById("id_icon_upload");
  const preview = document.querySelector("[data-km-category-icon-preview]");
  const glyph = document.querySelector("[data-km-category-icon-glyph]");
  const text = document.querySelector("[data-km-category-icon-text]");

  if (!iconInput || !preview || !glyph || !text) {
    return;
  }

  function setGlyph(node, isImage) {
    glyph.replaceChildren(node);
    glyph.classList.toggle("km-category-icon-preview__glyph--image", Boolean(isImage));
  }

  function render() {
    const uploadedFile = iconUploadInput && iconUploadInput.files && iconUploadInput.files[0];
    if (uploadedFile) {
      preview.classList.remove("is-empty");

      const extension = (uploadedFile.name.split(".").pop() || "").toLowerCase();
      if (["svg", "png", "jpg", "jpeg", "webp"].includes(extension)) {
        const url = URL.createObjectURL(uploadedFile);
        if (extension === "svg") {
          const div = document.createElement("div");
          div.className = "category-mask-icon";
          div.style.width = "24px";
          div.style.height = "24px";
          div.style.backgroundColor = "currentColor";
          div.style.maskImage = `url('${url}')`;
          div.style.webkitMaskImage = `url('${url}')`;
          div.style.maskSize = "contain";
          div.style.webkitMaskSize = "contain";
          div.style.maskRepeat = "no-repeat";
          div.style.webkitMaskRepeat = "no-repeat";
          div.style.maskPosition = "center";
          div.style.webkitMaskPosition = "center";
          setGlyph(div, true);
        } else {
          const image = document.createElement("img");
          image.src = url;
          image.alt = "";
          image.width = 24;
          image.height = 24;
          image.style.objectFit = "contain";
          setGlyph(image, true);
        }
      }
      text.textContent = uploadedFile.name;
      return;
    }

    const raw = iconInput.value.trim();

    if (!raw) {
      preview.classList.add("is-empty");
      const fallback = document.createElement("i");
      fallback.className = "fas fa-image";
      fallback.setAttribute("aria-hidden", "true");
      setGlyph(fallback, false);
      text.textContent = "Нет иконки";
      return;
    }

    preview.classList.remove("is-empty");

    if (raw.includes("/") || raw.includes(".") || raw.startsWith("http")) {
      const fileName = raw.split("/").pop() || raw;
      const url = (raw.startsWith("http") || raw.startsWith("/")) ? raw : "/static/" + raw;
      
      const div = document.createElement("div");
      div.className = "category-mask-icon";
      div.style.width = "24px";
      div.style.height = "24px";
      div.style.backgroundColor = "currentColor";
      div.style.maskImage = `url('${url}')`;
      div.style.webkitMaskImage = `url('${url}')`;
      div.style.maskSize = "contain";
      div.style.webkitMaskSize = "contain";
      div.style.maskRepeat = "no-repeat";
      div.style.webkitMaskRepeat = "no-repeat";
      div.style.maskPosition = "center";
      div.style.webkitMaskPosition = "center";

      setGlyph(div, true);
      text.textContent = fileName.length > 18 ? `${fileName.slice(0, 15)}...` : fileName;
      return;
    }

    const normalized = raw.split(/\s+/).filter(Boolean);
    const classNames = normalized.length > 1 ? normalized : ["fas", raw.startsWith("fa-") ? raw : `fa-${raw}`];

    const icon = document.createElement("i");
    icon.className = classNames.join(" ");
    icon.setAttribute("aria-hidden", "true");
    setGlyph(icon, false);
    text.textContent = raw;
    updateLivePreview();
  }

  function updateLivePreview() {
    const bgInput = document.getElementById("id_color_bg");
    const textInput = document.getElementById("id_color_text");
    const nameRuInput = document.getElementById("id_name_ru");
    const nameAzInput = document.getElementById("id_name_az");
    const nameEnInput = document.getElementById("id_name_en");
    
    const bgVal = bgInput ? bgInput.value : "#FEF3C7";
    const textVal = textInput ? textInput.value : "#B45309";
    
    let nameVal = "Категория";
    if (nameRuInput && nameRuInput.value.trim()) {
      nameVal = nameRuInput.value.trim();
    } else if (nameAzInput && nameAzInput.value.trim()) {
      nameVal = nameAzInput.value.trim();
    } else if (nameEnInput && nameEnInput.value.trim()) {
      nameVal = nameEnInput.value.trim();
    }

    // 1. Update website badge preview
    const previewBadge = document.getElementById("preview-badge");
    if (previewBadge) {
      previewBadge.style.backgroundColor = bgVal;
      previewBadge.style.color = textVal;
      previewBadge.textContent = nameVal;
    }

    // 2. Update map pin preview
    const previewPinContainer = document.getElementById("preview-pin-container");
    if (previewPinContainer) {
      const currentGlyph = document.querySelector("[data-km-category-icon-glyph]");
      let innerIconHtml = "";
      
      if (currentGlyph && currentGlyph.firstElementChild) {
        const child = currentGlyph.firstElementChild;
        const tagName = child.tagName.toLowerCase();
        
        if (tagName === "i") {
          const classes = child.className;
          innerIconHtml = `<i class="${classes}" style="color: ${textVal}; font-size: 14px;"></i>`;
        } else if (child.classList.contains("category-mask-icon")) {
          const maskImg = child.style.maskImage || child.style.webkitMaskImage;
          innerIconHtml = `<div style="width: 14px; height: 14px; background-color: ${textVal}; -webkit-mask-image: ${maskImg}; mask-image: ${maskImg}; -webkit-mask-size: contain; mask-size: contain; -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; -webkit-mask-position: center; mask-position: center;"></div>`;
        } else if (tagName === "img") {
          innerIconHtml = `<img src="${child.src}" style="width: 14px; height: 14px; object-fit: contain;" />`;
        }
      }

      if (!innerIconHtml) {
        innerIconHtml = `<i class="fas fa-image" style="color: ${textVal}; font-size: 14px;"></i>`;
      }

      const pinSvg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="38" height="48" viewBox="0 0 38 48" fill="none" style="display: block; margin: 0 auto;">
          <path d="M19 47C13.5 39 3 31 3 18C3 8.5 10 1 19 1C28 1 35 8.5 35 18C35 31 24.5 39 19 47Z" fill="${textVal}" stroke="white" stroke-width="2.2"/>
          <circle cx="19" cy="18" r="11" fill="${bgVal}" />
        </svg>
        <div class="km-preview-pin-icon-overlay">
          ${innerIconHtml}
        </div>
      `;
      previewPinContainer.innerHTML = pinSvg;
    }
  }

  iconInput.addEventListener("input", render);
  iconInput.addEventListener("change", render);
  if (iconUploadInput) {
    iconUploadInput.addEventListener("change", render);
  }
  render();

  // Dynamic color label update & live preview
  const bgInput = document.getElementById("id_color_bg");
  const bgLabel = document.getElementById("color-bg-val");
  const textInput = document.getElementById("id_color_text");
  const textLabel = document.getElementById("color-text-val");
  const nameRuInput = document.getElementById("id_name_ru");
  const nameAzInput = document.getElementById("id_name_az");
  const nameEnInput = document.getElementById("id_name_en");

  if (bgInput) {
    bgInput.addEventListener("input", function() {
      if (bgLabel) bgLabel.textContent = bgInput.value.toUpperCase();
      updateLivePreview();
    });
    bgInput.addEventListener("change", updateLivePreview);
  }
  
  if (textInput) {
    textInput.addEventListener("input", function() {
      if (textLabel) textLabel.textContent = textInput.value.toUpperCase();
      updateLivePreview();
    });
    textInput.addEventListener("change", updateLivePreview);
  }

  [nameRuInput, nameAzInput, nameEnInput].forEach(inp => {
    if (inp) {
      inp.addEventListener("input", updateLivePreview);
      inp.addEventListener("change", updateLivePreview);
    }
  });

  updateLivePreview();
});
