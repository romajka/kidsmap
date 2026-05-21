(function () {
  const toggleButtons = document.querySelectorAll("[data-password-toggle]");
  if (!toggleButtons.length) return;

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
})();
