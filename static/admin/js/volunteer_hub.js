document.addEventListener('DOMContentLoaded', () => {
  const error = document.querySelector('.km-volunteer [role="alert"]');
  if (error) {
    error.setAttribute('tabindex', '-1');
    error.focus();
  }
});
