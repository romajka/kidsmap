/* ==========================================================================
   KidsMap - Category popup dynamic icon preset, upload and preview handler
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    const iconInput = document.getElementById("id_icon");
    const previewWrapper = document.querySelector(".field-icon .row");

    if (iconInput && previewWrapper) {
        // 1. Setup the Dropzone / Interactive Preview box structure
        // Find existing preview box or create one
        let previewBox = document.querySelector(".icon-preview-box");
        if (!previewBox) {
            previewBox = document.createElement("div");
            previewBox.className = "icon-preview-box";
            previewWrapper.appendChild(previewBox);
        }

        // Render dropzone / preview interior HTML
        previewBox.innerHTML = `
            <span class="icon-preview-box__title">Иконка</span>
            <div class="icon-preview-box__icon-wrapper" id="km-icon-wrapper">
                <i id="km-icon-preview-element" class="fas fa-image"></i>
            </div>
            <p class="icon-preview-box__upload-text" id="km-upload-text">Перетащите SVG/PNG сюда или кликните</p>
            <p class="icon-preview-box__upload-subtext" id="km-upload-subtext">Рекомендуется SVG, до 50 КБ</p>
            <button type="button" class="icon-preview-box__clear-btn" id="km-clear-icon-btn" style="display: none;">Сбросить</button>
            <input type="file" id="km-icon-file-input" accept=".svg,.png,.jpg,.jpeg,.webp" style="display: none;" />
        `;

        const iconWrapper = document.getElementById("km-icon-wrapper");
        const previewIcon = document.getElementById("km-icon-preview-element");
        const uploadText = document.getElementById("km-upload-text");
        const uploadSubtext = document.getElementById("km-upload-subtext");
        const clearBtn = document.getElementById("km-clear-icon-btn");
        const fileInput = document.getElementById("km-icon-file-input");

        // 2. Setup the Presets grid
        const presets = [
            { cls: "icons/categories/sports.svg", name: "Спорт" },
            { cls: "img/icon/cooliocns SVG/Edit/Swatches_Palette.svg", name: "Искусство" },
            { cls: "icons/categories/music.svg", name: "Музыка" },
            { cls: "img/icon/cooliocns SVG/Interface/Book_Open.svg", name: "Образование" },
            { cls: "img/icon/cooliocns SVG/System/Code.svg", name: "Технологии" },
            { cls: "icons/categories/camp.svg", name: "Лагерь" },
            { cls: "img/icon/cooliocns SVG/Interface/Ticket_Voucher.svg", name: "Развлечения" },
            { cls: "icons/categories/early-development.svg", name: "Развитие" },
            { cls: "img/icon/cooliocns SVG/Environment/Puzzle.svg", name: "Интеллект" },
            { cls: "img/icon/cooliocns SVG/Interface/Heart_01.svg", name: "Поддержка" },
            { cls: "icons/categories/dance.svg", name: "Танцы" }
        ];

        // Create presets container under the icon input field
        const iconFieldDiv = document.querySelector(".field-icon .field-icon");
        if (iconFieldDiv) {
            const presetsContainer = document.createElement("div");
            presetsContainer.className = "km-presets-container";
            presetsContainer.innerHTML = `
                <span class="km-presets-label">Выберите готовую иконку:</span>
                <div class="km-presets-grid" id="km-presets-grid-el"></div>
            `;
            iconFieldDiv.appendChild(presetsContainer);

            const gridEl = document.getElementById("km-presets-grid-el");
            presets.forEach(p => {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.className = "km-preset-btn";
                btn.title = p.name;
                btn.innerHTML = `<div class="category-mask-icon" style="width: 24px; height: 24px; background-color: currentColor; mask-image: url('/static/${p.cls}'); -webkit-mask-image: url('/static/${p.cls}'); mask-size: contain; -webkit-mask-size: contain; mask-repeat: no-repeat; -webkit-mask-repeat: no-repeat; mask-position: center; -webkit-mask-position: center;"></div>`;
                btn.dataset.class = p.cls;

                btn.addEventListener("click", function() {
                    iconInput.value = p.cls;
                    // Trigger input event to update preview
                    iconInput.dispatchEvent(new Event("input"));
                });

                gridEl.appendChild(btn);
            });
        }

        // 3. Preview Update logic
        function updateIconPreview() {
            const val = iconInput.value.trim();
            
            // Remove active classes from all preset buttons
            document.querySelectorAll(".km-preset-btn").forEach(btn => {
                if (val && btn.dataset.class === val) {
                    btn.classList.add("is-active");
                } else {
                    btn.classList.remove("is-active");
                }
            });

            if (!val) {
                // Empty state
                iconWrapper.innerHTML = `<i id="km-icon-preview-element" class="fas fa-image" style="color: #9ca3af !important;"></i>`;
                uploadText.textContent = "Перетащите SVG/PNG сюда или кликните";
                uploadSubtext.style.display = "block";
                clearBtn.style.display = "none";
                return;
            }

            // Check if it's an uploaded file (contains /media/ or /static/ or extension suffix)
            const isFile = val.includes("/") || val.includes(".") || val.startsWith("http");

            if (isFile) {
                // File/URL state
                const filename = val.substring(val.lastIndexOf("/") + 1);
                const url = (val.startsWith("http") || val.startsWith("/")) ? val : "/static/" + val;
                iconWrapper.innerHTML = `<div class="category-mask-icon" style="width: 48px; height: 48px; background-color: var(--brand-jet); mask-image: url('${url}'); -webkit-mask-image: url('${url}'); mask-size: contain; -webkit-mask-size: contain; mask-repeat: no-repeat; -webkit-mask-repeat: no-repeat; mask-position: center; -webkit-mask-position: center;"></div>`;
                uploadText.textContent = filename.length > 20 ? filename.substring(0, 17) + "..." : filename;
                uploadSubtext.style.display = "none";
                clearBtn.style.display = "block";
            } else {
                // FontAwesome class state
                iconWrapper.innerHTML = `<i id="km-icon-preview-element" class=""></i>`;
                const iEl = document.getElementById("km-icon-preview-element");
                val.split(/\s+/).forEach(cls => {
                    if (cls) iEl.classList.add(cls);
                });
                uploadText.textContent = "Иконка: " + val;
                uploadSubtext.style.display = "none";
                clearBtn.style.display = "block";
            }
        }

        // Listen for manual user input on field
        iconInput.addEventListener("input", updateIconPreview);
        updateIconPreview();

        // 4. Reset/Clear action
        clearBtn.addEventListener("click", function(e) {
            e.stopPropagation(); // prevent triggering upload dialog click
            iconInput.value = "";
            iconInput.dispatchEvent(new Event("input"));
        });

        // 5. Drag & Drop Upload logic
        // Click to upload
        previewBox.addEventListener("click", () => fileInput.click());

        // File selection handler
        fileInput.addEventListener("change", function() {
            if (fileInput.files && fileInput.files[0]) {
                handleFileUpload(fileInput.files[0]);
            }
        });

        // Drag events
        ["dragenter", "dragover"].forEach(eventName => {
            previewBox.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                previewBox.classList.add("dragover");
            }, false);
        });

        ["dragleave", "drop"].forEach(eventName => {
            previewBox.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                previewBox.classList.remove("dragover");
            }, false);
        });

        previewBox.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files && files[0]) {
                handleFileUpload(files[0]);
            }
        }, false);

        // Resolve upload url relative to current page
        function getUploadUrl() {
            let path = window.location.pathname;
            if (path.endsWith("/")) {
                path = path.slice(0, -1);
            }
            if (path.includes("/add")) {
                return path.replace(/\/add$/, "/upload-icon/");
            } else if (path.includes("/change")) {
                // format is .../category/ID/change
                const basePath = path.replace(/\/change$/, "");
                return basePath.substring(0, basePath.lastIndexOf("/")) + "/upload-icon/";
            } else {
                return "/admin/catalog/category/upload-icon/"; // fallback
            }
        }

        // Upload handler
        function handleFileUpload(file) {
            // Show loading spinner
            iconWrapper.innerHTML = `<div class="km-upload-spinner"></div>`;
            uploadText.textContent = "Загрузка...";
            uploadSubtext.style.display = "none";
            clearBtn.style.display = "none";

            const formData = new FormData();
            formData.append("file", file);

            // Fetch CSRF Token
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            const csrfToken = csrfInput ? csrfInput.value : "";

            const uploadUrl = getUploadUrl();

            fetch(uploadUrl, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": csrfToken
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.error || "Ошибка загрузки"); });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    iconInput.value = data.path;
                    iconInput.dispatchEvent(new Event("input"));
                } else {
                    if (window.kmToast) {
                        window.kmToast.error(data.error || "Не удалось загрузить файл.");
                    } else {
                        alert(data.error || "Не удалось загрузить файл.");
                    }
                    updateIconPreview();
                }
            })
            .catch(error => {
                if (window.kmToast) {
                    window.kmToast.error("Ошибка: " + error.message);
                } else {
                    alert("Ошибка: " + error.message);
                }
                updateIconPreview();
            });
        }
    }
});
