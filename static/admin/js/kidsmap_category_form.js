/* ==========================================================================
   KidsMap - Category form icon preview
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {
  const iconInput = document.getElementById("id_icon");
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
  }

  iconInput.addEventListener("input", render);
  iconInput.addEventListener("change", render);
  render();
});
