/* Progressive enhancement: native scrolling remains available on every device. */
(() => {
  'use strict';
  document.querySelectorAll('[data-places-rail]').forEach((rail) => {
    const viewport = rail.querySelector('[data-rail-viewport]');
    const track = rail.querySelector('[data-rail-track]');
    const toggle = rail.querySelector('[data-rail-toggle]');
    const prevBtn = rail.querySelector('[data-rail-prev]');
    const nextBtn = rail.querySelector('[data-rail-next]');
    const progressThumb = rail.querySelector('[data-rail-progress-thumb]');
    const progressLoopThumb = rail.querySelector('[data-rail-progress-thumb-loop]');
    const originals = Array.from(track.children);
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    let paused = false;
    let hovered = false;
    let visible = false;
    let automatic = false;
    let isDragging = false;
    let isPointerDown = false;
    let hasMoved = false;
    let userInteracting = false;
    let resumeTimeout = null;
    let startX = 0;
    let startScrollLeft = 0;
    let activePointerId = null;
    let period = 0;
    let frame = 0;
    let inertiaFrame = 0;
    let lastTime = 0;
    let offset = 0;
    let lastWidth = 0;
    let lastMoveX = 0;
    let lastMoveTime = 0;
    let velocity = 0;

    function canMove() {
      const isKeyboardFocused = document.activeElement &&
        viewport.contains(document.activeElement) &&
        (typeof document.activeElement.matches === 'function' ? document.activeElement.matches(':focus-visible') : false);

      return automatic &&
        !paused &&
        !userInteracting &&
        !hovered &&
        !isPointerDown &&
        !isDragging &&
        !inertiaFrame &&
        visible &&
        !document.hidden &&
        !isKeyboardFocused;
    }

    function scheduleAutoResume(delay = 1800) {
      if (resumeTimeout) clearTimeout(resumeTimeout);
      if (paused || !automatic) return;
      resumeTimeout = setTimeout(() => {
        userInteracting = false;
        hovered = false;
        sync();
      }, delay);
    }

    function updateProgress() {
      if (!progressThumb) return;
      const trackEl = progressThumb.parentElement;
      const trackWidth = trackEl ? trackEl.clientWidth : 280;
      const thumbWidth = progressThumb.clientWidth || (trackWidth * 0.25);

      if (period > 0) {
        // Continuous, infinitely cycling progress without sharp snaps
        const normScroll = ((viewport.scrollLeft % period) + period) % period;
        const ratio = normScroll / period;
        const pos = ratio * trackWidth;

        progressThumb.style.transform = `translate3d(${pos.toFixed(2)}px, 0, 0)`;

        if (progressLoopThumb) {
          if (pos + thumbWidth > trackWidth) {
            // Primary thumb is exiting right edge; loop thumb simultaneously enters from left edge
            const loopPos = pos - trackWidth;
            progressLoopThumb.style.display = '';
            progressLoopThumb.style.transform = `translate3d(${loopPos.toFixed(2)}px, 0, 0)`;
          } else if (pos < 0) {
            // Scrolling backwards; loop thumb enters from right edge
            const loopPos = pos + trackWidth;
            progressLoopThumb.style.display = '';
            progressLoopThumb.style.transform = `translate3d(${loopPos.toFixed(2)}px, 0, 0)`;
          } else {
            progressLoopThumb.style.display = 'none';
          }
        }
      } else {
        const max = viewport.scrollWidth - viewport.clientWidth;
        const travel = Math.max(0, trackWidth - thumbWidth);
        const ratio = max > 0 ? Math.min(1, Math.max(0, viewport.scrollLeft / max)) : 0;
        progressThumb.style.transform = `translate3d(${(ratio * travel).toFixed(2)}px, 0, 0)`;
        if (progressLoopThumb) progressLoopThumb.style.display = 'none';
      }
    }

    function tick(time) {
      frame = 0;
      if (!canMove()) { lastTime = 0; return; }
      if (lastTime) {
        offset = (offset + Math.min(time - lastTime, 64) * 0.022) % period;
        viewport.scrollLeft = offset;
        updateProgress();
      }
      lastTime = time;
      frame = requestAnimationFrame(tick);
    }

    function sync() {
      if (toggle) {
        toggle.querySelector('[data-rail-toggle-label]').textContent = paused ? toggle.dataset.resumeLabel : toggle.dataset.pauseLabel;
        toggle.querySelector('[data-rail-toggle-icon]').textContent = paused ? '▷' : 'Ⅱ';
      }
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
      lastTime = 0;
      offset = period ? ((viewport.scrollLeft % period) + period) % period : viewport.scrollLeft;
      updateProgress();
      if (canMove()) frame = requestAnimationFrame(tick);
    }

    function rebuild() {
      track.querySelectorAll('[data-rail-copy]').forEach((copy) => copy.remove());
      automatic = !reduced.matches && originals.length > 1;
      rail.classList.toggle('is-automatic', automatic);
      if (toggle) toggle.hidden = !automatic;
      const navGroup = rail.querySelector('.home-rail-nav-group');
      if (navGroup) navGroup.hidden = !automatic;
      const prog = rail.querySelector('[data-rail-progress]');
      if (prog) prog.hidden = !automatic;
      period = 0;
      if (automatic) {
        const gap = parseFloat(getComputedStyle(track).columnGap) || 18;
        period = originals.reduce((sum, item) => sum + item.getBoundingClientRect().width + gap, 0);
        const groups = Math.ceil(viewport.clientWidth / period) + 1;
        for (let group = 0; group < groups; group += 1) {
          originals.forEach((item) => {
            const copy = item.cloneNode(true);
            copy.removeAttribute('data-rail-original');
            copy.setAttribute('data-rail-copy', '');
            copy.setAttribute('aria-hidden', 'true');
            copy.querySelectorAll('[id]').forEach((element) => element.removeAttribute('id'));
            copy.querySelectorAll('a').forEach((link) => link.setAttribute('tabindex', '-1'));
            track.append(copy);
          });
        }
      }
      viewport.scrollLeft = 0;
      sync();
    }

    if (toggle) {
      toggle.addEventListener('click', () => {
        paused = !paused;
        if (paused) {
          if (resumeTimeout) clearTimeout(resumeTimeout);
          userInteracting = false;
        } else {
          hovered = false;
          userInteracting = false;
        }
        toggle.blur();
        sync();
      });
    }

    function smoothSlide(delta) {
      if (inertiaFrame) {
        cancelAnimationFrame(inertiaFrame);
        inertiaFrame = 0;
      }
      if (frame) {
        cancelAnimationFrame(frame);
        frame = 0;
      }
      userInteracting = true;
      if (resumeTimeout) clearTimeout(resumeTimeout);
      const start = viewport.scrollLeft;
      const startTime = performance.now();
      const duration = 380;

      function step(now) {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        let curr = start + delta * ease;
        if (period > 0) {
          while (curr < 0) curr += period;
          curr = curr % period;
        }
        viewport.scrollLeft = curr;
        offset = period ? ((viewport.scrollLeft % period) + period) % period : viewport.scrollLeft;
        updateProgress();
        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          userInteracting = false;
          sync();
          scheduleAutoResume(1800);
        }
      }
      requestAnimationFrame(step);
    }

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        const itemWidth = originals[0] ? originals[0].getBoundingClientRect().width + 18 : 314;
        smoothSlide(-itemWidth);
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        const itemWidth = originals[0] ? originals[0].getBoundingClientRect().width + 18 : 314;
        smoothSlide(itemWidth);
      });
    }

    const progressTrack = rail.querySelector('.home-rail-progress-track');
    if (progressTrack) {
      progressTrack.style.cursor = 'pointer';
      progressTrack.addEventListener('click', (e) => {
        const rect = progressTrack.getBoundingClientRect();
        const clickRatio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        if (period > 0) {
          const targetScroll = clickRatio * period;
          smoothSlide(targetScroll - (viewport.scrollLeft % period));
        }
      });
    }

    viewport.addEventListener('pointerenter', (event) => {
      if (event.pointerType === 'mouse') {
        hovered = true;
        scheduleAutoResume(2500);
      }
    });

    viewport.addEventListener('pointerleave', () => {
      hovered = false;
      userInteracting = false;
      if (resumeTimeout) clearTimeout(resumeTimeout);
      sync();
    });

    viewport.addEventListener('wheel', () => {
      if (!automatic || paused) return;
      userInteracting = true;
      if (frame) {
        cancelAnimationFrame(frame);
        frame = 0;
      }
      offset = period ? ((viewport.scrollLeft % period) + period) % period : viewport.scrollLeft;
      updateProgress();
      scheduleAutoResume(1800);
    }, { passive: true });

    // Prevent browser native image/link ghost drag so grabbing cards works reliably
    viewport.addEventListener('dragstart', (event) => {
      event.preventDefault();
    });

    viewport.addEventListener('pointerdown', (event) => {
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      if (!['mouse', 'touch', 'pen'].includes(event.pointerType)) return;
      if (event.target.closest('.card-go-btn, .like-btn, .like-form, .card-contact-toggle, [data-rail-toggle], [data-rail-prev], [data-rail-next]')) {
        return;
      }
      if (inertiaFrame) {
        cancelAnimationFrame(inertiaFrame);
        inertiaFrame = 0;
      }
      if (resumeTimeout) clearTimeout(resumeTimeout);
      isPointerDown = true;
      userInteracting = true;
      isDragging = false;
      hasMoved = false;
      startX = event.clientX;
      startScrollLeft = viewport.scrollLeft;
      activePointerId = event.pointerId;
      lastMoveX = event.clientX;
      lastMoveTime = performance.now();
      velocity = 0;
      sync();
      try {
        viewport.setPointerCapture(event.pointerId);
      } catch (_) {}
    });

    viewport.addEventListener('pointermove', (event) => {
      if (!isPointerDown) {
        if (event.pointerType === 'mouse') {
          hovered = true;
          scheduleAutoResume(2500);
        }
        return;
      }
      const dx = event.clientX - startX;
      const now = performance.now();
      const dt = now - lastMoveTime;
      if (dt > 0) {
        velocity = ((event.clientX - lastMoveX) / dt) * 16;
        lastMoveX = event.clientX;
        lastMoveTime = now;
      }

      if (!isDragging && Math.abs(dx) > 3) {
        isDragging = true;
        hasMoved = true;
        viewport.classList.add('is-dragging');
        if (frame) {
          cancelAnimationFrame(frame);
          frame = 0;
        }
      }

      if (isDragging) {
        if (event.pointerType !== 'mouse') event.preventDefault();
        let nextScroll = startScrollLeft - dx;
        if (period > 0) {
          while (nextScroll < 0) {
            nextScroll += period;
            startScrollLeft += period;
          }
          while (nextScroll >= period * 2) {
            nextScroll -= period;
            startScrollLeft -= period;
          }
        }
        viewport.scrollLeft = nextScroll;
        offset = period ? ((viewport.scrollLeft % period) + period) % period : viewport.scrollLeft;
        updateProgress();

        const tilt = Math.max(-5, Math.min(5, -velocity * 0.35));
        track.style.setProperty('--rail-item-tilt', tilt.toFixed(2));
        track.style.setProperty('--rail-item-scale', '0.988');
      }
    });

    const endDrag = () => {
      if (!isPointerDown) return;
      isPointerDown = false;
      track.style.setProperty('--rail-item-tilt', '0');
      track.style.setProperty('--rail-item-scale', '1');

      if (activePointerId !== null) {
        try {
          if (viewport.hasPointerCapture(activePointerId)) {
            viewport.releasePointerCapture(activePointerId);
          }
        } catch (_) {}
        activePointerId = null;
      }

      if (isDragging) {
        isDragging = false;
        viewport.classList.remove('is-dragging');
        offset = period ? ((viewport.scrollLeft % period) + period) % period : viewport.scrollLeft;

        if (Math.abs(velocity) > 0.4) {
          let v = velocity;
          function runInertia() {
            if (isPointerDown || paused) {
              inertiaFrame = 0;
              userInteracting = false;
              sync();
              scheduleAutoResume(1800);
              return;
            }
            v *= 0.94;
            let nextScroll = viewport.scrollLeft - v;
            if (period > 0) {
              while (nextScroll < 0) nextScroll += period;
              nextScroll = nextScroll % period;
            }
            viewport.scrollLeft = nextScroll;
            offset = period ? ((viewport.scrollLeft % period) + period) % period : viewport.scrollLeft;
            updateProgress();
            if (Math.abs(v) > 0.1) {
              inertiaFrame = requestAnimationFrame(runInertia);
            } else {
              inertiaFrame = 0;
              userInteracting = false;
              sync();
              scheduleAutoResume(1800);
            }
          }
          inertiaFrame = requestAnimationFrame(runInertia);
        } else {
          userInteracting = false;
          sync();
          scheduleAutoResume(1800);
        }
      } else {
        userInteracting = false;
        sync();
        scheduleAutoResume(1800);
      }
    };

    viewport.addEventListener('pointerup', endDrag);
    viewport.addEventListener('pointercancel', endDrag);

    // CLICK HANDLER:
    // Only «Перейти ›» navigates to the place. Card body/image is a grab-and-scroll surface.
    track.addEventListener('click', (event) => {
      if (hasMoved) {
        event.preventDefault();
        event.stopPropagation();
        hasMoved = false;
        return;
      }

      // If clicked «Перейти ›», allow navigation
      if (event.target.closest('.card-go-btn')) {
        return;
      }

      // If clicked like button or phone button, allow action
      if (event.target.closest('.like-btn') || event.target.closest('.like-form') || event.target.closest('.card-contact-toggle')) {
        return;
      }

      // Any other click on the card prevents navigation so user can safely grab and drag anywhere!
      const clickedCard = event.target.closest('.card.place-card');
      if (clickedCard) {
        event.preventDefault();
      }
    }, true);

    viewport.addEventListener('scroll', () => {
      offset = period ? ((viewport.scrollLeft % period) + period) % period : viewport.scrollLeft;
      updateProgress();
      if (!isDragging && !inertiaFrame && !paused && automatic) {
        scheduleAutoResume(1800);
      }
    }, { passive: true });

    rail.addEventListener('focusin', sync);
    rail.addEventListener('focusout', () => queueMicrotask(sync));
    document.addEventListener('visibilitychange', sync);
    reduced.addEventListener('change', rebuild);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; sync(); }).observe(rail);
    } else { visible = true; }
    if ('ResizeObserver' in window) {
      new ResizeObserver(() => {
        if (lastWidth !== viewport.clientWidth) { lastWidth = viewport.clientWidth; rebuild(); }
      }).observe(viewport);
    } else { window.addEventListener('resize', rebuild); }
    rebuild();
  });

  // Infinite Benefits Marquee Enhancement
  function initBenefitsMarquee() {
    const marquees = document.querySelectorAll('[data-benefits-marquee]');
    if (!marquees.length) return;

    marquees.forEach((marquee) => {
      const track = marquee.querySelector('[data-benefits-track]');
      const originalList = marquee.querySelector('[data-benefits-list]');
      if (!track || !originalList) return;

      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
      let animFrame = 0;
      let lastTime = 0;
      let offset = 0;
      let listWidth = 0;
      let isHovered = false;
      let isTouching = false;
      let isFocused = false;
      let isVisible = true;
      let currentSpeed = 0.032;

      function getTargetSpeed() {
        if (reduced.matches || !isVisible || document.hidden) return 0;
        const isMobile = window.innerWidth <= 767 || window.matchMedia('(pointer: coarse)').matches;
        if (isHovered || isTouching || isFocused) {
          return 0.009; // smooth, comfortable slow-down on hover/touch
        }
        return isMobile ? 0.022 : 0.034;
      }

      function setupClones() {
        track.querySelectorAll('[data-benefits-clone]').forEach((el) => el.remove());

        if (reduced.matches) {
          track.style.transform = '';
          return;
        }

        listWidth = originalList.getBoundingClientRect().width;
        if (listWidth <= 0) {
          requestAnimationFrame(setupClones);
          return;
        }

        const containerWidth = marquee.clientWidth || window.innerWidth;
        let totalWidth = listWidth;
        while (totalWidth < containerWidth + listWidth * 2) {
          const clone = originalList.cloneNode(true);
          clone.setAttribute('data-benefits-clone', 'true');
          clone.setAttribute('aria-hidden', 'true');
          clone.removeAttribute('data-benefits-list');
          track.appendChild(clone);
          totalWidth += listWidth;
        }
      }

      function tick(time) {
        if (!lastTime) lastTime = time;
        const dt = Math.min(time - lastTime, 64);
        lastTime = time;

        const targetSpeed = getTargetSpeed();
        currentSpeed += (targetSpeed - currentSpeed) * 0.06;

        if (listWidth > 0 && !reduced.matches) {
          offset += currentSpeed * dt;
          if (offset >= listWidth) {
            offset = offset % listWidth;
          }
          track.style.transform = `translate3d(${-offset.toFixed(2)}px, 0, 0)`;
        }

        if (!reduced.matches && isVisible && !document.hidden) {
          animFrame = requestAnimationFrame(tick);
        } else {
          animFrame = 0;
        }
      }

      function startTicker() {
        if (!animFrame && !reduced.matches && isVisible && !document.hidden) {
          lastTime = 0;
          animFrame = requestAnimationFrame(tick);
        }
      }

      function stopTicker() {
        if (animFrame) {
          cancelAnimationFrame(animFrame);
          animFrame = 0;
        }
      }

      marquee.addEventListener('mouseenter', () => { isHovered = true; });
      marquee.addEventListener('mouseleave', () => { isHovered = false; });
      marquee.addEventListener('touchstart', () => { isTouching = true; }, { passive: true });
      marquee.addEventListener('touchend', () => { isTouching = false; }, { passive: true });
      marquee.addEventListener('touchcancel', () => { isTouching = false; }, { passive: true });
      marquee.addEventListener('focusin', () => { isFocused = true; });
      marquee.addEventListener('focusout', () => { isFocused = false; });

      document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
          stopTicker();
        } else {
          startTicker();
        }
      });

      reduced.addEventListener('change', () => {
        setupClones();
        if (reduced.matches) {
          stopTicker();
          track.style.transform = '';
        } else {
          startTicker();
        }
      });

      if ('IntersectionObserver' in window) {
        new IntersectionObserver(([entry]) => {
          isVisible = entry.isIntersecting;
          if (isVisible) {
            startTicker();
          } else {
            stopTicker();
          }
        }, { threshold: 0.05 }).observe(marquee);
      } else {
        isVisible = true;
      }

      let resizeTimer = 0;
      window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
          setupClones();
        }, 120);
      }, { passive: true });

      if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(setupClones);
      }

      setupClones();
      startTicker();
    });
  }

  initBenefitsMarquee();
})();
