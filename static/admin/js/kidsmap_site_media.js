/* kidsmap_site_media.js */

document.addEventListener("DOMContentLoaded", () => {
    const csrfTokenEl = document.getElementById("km-csrf-token");
    if (!csrfTokenEl) return;
    const csrfToken = csrfTokenEl.value;

    // 1. Gallery Grid uploads (placement-based)
    document.querySelectorAll(".km-gallery-grid").forEach(grid => {
        const placement = grid.dataset.placement;
        const uploadUrl = grid.dataset.uploadUrl;
        const addBtn = grid.querySelector(".km-gallery-add");
        if (!addBtn) return;
        const fileInput = addBtn.querySelector(".km-gallery-file-input");

        // Click handler to trigger file selector
        addBtn.addEventListener("click", (e) => {
            if (e.target !== fileInput) {
                fileInput.click();
            }
        });

        // Input change handler
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                uploadGalleryFiles(fileInput.files, grid, placement, uploadUrl, csrfToken);
                fileInput.value = ""; // Reset file input
            }
        });

        // Drag & Drop visual state helpers
        addBtn.addEventListener("dragover", (e) => {
            e.preventDefault();
            addBtn.style.borderColor = "#009A4E";
            addBtn.style.background = "#F0FDF4";
        });

        ["dragleave", "dragend", "drop"].forEach(eventName => {
            addBtn.addEventListener(eventName, () => {
                addBtn.style.borderColor = "";
                addBtn.style.background = "";
            });
        });

        // Drop handler
        addBtn.addEventListener("drop", (e) => {
            e.preventDefault();
            if (e.dataTransfer.files.length > 0) {
                uploadGalleryFiles(e.dataTransfer.files, grid, placement, uploadUrl, csrfToken);
            }
        });
    });

    // 2. Single Main image uploads (field-based)
    document.querySelectorAll(".km-media-row").forEach(row => {
        const field = row.dataset.field;
        const uploadUrl = row.dataset.uploadUrl;
        const deleteUrl = row.dataset.deleteUrl;
        const uploadBtn = row.querySelector(".km-media-upload-btn");
        const fileInput = row.querySelector(".km-media-file-input");
        if (!uploadBtn || !fileInput) return;

        // Click handler to trigger file selector
        uploadBtn.addEventListener("click", () => {
            fileInput.click();
        });

        // Input change handler
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                uploadSingleFile(fileInput.files[0], row, field, uploadUrl, csrfToken);
                fileInput.value = ""; // Reset
            }
        });

        // Drag & Drop visual state helpers
        row.addEventListener("dragover", (e) => {
            e.preventDefault();
            row.style.outline = "2px dashed #009A4E";
            row.style.background = "#F0FDF4";
        });

        ["dragleave", "dragend", "drop"].forEach(eventName => {
            row.addEventListener(eventName, () => {
                row.style.outline = "";
                row.style.background = "";
            });
        });

        // Drop handler
        row.addEventListener("drop", (e) => {
            e.preventDefault();
            if (e.dataTransfer.files.length > 0) {
                uploadSingleFile(e.dataTransfer.files[0], row, field, uploadUrl, csrfToken);
            }
        });

        row.addEventListener("click", (e) => {
            const deleteBtn = e.target.closest(".km-media-delete-btn");
            if (!deleteBtn) return;
            deleteSingleFile(row, field, deleteUrl, csrfToken);
        });
    });
});

// Helper: Upload gallery image files (placement-based)
function uploadGalleryFiles(files, grid, placement, uploadUrl, csrfToken) {
    const addBtn = grid.querySelector(".km-gallery-add");

    Array.from(files).forEach(file => {
        // Create skeleton card loader
        const loader = document.createElement("div");
        loader.className = "km-gallery-card km-gallery-card-uploading";
        loader.innerHTML = `
            <div class="km-gallery-card-preview" style="background:#F9FAFB; display:flex; align-items:center; justify-content:center; height:120px;">
                <i class="fas fa-spinner fa-spin fa-2x" style="color:#009A4E;"></i>
            </div>
            <div class="km-gallery-card-body" style="padding:10px 12px; display:flex; align-items:center; justify-content:center; border-top: 1px solid #F3F4F6;">
                <span style="font-size:12px; color:#6B7280;">Загрузка...</span>
            </div>
        `;
        // Insert loader before add button
        grid.insertBefore(loader, addBtn);

        // Prepare formData
        const formData = new FormData();
        formData.append("image", file);
        formData.append("placement", placement);

        fetch(uploadUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || `Ошибка сервера (${response.status})`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Construct real card using output data
                const newCard = document.createElement("div");
                newCard.className = "km-gallery-card";
                newCard.innerHTML = `
                    <div class="km-gallery-card-preview">
                        <img src="${data.file.url}" alt="${data.title}">
                    </div>
                    <div class="km-gallery-card-body">
                        <h4 class="km-gallery-card-title" title="${data.title}">${data.title}</h4>
                        <div class="km-gallery-card-footer">
                            <span class="km-gallery-card-size">${data.file.size}</span>
                            <div class="km-gallery-card-actions">
                                <a href="${data.edit_url}" class="km-gallery-card-btn" title="Редактировать"><i class="fas fa-pencil-alt"></i></a>
                                <a href="${data.delete_url}" class="km-gallery-card-btn delete" title="Удалить"><i class="far fa-trash-alt"></i></a>
                            </div>
                        </div>
                    </div>
                `;
                loader.replaceWith(newCard);
            } else {
                throw new Error(data.error || "Неизвестная ошибка");
            }
        })
        .catch(err => {
            loader.remove();
            if (window.kmToast) {
                window.kmToast.error(`Не удалось загрузить файл «${file.name}»: ${err.message}`);
            } else {
                alert(`Не удалось загрузить файл "${file.name}": ${err.message}`);
            }
        });
    });
}

// Helper: Upload single settings image (field-based)
function uploadSingleFile(file, row, field, uploadUrl, csrfToken) {
    const previewContainer = row.querySelector(".km-media-preview");
    const statusContainer = row.querySelector(".km-media-status-wrapper");
    const uploadBtn = row.querySelector(".km-media-upload-btn");

    const origPreview = previewContainer.innerHTML;
    const origStatus = statusContainer.innerHTML;

    // Show loading spinner
    previewContainer.innerHTML = `
        <div style="background:#F9FAFB; display:flex; align-items:center; justify-content:center; width:100%; height:100%;">
            <i class="fas fa-spinner fa-spin fa-2x" style="color:#009A4E;"></i>
        </div>
    `;
    statusContainer.innerHTML = `
        <span class="km-media-status" style="background:#E5E7EB; color:#4B5563; display:inline-flex; align-items:center; gap:4px; padding:4px 8px; border-radius:12px; font-size:12px; font-weight:600;"><i class="fas fa-spinner fa-spin"></i> Загрузка...</span>
    `;
    if (uploadBtn) uploadBtn.disabled = true;

    const formData = new FormData();
    formData.append("image", file);
    formData.append("field", field);

    fetch(uploadUrl, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || `Ошибка сервера (${response.status})`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update preview
            previewContainer.innerHTML = `<img src="${data.file.url}" alt="${file.name}">`;
            // Update status & details
            statusContainer.innerHTML = `
                <span class="km-media-status km-media-status-active"><i class="fas fa-check-circle"></i> Активно</span>
                <span class="km-media-filename" title="${data.file.name}">${data.file.name} &bull; ${data.file.size}</span>
            `;
            ensureDeleteButton(row);
        } else {
            throw new Error(data.error || "Неизвестная ошибка");
        }
    })
    .catch(err => {
        // Revert on error
        previewContainer.innerHTML = origPreview;
        statusContainer.innerHTML = origStatus;
        if (window.kmToast) {
            window.kmToast.error(`Не удалось загрузить файл «${file.name}»: ${err.message}`);
        } else {
            alert(`Не удалось загрузить файл "${file.name}": ${err.message}`);
        }
    })
    .finally(() => {
        if (uploadBtn) uploadBtn.disabled = false;
    });
}

function ensureDeleteButton(row) {
    if (row.querySelector(".km-media-delete-btn")) return;

    const settingsLink = row.querySelector(".km-media-actions .km-btn-link");
    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "km-btn-link km-btn-link-danger km-media-delete-btn";
    deleteBtn.innerHTML = '<i class="far fa-trash-alt"></i> Удалить';

    if (settingsLink) {
        settingsLink.before(deleteBtn);
    } else {
        row.querySelector(".km-media-actions")?.appendChild(deleteBtn);
    }
}

function deleteSingleFile(row, field, deleteUrl, csrfToken) {
    if (!deleteUrl) return;

    var doDelete = function() {
        const deleteBtn = row.querySelector(".km-media-delete-btn");
        if (deleteBtn) {
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Удаление...';
        }

        const formData = new FormData();
        formData.append("field", field);

        fetch(deleteUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.error || `Ошибка сервера (${response.status})`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (!data.success) {
                throw new Error(data.error || "Неизвестная ошибка");
            }
            window.location.reload();
        })
        .catch(err => {
            if (window.kmToast) {
                window.kmToast.error(`Не удалось удалить изображение: ${err.message}`);
            } else {
                alert(`Не удалось удалить изображение: ${err.message}`);
            }
            if (deleteBtn) {
                deleteBtn.disabled = false;
                deleteBtn.innerHTML = '<i class="far fa-trash-alt"></i> Удалить';
            }
        });
    };

    if (window.kmModal) {
        window.kmModal.confirm({
            title: 'Удалить изображение?',
            message: 'Загруженное изображение будет удалено без возможности восстановления.',
            iconTone: 'danger',
            confirmText: 'Удалить',
            cancelText: 'Отмена',
            isAlertDialog: true
        }).then(function(confirmed) {
            if (confirmed) doDelete();
        });
    } else if (window.confirm("Удалить загруженное изображение?")) {
        doDelete();
    }
}
