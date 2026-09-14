/**
 * Staff Profile Tab Navigation & UX enhancements
 */
(function() {
  'use strict';

  function initStaffProfileTabs() {
    const tabList = document.querySelector('.km-staff-profile__tabs');
    if (!tabList) return;

    const tabLinks = tabList.querySelectorAll('[role="tab"]');
    const tabPanels = document.querySelectorAll('.km-staff-tabpanel');
    if (!tabLinks.length || !tabPanels.length) return;

    function activateTab(tabId, updateHash) {
      if (!tabId) return;
      const cleanId = tabId.replace(/^#/, '');
      const targetPanel = document.getElementById(cleanId);
      if (!targetPanel) return;

      tabLinks.forEach(link => {
        const hrefId = (link.getAttribute('href') || '').replace(/^#/, '');
        const isMatch = hrefId === cleanId;
        link.classList.toggle('is-active', isMatch);
        link.setAttribute('aria-selected', isMatch ? 'true' : 'false');
        link.setAttribute('tabindex', isMatch ? '0' : '-1');
      });

      tabPanels.forEach(panel => {
        const isMatch = panel.id === cleanId;
        panel.hidden = !isMatch;
        panel.classList.toggle('is-active', isMatch);
      });

      if (updateHash && window.location.hash !== '#' + cleanId) {
        if (history.replaceState) {
          history.replaceState(null, '', '#' + cleanId);
        } else {
          window.location.hash = '#' + cleanId;
        }
      }
    }

    tabLinks.forEach((tab, index) => {
      tab.addEventListener('click', function(e) {
        e.preventDefault();
        const href = this.getAttribute('href');
        activateTab(href, true);
      });

      tab.addEventListener('keydown', function(e) {
        let newIndex = null;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
          newIndex = (index + 1) % tabLinks.length;
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
          newIndex = (index - 1 + tabLinks.length) % tabLinks.length;
        } else if (e.key === 'Home') {
          newIndex = 0;
        } else if (e.key === 'End') {
          newIndex = tabLinks.length - 1;
        }

        if (newIndex !== null) {
          e.preventDefault();
          tabLinks[newIndex].focus();
          activateTab(tabLinks[newIndex].getAttribute('href'), true);
        }
      });
    });

    window.addEventListener('hashchange', function() {
      if (window.location.hash) {
        activateTab(window.location.hash, false);
      }
    });

    // Determine initial active tab
    const hasFormErrors = document.querySelector('.km-staff-profile__errors, #staff-account .errorlist');
    const initialHash = window.location.hash;

    if (hasFormErrors) {
      activateTab('#staff-account', false);
    } else if (initialHash && document.getElementById(initialHash.replace(/^#/, ''))) {
      activateTab(initialHash, false);
    } else {
      const firstTabHref = tabLinks[0].getAttribute('href');
      activateTab(firstTabHref, false);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStaffProfileTabs);
  } else {
    initStaffProfileTabs();
  }
})();
