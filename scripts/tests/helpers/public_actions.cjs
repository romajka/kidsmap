const fs = require('node:fs');
const path = require('node:path');

module.exports = function loadPublicActions(window, root = path.resolve(__dirname, '../../..')) {
  window.matchMedia ??= () => ({matches: false, addEventListener() {}, removeEventListener() {}});
  const script = window.document.createElement('script');
  script.dataset.trackUrl = '/ru/events/track/';
  script.textContent = fs.readFileSync(path.join(root, 'static/js/public_actions.js'), 'utf8');
  window.document.body.appendChild(script);
};
