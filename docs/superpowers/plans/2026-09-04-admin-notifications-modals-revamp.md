# Admin Notifications and Modals Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a unified, accessible, premium design system for all notifications, modals, confirm dialogs, toasts, and alerts across the KidsMap admin panel, completely replacing disparate/outdated implementations (SweetAlert2, native alerts/confirms, fragmented styles) with a consistent 5-state system.

**Architecture:** 
A centralized notification engine comprising `kidsmap_notifications.css` and `kidsmap_notifications.js` exposed globally via `window.kmModal`, `window.kmToast`, `window.kmConfirm`, and `window.kmAlert`. Loaded across the entire admin panel through `base_site.html` alongside the SVG icon sprite (`km_icon_sprite.html`). All individual admin scripts (`kidsmap_admin_form_shell.js`, `kidsmap_place_form.js`, `kidsmap_place_changelist.js`, `kidsmap_review_changelist.js`, `kidsmap_taxonomy.js`, `kidsmap_site_media.js`, etc.) and templates are refactored to consume this unified API.

**Tech Stack:** Vanilla JavaScript (ES6-compatible, zero dependencies), CSS Variables / KidsMap Design Tokens, SVG Icons Sprite (Material Symbols outlines), Django Admin / Jazzmin Templates.

**Spec:** User prompt requirements:
- 5 states: success, warning, error, info, destructive/danger
- Unsaved changes modal with 3 distinct actions ("Остаться", "Сохранить и выйти", "Выйти без сохранения") with clear hierarchy and prevention of accidental destructive clicks; internal navigation interception vs. native browser beforeunload
- Dangerous action confirm modals (unpublish, delete, etc.)
- Unified toasts system (saved, published, unpublished, imported, coordinates calculated, error, warning, info) with auto-dismiss and manual close
- Full accessibility: focus trap, Esc key, aria attributes (`role="dialog"`, `role="alertdialog"`, `aria-modal`), backdrop scroll lock, focus restoration
- Responsive layout (desktop centered card, mobile bottom sheet/card)
- Clean typography and calm, friendly microcopy without bureaucratic clutter

## Global Constraints
- Do not break existing Django admin workflows or business logic.
- Do not use native `alert()` or `confirm()` inside application interactions (except `beforeunload` for browser tab close/navigation).
- Remove third-party SweetAlert2 dependencies and unify everything on the KidsMap design language.
- Ensure all tests pass.

---

### Task 1: Create the Unified Notifications & Modals Stylesheet (`kidsmap_notifications.css`)

**Files:**
- Create: `static/admin/css/kidsmap_notifications.css`
- Modify: `static/admin/css/kidsmap_admin.css`
- Modify: `templates/admin/base_site.html`

**Interfaces:**
- Produces CSS classes:
  - `.km-modal-backdrop`, `.km-modal`, `.km-modal--sm`, `.km-modal--md`, `.km-modal--lg`
  - 5 states: `.km-modal__icon--success`, `.km-modal__icon--warning`, `.km-modal__icon--error`, `.km-modal__icon--info`, `.km-modal__icon--danger`
  - Action buttons: `.km-btn-modal`, `.km-btn-modal--primary`, `.km-btn-modal--danger`, `.km-btn-modal--secondary`, `.km-btn-modal--quiet`
  - Unsaved modal layout: `.km-unsaved-modal`, with clear separation for the destructive button
  - Toast container: `.km-toast-container`, `.km-toast`, `.km-toast--success`, `.km-toast--warning`, `.km-toast--error`, `.km-toast--info`, `.km-toast--danger`
  - Inline alerts: `.km-alert`, `.km-alert--success`, `.km-alert--warning`, `.km-alert--error`, `.km-alert--info`, `.km-alert--danger`
  - Confirm cards: `.km-confirm-card`, `.km-confirm-icon-wrap`, `.km-confirm-title`, `.km-confirm-text`, `.km-confirm-actions` (unifying the 4 delete/restore confirm templates)
  - Dark mode support for all above components

- [ ] **Step 1: Write `static/admin/css/kidsmap_notifications.css`**
Include complete styling for modals, backdrops, focus states, animations, toasts, inline alerts, confirm cards, and responsive rules.

- [ ] **Step 2: Import `kidsmap_notifications.css` into `static/admin/css/kidsmap_admin.css`**
Add `@import 'kidsmap_notifications.css?v=1';` so that all admin pages inherit the stylesheet.

- [ ] **Step 3: Update `templates/admin/base_site.html` to include the SVG sprite and notification assets globally**
Include `admin/catalog/includes/km_icon_sprite.html` in `base_site.html` so that icons are always rendered properly on every admin page.

---

### Task 2: Create the Core JavaScript Library (`kidsmap_notifications.js`)

**Files:**
- Create: `static/admin/js/kidsmap_notifications.js`
- Modify: `templates/admin/base_site.html`

**Interfaces:**
- Produces global APIs:
  - `window.kmModal.show({ title, message, icon, tone, actions, closeOnBackdrop, closeOnEscape, onClose, customClass, isAlertDialog })`
  - `window.kmModal.confirm({ title, message, confirmText, cancelText, tone, onConfirm, onCancel, icon })` (returns Promise)
  - `window.kmModal.alert({ title, message, okText, tone, onOk, icon })` (returns Promise)
  - `window.kmModal.close()`
  - `window.kmModal.unsavedChanges({ onSaveAndExit, onExitWithoutSaving, onStay })`
  - `window.kmToast.show({ title, message, type, duration, action, onClose })`
  - `window.kmToast.success(title, message, action)`
  - `window.kmToast.warning(title, message, action)`
  - `window.kmToast.error(title, message, action)`
  - `window.kmToast.info(title, message, action)`
  - `window.kmToast.dismiss(toastEl)`
  - `window.kmToast.clearAll()`
- Features:
  - Full focus trap (keeps Tab / Shift+Tab inside the open modal)
  - Focus restoration to the trigger element when modal closes
  - Body scroll lock (`document.body.classList.add('km-modal-open')`)
  - ESC key handling
  - ARIA attributes: `role="dialog"` or `role="alertdialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby`
  - Fallback SVG icons if SVG sprite is somehow omitted

- [ ] **Step 1: Write `static/admin/js/kidsmap_notifications.js`**
Implement the unified `kmModal` and `kmToast` modules with all methods, focus management, animations, and accessibility.

- [ ] **Step 2: Include `kidsmap_notifications.js` in `templates/admin/base_site.html`**
Ensure it loads before page scripts so `window.kmModal` and `window.kmToast` are always available.

---

### Task 3: Overhaul the Unsaved Changes Handling Across Admin Forms

**Files:**
- Modify: `static/admin/js/kidsmap_place_form.js`
- Modify: `static/admin/js/kidsmap_admin_form_shell.js`

**Interfaces:**
- Consumes: `window.kmModal.unsavedChanges(...)`, `window.kmToast`
- Scenarios handled:
  - Form dirty detection on user input
  - Clicking any internal link or button -> intercepts and opens `kmModal.unsavedChanges`
  - Three distinct actions:
    1. "Остаться" (ghost/quiet button) -> cancels navigation, closes modal, restores focus.
    2. "Сохранить и выйти" (primary button) -> triggers save then redirects to target URL.
    3. "Выйти без сохранения" (danger-filled button, separated layout) -> proceeds directly to target URL.
  - Hard reload / closing tab / leaving browser -> uses standard `beforeunload` event handler.

- [ ] **Step 1: Refactor unsaved changes in `static/admin/js/kidsmap_place_form.js`**
Replace custom/local modal code with `window.kmModal.unsavedChanges`, ensuring clean 3-button hierarchy, smooth save flow, and error toast handling.

- [ ] **Step 2: Refactor unsaved changes in `static/admin/js/kidsmap_admin_form_shell.js`**
Remove `Swal.fire` and `confirm(...)` for unsaved changes. Use `window.kmModal.unsavedChanges`. Support saving and redirecting or discarding changes.

---

### Task 4: Unify Confirmations and Danger Flows in Place Changelist and Bulk Actions

**Files:**
- Modify: `static/admin/js/kidsmap_place_changelist.js`
- Modify: `static/admin/js/kidsmap_admin_form_shell.js`
- Modify: `static/admin/js/kidsmap_review_changelist.js`
- Modify: `static/admin/js/kidsmap_taxonomy.js`
- Modify: `static/admin/js/kidsmap_site_media.js`
- Modify: `src/catalog/templates/admin/catalog/place/change_list.html`
- Modify: `src/catalog/templates/admin/catalog/place/change_form.html`
- Modify: `src/catalog/templates/admin/catalog/event/change_list.html`
- Modify: `src/catalog/templates/admin/catalog/event/change_form.html`

**Interfaces:**
- Consumes: `window.kmModal.confirm`, `window.kmToast`
- Changes:
  - Remove SweetAlert2 CDN script tags from all templates
  - Replace SweetAlert2 unpublish confirmation with `kmModal.confirm`:
    - Title: "Снять с публикации?"
    - Message: "Карточка перестанет отображаться на сайте и перейдёт в черновики."
    - Buttons: "Отмена" (secondary), "Снять с публикации" (warning/danger)
  - Replace SweetAlert2 soft_delete confirmation with `kmModal.confirm`:
    - Title: "Переместить в удалённые?"
    - Message: "Карточка будет скрыта и перемещена в раздел «В удалённых»."
    - Buttons: "Отмена" (secondary), "Переместить в удалённые" (danger)
  - Replace SweetAlert2 loaders and alerts with `kmToast`:
    - Toggle publication loader -> `kmToast.info("Обновление статуса публикации...")`
    - Published success -> `kmToast.success("Опубликовано", "Карточка теперь отображается на сайте.")`
    - Unpublished success -> `kmToast.warning("Снято с публикации", "Карточка переведена в черновики.")`
    - Publish error -> `kmToast.error("Не удалось опубликовать", errorMsg)`
  - Replace `.deletelink` navigation intercept in `kidsmap_admin_form_shell.js` with `kmModal.confirm`
  - Replace `window.confirm` in `kidsmap_review_changelist.js` with `kmModal.confirm`
  - Replace `confirm` and `alert` in `kidsmap_taxonomy.js` with `kmModal.confirm` and `kmToast.error`
  - Replace `window.confirm` and `alert` in `kidsmap_site_media.js` with `kmModal.confirm` and `kmToast.error`
  - Replace `alert` in `kidsmap_category_popup.js` and `kidsmap_place_media.js` with `kmToast`

---

### Task 5: Unify Inline Alerts and Django Admin Messages

**Files:**
- Modify: `templates/admin/base.html`
- Modify: `static/admin/css/kidsmap_notifications.css`

**Interfaces:**
- Consumes: unified `.km-alert` system
- Changes:
  - Modernize Django admin messages block (`{% block messages %}`) in `templates/admin/base.html`:
    - Render alerts using `.km-alert.km-alert--<type>` with proper SVG icons (`check_circle`, `warning`, `error`, `info`), dismiss button, clear typography.
  - Standardize `.km-place-form-alert`, `.km-category-alert`, `.km-user-access-alert`, and `.km-pf-alert` to adhere to the same spacing, border-radius, font size, and color hierarchy.

---

### Task 6: Unify Standalone Confirmation Pages

**Files:**
- Modify: `src/catalog/templates/admin/catalog/place_delete_confirmation.html`
- Modify: `src/catalog/templates/admin/catalog/place_delete_selected_confirmation.html`
- Modify: `src/catalog/templates/admin/catalog/place_restore_confirmation.html`
- Modify: `src/catalog/templates/admin/catalog/placereview/moderation_confirm.html`

**Interfaces:**
- Remove redundant inline `<style>` tags from each template and rely on `kidsmap_notifications.css`
- Standardize `.km-confirm-card` styles, button styles, typography, and responsive adjustments across all 4 templates.

---

### Task 7: Verification and Comprehensive Testing

**Files:**
- Test with Django test suite: `catalog.testcases.admin`
- Write automated test for notification stylesheet and script inclusion
- Verify key scenarios:
  1. Unsaved changes modal (Stay, Save and exit, Exit without saving)
  2. Native beforeunload on browser reload/close
  3. Unpublish confirm modal
  4. Delete confirm modal
  5. Restore confirm modal
  6. Toast notifications (success, warning, error, info)
  7. Mobile responsiveness and accessibility (Esc, Tab order, focus trap)
  8. Absence of console errors and clean z-index stacking
