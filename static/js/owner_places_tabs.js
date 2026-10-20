/**
 * KidsMap - Owner Dashboard Tabs Interaction
 * Smoothly switches between Places, Events, and Specialists tabs
 * with silky transitions, deep link hash handling, and ARIA accessibility.
 */
(() => {
  'use strict';

  function initOwnerTabs() {
    const tabsNav = document.querySelector('.account-tabs-nav');
    if (!tabsNav) return;

    const pills = Array.from(tabsNav.querySelectorAll('.account-tab-pill'));
    if (!pills.length) return;

    const mainContent = tabsNav.closest('.account-main-content') || tabsNav.parentElement;
    if (mainContent) {
      mainContent.classList.add('js-owner-tabs');
    }

    const panels = Array.from(document.querySelectorAll('.owner-tab-panel'));
    if (!panels.length) return;

    let currentActivePill = null;

    function activateTab(targetIdentifier, updateHash = false, shouldScroll = false) {
      if (!targetIdentifier) return;

      const cleanId = String(targetIdentifier).replace(/^#/, '');

      // Find the corresponding pill
      let targetPill = null;
      for (const pill of pills) {
        const dataTarget = pill.getAttribute('data-tab-target') || '';
        const hrefId = (pill.getAttribute('href') || '').replace(/^#/, '');
        const pillId = pill.id || '';

        if (
          dataTarget === cleanId ||
          hrefId === cleanId ||
          pillId === cleanId ||
          dataTarget.includes(cleanId) ||
          cleanId.includes(dataTarget.replace('owner-panel-', ''))
        ) {
          targetPill = pill;
          break;
        }
      }

      if (!targetPill) {
        targetPill = pills.find(p => p.classList.contains('is-active')) || pills[0];
      }

      const panelId = targetPill.getAttribute('data-tab-target');
      let targetPanel = document.getElementById(panelId);
      if (!targetPanel) {
        const hrefId = (targetPill.getAttribute('href') || '').replace(/^#/, '');
        targetPanel = panels.find(p => p.id === hrefId || p.querySelector('#' + CSS.escape(hrefId)));
      }

      // If already active, just scroll if requested
      if (currentActivePill === targetPill && targetPanel && targetPanel.classList.contains('is-active')) {
        if (shouldScroll) {
          scrollNavIntoView();
        }
        return;
      }

      currentActivePill = targetPill;

      // Update pills
      pills.forEach(pill => {
        const isActive = (pill === targetPill);
        pill.classList.toggle('is-active', isActive);
        pill.setAttribute('aria-selected', isActive ? 'true' : 'false');
        pill.setAttribute('tabindex', isActive ? '0' : '-1');
      });

      // Update panels with clean animation restart
      panels.forEach(panel => {
        const isMatch = (panel === targetPanel);
        if (isMatch) {
          panel.classList.add('is-active');
          panel.removeAttribute('hidden');
          // Trigger smooth CSS animation
          panel.style.animation = 'none';
          void panel.offsetHeight; // force reflow
          panel.style.animation = '';
        } else {
          panel.classList.remove('is-active');
          panel.setAttribute('hidden', '');
        }
      });

      // Update URL hash cleanly without native jump
      if (updateHash) {
        const href = targetPill.getAttribute('href');
        if (href && window.history && window.history.replaceState) {
          window.history.replaceState(null, '', href);
        }
      }

      // Smooth scroll back to tabs if user is scrolled further down
      if (shouldScroll) {
        scrollNavIntoView();
      }
    }

    function scrollNavIntoView() {
      const navRect = tabsNav.getBoundingClientRect();
      // If the top of the tabs navigation is above the top of the viewport
      if (navRect.top < 60) {
        const targetY = window.scrollY + navRect.top - 80;
        window.scrollTo({
          top: Math.max(0, targetY),
          behavior: 'smooth'
        });
      }
    }

    // Attach click and keyboard handlers to tab pills
    pills.forEach((pill, idx) => {
      pill.addEventListener('click', (e) => {
        e.preventDefault();
        const target = pill.getAttribute('data-tab-target') || pill.getAttribute('href');
        activateTab(target, true, true);
        pill.focus();
      });

      // Standard WAI-ARIA tab navigation
      pill.addEventListener('keydown', (e) => {
        let nextIdx = null;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
          e.preventDefault();
          nextIdx = (idx + 1) % pills.length;
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
          e.preventDefault();
          nextIdx = (idx - 1 + pills.length) % pills.length;
        } else if (e.key === 'Home') {
          e.preventDefault();
          nextIdx = 0;
        } else if (e.key === 'End') {
          e.preventDefault();
          nextIdx = pills.length - 1;
        }

        if (nextIdx !== null) {
          const nextPill = pills[nextIdx];
          const target = nextPill.getAttribute('data-tab-target') || nextPill.getAttribute('href');
          activateTab(target, true, false);
          nextPill.focus();
        }
      });
    });

    // Check initial hash from URL or default
    const initialHash = (window.location.hash || '').replace(/^#/, '');
    if (initialHash) {
      activateTab(initialHash, false, false);
    } else {
      const defaultPill = pills.find(p => p.classList.contains('is-active')) || pills[0];
      const target = defaultPill.getAttribute('data-tab-target') || defaultPill.getAttribute('href');
      activateTab(target, false, false);
    }

    // React to browser back/forward buttons
    window.addEventListener('hashchange', () => {
      const currentHash = (window.location.hash || '').replace(/^#/, '');
      if (currentHash) {
        activateTab(currentHash, false, true);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initOwnerTabs);
  } else {
    initOwnerTabs();
  }
})();
