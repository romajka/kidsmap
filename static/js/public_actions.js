(function () {
  function prepareForms() {
    const fields = document.querySelectorAll("input[data-km-csrf]");
    if (!fields.length) return;
    const cookie = document.cookie.split("; ").find(value => value.startsWith("csrftoken="));
    if (!cookie) return;
    for (const field of fields) {
      field.name = "csrfmiddlewaretoken";
      field.value = cookie.slice("csrftoken=".length);
    }
  }

  prepareForms();
  document.addEventListener("DOMContentLoaded", prepareForms, { once: true });
  document.addEventListener("submit", prepareForms, true);
}());

      (function () {
        const labels = document.currentScript.dataset;
        const toastStack = document.querySelector("[data-toast-stack]");
        const toastLoginLabel = labels.login;
        const toastCloseLabel = labels.close;
        const genericActionErrorMessage = labels.failure;

        const favoriteFeedbackMessages = {
          ru: { added: "Добавлено в избранное", removed: "Удалено из избранного" },
          az: { added: "Seçilmişlərə əlavə edildi", removed: "Seçilmişlərdən silindi" },
          en: { added: "Added to favorites", removed: "Removed from favorites" },
        };
        const favoriteFeedback = favoriteFeedbackMessages[(document.documentElement.lang || "az").split("-")[0]] || favoriteFeedbackMessages.az;

        function showToast(message, options) {
          if (!toastStack || !message) return;
          const config = options || {};
          const toast = document.createElement("section");
          toast.className = "toast toast-" + (config.variant || "info");
          toast.setAttribute("role", "status");

          const text = document.createElement("p");
          text.className = "toast-message";
          text.textContent = message;
          toast.appendChild(text);

          const actions = document.createElement("div");
          actions.className = "toast-actions";

          if (config.actionUrl) {
            const actionLink = document.createElement("a");
            actionLink.className = "toast-link";
            actionLink.href = config.actionUrl;
            actionLink.textContent = config.actionLabel || toastLoginLabel;
            actions.appendChild(actionLink);
          }

          const closeButton = document.createElement("button");
          closeButton.type = "button";
          closeButton.className = "toast-close";
          closeButton.textContent = toastCloseLabel;
          closeButton.setAttribute("aria-label", toastCloseLabel);
          actions.appendChild(closeButton);

          toast.appendChild(actions);
          toastStack.appendChild(toast);

          const removeToast = function () {
            if (!toast.isConnected) return;
            toast.classList.add("is-leaving");
            window.setTimeout(function () {
              toast.remove();
            }, 220);
          };

          closeButton.addEventListener("click", removeToast);
          window.setTimeout(function () {
            toast.classList.add("is-visible");
          }, 10);
          window.setTimeout(removeToast, config.duration || 4200);
        }

        window.addEventListener("kidsmap:notification", function (event) {
          showToast(event.detail.message, event.detail);
        });

        function handleAuthRequiredPayload(payload) {
          if (!payload || !payload.auth_required) return false;
          showToast(
            payload.message || labels.signIn,
            {
              actionUrl: payload.redirect_url || "",
              actionLabel: toastLoginLabel,
              variant: "info",
            }
          );
          return true;
        }

        function showAuthRequiredNotice(message, redirectUrl, form) {
          const resolvedMessage = message || labels.signIn;
          showToast(resolvedMessage, {
            actionUrl: redirectUrl || "",
            actionLabel: toastLoginLabel,
            variant: "info",
          });
          if (form instanceof HTMLFormElement) {
            showInlineFormNotice(form, resolvedMessage, { duration: 4200 });
          }
        }

        function showInlineFormNotice(form, message, options) {
          if (!(form instanceof HTMLFormElement) || !message) return;
          const config = options || {};
          const siblingNotice = form.parentElement ? form.parentElement.querySelector(".form-inline-notice") : null;
          if (siblingNotice) {
            siblingNotice.remove();
          }

          const notice = document.createElement("p");
          notice.className = "form-inline-notice" + (config.variant === "error" ? " is-error" : "");
          notice.textContent = message;
          form.insertAdjacentElement("afterend", notice);

          window.setTimeout(function () {
            if (notice.isConnected) {
              notice.remove();
            }
          }, config.duration || 4200);
        }

        function buildImagePlaceholder(text) {
          const wrap = document.createElement("div");
          wrap.className = "image-placeholder";
          wrap.setAttribute("aria-label", text);

          const icon = document.createElement("span");
          icon.className = "image-placeholder-icon";
          icon.setAttribute("aria-hidden", "true");
          icon.textContent = "📷";

          const label = document.createElement("span");
          label.className = "image-placeholder-text";
          label.textContent = text;

          wrap.appendChild(icon);
          wrap.appendChild(label);
          return wrap;
        }

        function attachImageFallbacks() {
          document.querySelectorAll("img[data-photo-fallback]").forEach(function (img) {
            const text = img.getAttribute("data-placeholder-text") || labels.photo;
            const applyFallback = function () {
              const fallbackSrc = img.getAttribute("data-fallback-src");
              if (fallbackSrc && img.getAttribute("data-fallback-applied") !== "1") {
                img.setAttribute("data-fallback-applied", "1");
                img.src = fallbackSrc;
                return;
              }

              const container = img.closest(".card-media");
              if (!container || container.querySelector(".image-placeholder")) return;
              const mediaLink = img.closest(".card-media-link");
              container.querySelectorAll(".card-media-blur-bg").forEach(function (background) {
                background.remove();
              });
              img.remove();
              const categoryTemplate = container.querySelector("template[data-card-image-placeholder]");
              const categoryPlaceholder = categoryTemplate && categoryTemplate.content.firstElementChild;
              (mediaLink || container).appendChild(categoryPlaceholder ? categoryPlaceholder.cloneNode(true) : buildImagePlaceholder(text));
            };

            img.addEventListener("error", applyFallback);
            if (img.complete && img.naturalWidth === 0) {
              applyFallback();
            }
          });
        }

        attachImageFallbacks();

        function updateLikeForm(form, payload) {
          if (!payload || payload.ok !== true) return;
          const button = form.querySelector(".like-btn");
          const countEl = form.querySelector(".like-count");
          if (button) {
            button.classList.toggle("active", !!payload.liked);
            button.setAttribute("aria-pressed", payload.liked ? "true" : "false");
            const nextLabel = payload.liked ? button.dataset.favoriteRemoveLabel : button.dataset.favoriteAddLabel;
            if (nextLabel) {
              button.setAttribute("aria-label", nextLabel);
              button.setAttribute("title", nextLabel);
            }
            button.classList.remove("like-pop");
            // restart keyframe animation for each state change
            void button.offsetWidth;
            button.classList.add("like-pop");
          }
          if (countEl && typeof payload.likes_count === "number") {
            countEl.textContent = payload.likes_count;
          }
          showToast(payload.liked ? favoriteFeedback.added : favoriteFeedback.removed);
          if (payload.analytics_event && typeof window.kidsMapEmitAnalyticsEvent === "function") {
            window.kidsMapEmitAnalyticsEvent(payload.analytics_event);
          }
        }

        function updateReviewReactionForm(form, payload) {
          if (!payload || payload.ok !== true) return;
          const likeButton = form.querySelector('button[name="value"][value="1"]');
          const dislikeButton = form.querySelector('button[name="value"][value="-1"]');
          const likeCountEl = form.querySelector("[data-review-like-count]");
          const dislikeCountEl = form.querySelector("[data-review-dislike-count]");

          if (likeButton) {
            const isActive = payload.current_reaction === 1;
            likeButton.classList.toggle("active", isActive);
            likeButton.setAttribute("aria-pressed", isActive ? "true" : "false");
          }

          if (dislikeButton) {
            const isActive = payload.current_reaction === -1;
            dislikeButton.classList.toggle("active", isActive);
            dislikeButton.setAttribute("aria-pressed", isActive ? "true" : "false");
          }

          if (likeCountEl && typeof payload.likes_count === "number") {
            likeCountEl.textContent = payload.likes_count;
          }

          if (dislikeCountEl && typeof payload.dislikes_count === "number") {
            dislikeCountEl.textContent = payload.dislikes_count;
          }
        }

        function setReviewReactionPending(form, isPending) {
          form.classList.toggle("is-pending", !!isPending);
          form.querySelectorAll(".review-reaction-btn").forEach(function (button) {
            button.disabled = !!isPending;
            button.setAttribute("aria-busy", isPending ? "true" : "false");
          });
        }

        function buildFormPayload(form, submitter) {
          if (submitter) {
            try {
              return new FormData(form, submitter);
            } catch (err) {
              // Fallback for browsers without FormData(form, submitter).
            }
          }

          const formData = new FormData(form);
          if (submitter && submitter.name) {
            formData.append(submitter.name, submitter.value || "");
          }
          return formData;
        }

        async function submitJsonForm(form, submitButtons, onSuccess, submitter) {
          const buttons = submitButtons.filter(Boolean);
          if (buttons.some((button) => button.disabled)) return;
          // Build the payload while the clicked submit button is still enabled.
          // Disabled submitters are omitted from FormData, which used to drop
          // the review reaction's value (1/-1) in some browsers.
          const formPayload = buildFormPayload(form, submitter);
          const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
          buttons.forEach((button) => {
            button.disabled = true;
          });

          try {
            const headers = {
              "X-Requested-With": "XMLHttpRequest",
              "Accept": "application/json",
            };
            if (csrfInput && csrfInput.value) {
              headers["X-CSRFToken"] = csrfInput.value;
            }
            const response = await fetch(form.action, {
              method: "POST",
              headers: headers,
              body: formPayload,
              credentials: "same-origin",
            });
            const payload = await response.json().catch(function () {
              return null;
            });
            if (response.status === 401 && handleAuthRequiredPayload(payload)) {
              showInlineFormNotice(form, payload.message || "", { duration: 4200 });
              return;
            }
            if (!response.ok && payload && payload.message) {
              showToast(payload.message, { variant: "error" });
              showInlineFormNotice(form, payload.message, { variant: "error" });
              return;
            }
            if (!response.ok || !payload) throw new Error("Request failed");
            onSuccess(form, payload);
          } catch (err) {
            showToast(genericActionErrorMessage, { variant: "error" });
            showInlineFormNotice(form, genericActionErrorMessage, { variant: "error" });
          } finally {
            delete form.__kidsMapSubmitter;
            buttons.forEach((button) => {
              button.disabled = false;
            });
          }
        }

        document.addEventListener("click", function (event) {
          if (!(event.target instanceof Element)) return;
          const authRequiredTrigger = event.target.closest("[data-auth-required-trigger]");
          if (authRequiredTrigger) {
            event.preventDefault();
            showAuthRequiredNotice(
              authRequiredTrigger.getAttribute("data-auth-required-message"),
              authRequiredTrigger.getAttribute("data-auth-required-url"),
              authRequiredTrigger.closest("form")
            );
            return;
          }
          const reviewReactionButton = event.target.closest(".review-reaction-btn");
          if (reviewReactionButton && reviewReactionButton.form instanceof HTMLFormElement && reviewReactionButton.form.matches("[data-review-reaction-form]")) {
            reviewReactionButton.form.__kidsMapSubmitter = reviewReactionButton;
          }
          const submitter = event.target.closest('button[type="submit"], input[type="submit"]');
          if (!submitter || !(submitter.form instanceof HTMLFormElement)) return;
          submitter.form.__kidsMapSubmitter = submitter;
        });

        document.addEventListener("submit", async function (event) {
          const form = event.target;
          if (!(form instanceof HTMLFormElement)) return;
          const submitter = event.submitter || form.__kidsMapSubmitter || null;
          if (form.matches("[data-like-form]")) {
            event.preventDefault();
            await submitJsonForm(
              form,
              [form.querySelector(".like-btn")],
              updateLikeForm,
              submitter,
            );
            return;
          }
          if (form.matches("[data-review-reaction-form]")) {
            event.preventDefault();
            form.classList.add("is-pending");
            await submitJsonForm(
              form,
              Array.from(form.querySelectorAll(".review-reaction-btn")),
              updateReviewReactionForm,
              submitter,
            );
            window.setTimeout(function () {
              form.classList.remove("has-error");
            }, 1400);
            setReviewReactionPending(form, false);
          }
        });

        (function () {
          const headerMenus = Array.from(document.querySelectorAll(".header-menu"));
          if (!headerMenus.length) return;

          headerMenus.forEach(function (menu) {
            const summary = menu.querySelector("summary");
            if (summary) {
              summary.setAttribute("aria-expanded", menu.hasAttribute("open") ? "true" : "false");
            }
            menu.addEventListener("toggle", function () {
              if (summary) {
                summary.setAttribute("aria-expanded", menu.hasAttribute("open") ? "true" : "false");
              }
              if (!menu.hasAttribute("open")) return;
              headerMenus.forEach(function (other) {
                if (other === menu) return;
                other.removeAttribute("open");
              });
            });

            menu.querySelectorAll("a").forEach(function (link) {
              link.addEventListener("click", function () {
                menu.removeAttribute("open");
              });
            });
          });

          document.addEventListener("click", function (event) {
            headerMenus.forEach(function (menu) {
              if (!menu.hasAttribute("open")) return;
              if (menu.contains(event.target)) return;
              menu.removeAttribute("open");
            });
          });

          document.addEventListener("keydown", function (event) {
            if (event.key !== "Escape") return;
            headerMenus.forEach(function (menu) {
              menu.removeAttribute("open");
            });
          });
        })();

        (function () {
          if (typeof window.IntersectionObserver !== "function") return;
          if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

          const targets = Array.from(
            document.querySelectorAll(".panel:not(.content-page):not(.legal-page), .card, .home-tile, .trust-card, .faq-card")
          );
          if (!targets.length) return;

          targets.forEach(function (el, idx) {
            el.classList.add("reveal-item");
            el.style.setProperty("--reveal-order", String(idx % 8));
            if (el.getBoundingClientRect().top <= window.innerHeight * 1.05) {
              el.classList.add("is-visible");
            }
          });

          const observer = new IntersectionObserver(
            function (entries, obs) {
              entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                entry.target.classList.add("is-visible");
                obs.unobserve(entry.target);
              });
            },
            { threshold: 0.14, rootMargin: "0px 0px -8% 0px" }
          );

          targets.forEach(function (el) {
            observer.observe(el);
          });

          window.setTimeout(function () {
            targets.forEach(function (el) {
              el.classList.add("is-visible");
            });
            observer.disconnect();
          }, 1400);
        })();

        (function () {
          function sendGoogleAnalyticsEvent(name, params) {
            if (document.body.hasAttribute('data-site-preview')) return;
            if (!name || typeof window.gtag !== "function") return;
            window.gtag("event", name, params || {});
          }

          window.kidsMapTrackGoogleAnalyticsEvent = sendGoogleAnalyticsEvent;

          const trackUrl = labels.trackUrl;
          if (document.body.hasAttribute('data-site-preview')) return;

          function emitAnalyticsEvent(eventItem) {
            if (!eventItem || !eventItem.name) return;
            sendGoogleAnalyticsEvent(eventItem.name, eventItem.params || {});
            if (typeof window.kidsMapTrackYandexMetricaEvent === "function") {
              window.kidsMapTrackYandexMetricaEvent(eventItem.name);
            }
          }

          window.kidsMapEmitAnalyticsEvent = emitAnalyticsEvent;

          function send(payload) {
            if (!payload || !payload.event_type) return;
            const legacyAliases = {
              place_open: "place_view",
              cta_call: "phone_click",
              cta_whatsapp: "whatsapp_click",
              cta_instagram: "social_click",
            };
            payload.event_type = legacyAliases[payload.event_type] || payload.event_type;
            let analyticsParams;
            if (payload.event_type === "ai_referral_visit") {
              analyticsParams = {
                ai_source: payload.ai_source || "",
                landing_path: payload.landing_path || "",
                page_type: payload.page_type || "",
                language: payload.language || "",
              };
            } else {
              analyticsParams = {
                page_type: payload.source || "",
                place_id: payload.place_id || undefined,
              };
            }
            emitAnalyticsEvent({
              name: payload.event_type,
              params: analyticsParams,
            });
            if (!trackUrl) return;
            try {
              if (navigator.sendBeacon) {
                const blob = new Blob([JSON.stringify(payload)], { type: "application/json" });
                if (navigator.sendBeacon(trackUrl, blob)) return; // Enqueued
              }
            } catch (err) {}

            fetch(trackUrl, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(payload),
              credentials: "same-origin",
              keepalive: true,
            }).catch(function () {});
          }

          window.kidsMapTrackEvent = send;

          document.addEventListener("click", function (event) {
            const target = event.target.closest("[data-track-event]");
            if (!target) return;

            const placeIdRaw = target.getAttribute("data-track-place-id");
            const placeId = placeIdRaw && /^\d+$/.test(placeIdRaw) ? Number(placeIdRaw) : null;

            send({
              event_type: target.getAttribute("data-track-event"),
              place_id: placeId,
              source: target.getAttribute("data-track-source") || "",
              path: window.location.pathname,
            });
          });
        })();

        // Footer Accordion toggles
        (function () {
          const mobile = window.matchMedia("(max-width: 820px)");
          const triggers = document.querySelectorAll(".footer-accordion-trigger");
          function syncFooter() {
            triggers.forEach(trigger => {
              const content = trigger.closest("[data-footer-accordion]").querySelector(".footer-accordion-content");
              trigger.disabled = !mobile.matches;
              trigger.setAttribute("aria-expanded", mobile.matches ? "false" : "true");
              content.hidden = mobile.matches;
              content.style.maxHeight = null;
            });
          }
          triggers.forEach((trigger, index) => {
            const content = trigger.closest("[data-footer-accordion]").querySelector(".footer-accordion-content");
            content.id = "footer-section-" + index;
            trigger.setAttribute("aria-controls", content.id);
            trigger.addEventListener("click", function () {
              if (!mobile.matches) return;
              const expanded = this.getAttribute("aria-expanded") !== "true";
              this.setAttribute("aria-expanded", String(expanded));
              content.hidden = !expanded;
              content.style.maxHeight = expanded ? content.scrollHeight + "px" : null;
            });
          });
          syncFooter();
          mobile.addEventListener("change", syncFooter);
        })();

        // Floating Back-to-Top button with scroll progress
        (function () {
          const btn = document.querySelector("[data-back-to-top]");
          if (!btn) return;

          const progressBar = btn.querySelector(".km-progress-bar");
          const totalLength = 131.95;
          const phone = window.matchMedia("(max-width: 767px)");
          let ticking = false;
          let lastScrollTop = window.scrollY || 0;
          let scrollingUp = false;

          function updateScroll() {
            const scrollTop = window.scrollY || document.documentElement.scrollTop;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            if (Math.abs(scrollTop - lastScrollTop) > 6) {
              scrollingUp = scrollTop < lastScrollTop;
              lastScrollTop = scrollTop;
            }

            // Phones: the button would sit on card actions while reading, so it
            // only appears when the visitor starts scrolling back up.
            if (scrollTop > 220 && (!phone.matches || scrollingUp)) {
              btn.classList.add("is-visible");
            } else {
              btn.classList.remove("is-visible");
            }

            if (progressBar && docHeight > 0) {
              const progress = Math.min(1, Math.max(0, scrollTop / docHeight));
              const offset = totalLength - (progress * totalLength);
              progressBar.style.strokeDashoffset = offset;
            }

            ticking = false;
          }

          window.addEventListener("scroll", function () {
            if (!ticking) {
              window.requestAnimationFrame(updateScroll);
              ticking = true;
            }
          }, { passive: true });

          btn.addEventListener("click", function (e) {
            e.preventDefault();
            window.scrollTo({
              top: 0,
              behavior: "smooth"
            });
          });

          updateScroll();
        })();

      })();
