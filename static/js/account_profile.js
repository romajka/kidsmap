(function () {
  const toggleButtons = document.querySelectorAll("[data-password-toggle]");
  if (toggleButtons.length) {
    toggleButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        const wrap = button.closest(".account-password-wrap");
        const input = wrap ? wrap.querySelector("input") : null;
        if (!input) return;

        const shouldShow = input.type === "password";
        input.type = shouldShow ? "text" : "password";
        button.setAttribute("aria-pressed", shouldShow ? "true" : "false");
      });
    });
  }

  const openBtn = document.getElementById("km-open-staff-deletion-btn");
  const modal = document.getElementById("km-staff-deletion-modal");
  const closeBtn = document.getElementById("km-close-staff-deletion-btn");
  const cancelBtn = document.getElementById("km-cancel-staff-deletion-btn");

  if (modal && openBtn) {
    function closeModal() {
      if (typeof modal.close === "function") {
        modal.close();
      } else {
        modal.removeAttribute("open");
      }
    }

    openBtn.addEventListener("click", function () {
      if (typeof modal.showModal === "function") {
        modal.showModal();
      } else {
        modal.setAttribute("open", "");
      }
    });

    if (closeBtn) {
      closeBtn.addEventListener("click", closeModal);
    }
    if (cancelBtn) {
      cancelBtn.addEventListener("click", closeModal);
    }

    modal.addEventListener("click", function (event) {
      if (event.target === modal) {
        closeModal();
      }
    });
  }

  // Profile avatar uploader
  const avatarInput = document.getElementById("id_avatar");
  const avatarImg = document.getElementById("account-avatar-preview-img");
  const avatarFallback = document.getElementById("account-avatar-preview-fallback");
  const avatarRemoveBtn = document.getElementById("account-avatar-remove-btn");
  const clearAvatarInput = document.getElementById("id_clear_avatar");
  const headerAvatar = document.querySelector(".account-user-card .account-user-avatar");

  if (avatarInput) {
    avatarInput.addEventListener("change", function () {
      const file = this.files && this.files[0];
      if (!file) return;

      if (file.size > 5 * 1024 * 1024) {
        alert("Faylın ölçüsü 5 MB-dan çox olmamalıdır.");
        this.value = "";
        return;
      }

      const reader = new FileReader();
      reader.onload = function (event) {
        if (avatarImg) {
          avatarImg.src = event.target.result;
          avatarImg.style.display = "block";
        }
        if (avatarFallback) {
          avatarFallback.style.display = "none";
        }
        if (avatarRemoveBtn) {
          avatarRemoveBtn.style.display = "inline-flex";
        }
        if (clearAvatarInput) {
          clearAvatarInput.value = "0";
        }
        if (headerAvatar) {
          let headerImg = headerAvatar.querySelector("img");
          if (!headerImg) {
            headerAvatar.innerHTML = '<img class="account-user-avatar__img" alt="">';
            headerImg = headerAvatar.querySelector("img");
          }
          headerImg.src = event.target.result;
        }
      };
      reader.readAsDataURL(file);
    });
  }

  if (avatarRemoveBtn) {
    avatarRemoveBtn.addEventListener("click", function () {
      if (avatarInput) avatarInput.value = "";
      if (clearAvatarInput) clearAvatarInput.value = "1";
      if (avatarImg) {
        avatarImg.src = "";
        avatarImg.style.display = "none";
      }
      if (avatarFallback) {
        avatarFallback.style.display = "flex";
      }
      avatarRemoveBtn.style.display = "none";
      if (headerAvatar) {
        const initials = headerAvatar.getAttribute("data-fallback-initials") || "KM";
        headerAvatar.innerHTML = initials;
      }
    });
  }
})();
