(function () {
  function ready(callback) {
    if (document.readyState !== "loading") {
      callback();
      return;
    }
    document.addEventListener("DOMContentLoaded", callback);
  }

  ready(function () {
    var root = document.querySelector("[data-home-recommendations]");
    if (!root) return;

    var dataNode = document.getElementById("km-home-recommendation-data");
    var slots = root.querySelector("[data-home-recs-slots]");
    var counter = root.querySelector("[data-home-recs-counter]");
    var status = root.querySelector("[data-home-recs-status]");
    var fallback = root.querySelector("[data-home-recs-fallback]");
    var openButton = root.querySelector("[data-home-recs-open]");
    var dialog = root.querySelector("[data-home-recs-dialog]");
    var closeButton = root.querySelector("[data-home-recs-close]");
    var searchInput = root.querySelector("[data-home-recs-search]");
    var candidatesNode = root.querySelector("[data-home-recs-candidates]");
    var csrfInput = root.querySelector("[name=csrfmiddlewaretoken]");
    var saveUrl = root.dataset.saveUrl || "";
    var candidatesUrl = root.dataset.candidatesUrl || "";
    var maxItems = Number(root.dataset.maxItems || 4);
    var cards = [];
    var draggedId = null;
    var searchTimer = null;
    var isSaving = false;

    try {
      cards = JSON.parse(dataNode ? dataNode.textContent : "[]");
    } catch (error) {
      cards = [];
    }

    function selectedIds() {
      return cards.map(function (card) {
        return Number(card.id);
      });
    }

    function setBusy(busy) {
      isSaving = busy;
      root.classList.toggle("is-saving", busy);
      root.setAttribute("aria-busy", busy ? "true" : "false");
      if (openButton) openButton.disabled = busy || cards.length >= maxItems;
    }

    function showStatus(message, tone) {
      if (!status) return;
      status.textContent = message;
      status.className = "km-home-recs__status is-visible km-home-recs__status--" + (tone || "success");
      window.clearTimeout(showStatus.timer);
      showStatus.timer = window.setTimeout(function () {
        status.classList.remove("is-visible");
      }, 2600);
    }

    function createIconButton(className, label, iconClass) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = className;
      button.setAttribute("aria-label", label);
      button.title = label;
      var icon = document.createElement("i");
      icon.className = iconClass;
      icon.setAttribute("aria-hidden", "true");
      button.appendChild(icon);
      return button;
    }

    function moveCard(cardId, direction) {
      if (isSaving) return;
      var index = cards.findIndex(function (card) {
        return Number(card.id) === Number(cardId);
      });
      var nextIndex = index + direction;
      if (index < 0 || nextIndex < 0 || nextIndex >= cards.length) return;
      var previous = cards.slice();
      var moved = cards.splice(index, 1)[0];
      cards.splice(nextIndex, 0, moved);
      render();
      save(previous, "Порядок сохранён");
    }

    function createCard(card, index) {
      var article = document.createElement("article");
      article.className = "km-home-recs__card";
      article.dataset.placeId = String(card.id);
      article.draggable = true;

      var position = document.createElement("span");
      position.className = "km-home-recs__position";
      position.textContent = String(index + 1);
      position.setAttribute("aria-label", "Позиция " + String(index + 1));

      var handle = document.createElement("span");
      handle.className = "km-home-recs__handle";
      handle.setAttribute("aria-hidden", "true");
      handle.innerHTML = '<i class="fas fa-grip-vertical"></i>';

      var media = document.createElement("div");
      media.className = "km-home-recs__media";
      if (card.image_url) {
        var image = document.createElement("img");
        image.src = card.image_url;
        image.alt = "";
        image.loading = "lazy";
        media.appendChild(image);
      } else {
        media.innerHTML = '<i class="far fa-image" aria-hidden="true"></i>';
      }

      var body = document.createElement("div");
      body.className = "km-home-recs__card-body";
      var category = document.createElement("span");
      category.className = "km-home-recs__category";
      category.textContent = card.category || "Место";
      var title = document.createElement("a");
      title.className = "km-home-recs__card-title";
      title.href = card.change_url || "#";
      title.textContent = card.title || "Без названия";
      var location = document.createElement("span");
      location.className = "km-home-recs__location";
      location.textContent = card.location || "Локация не указана";
      body.appendChild(category);
      body.appendChild(title);
      body.appendChild(location);

      var actions = document.createElement("div");
      actions.className = "km-home-recs__card-actions";
      var moveUp = createIconButton("km-home-recs__move", "Переместить выше", "fas fa-arrow-left");
      var moveDown = createIconButton("km-home-recs__move", "Переместить ниже", "fas fa-arrow-right");
      var remove = createIconButton("km-home-recs__remove", "Убрать из рекомендаций", "fas fa-times");
      moveUp.disabled = index === 0;
      moveDown.disabled = index === cards.length - 1;
      moveUp.addEventListener("click", function () { moveCard(card.id, -1); });
      moveDown.addEventListener("click", function () { moveCard(card.id, 1); });
      remove.addEventListener("click", function () {
        if (isSaving) return;
        var previous = cards.slice();
        cards = cards.filter(function (item) {
          return Number(item.id) !== Number(card.id);
        });
        render();
        save(previous, "Место убрано с главной");
      });
      actions.appendChild(moveUp);
      actions.appendChild(moveDown);
      actions.appendChild(remove);

      article.appendChild(position);
      article.appendChild(handle);
      article.appendChild(media);
      article.appendChild(body);
      article.appendChild(actions);

      article.addEventListener("dragstart", function (event) {
        if (isSaving) {
          event.preventDefault();
          return;
        }
        draggedId = Number(card.id);
        article.classList.add("is-dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", String(card.id));
      });
      article.addEventListener("dragend", function () {
        draggedId = null;
        article.classList.remove("is-dragging");
        root.querySelectorAll(".is-drag-over").forEach(function (node) {
          node.classList.remove("is-drag-over");
        });
      });
      article.addEventListener("dragover", function (event) {
        if (draggedId === null || draggedId === Number(card.id)) return;
        event.preventDefault();
        article.classList.add("is-drag-over");
      });
      article.addEventListener("dragleave", function () {
        article.classList.remove("is-drag-over");
      });
      article.addEventListener("drop", function (event) {
        event.preventDefault();
        article.classList.remove("is-drag-over");
        var fromIndex = cards.findIndex(function (item) {
          return Number(item.id) === Number(draggedId);
        });
        var toIndex = cards.findIndex(function (item) {
          return Number(item.id) === Number(card.id);
        });
        if (fromIndex < 0 || toIndex < 0 || fromIndex === toIndex) return;
        var previous = cards.slice();
        var moved = cards.splice(fromIndex, 1)[0];
        cards.splice(toIndex, 0, moved);
        render();
        save(previous, "Порядок сохранён");
      });

      return article;
    }

    function createEmptySlot(index) {
      var slot = document.createElement("button");
      slot.type = "button";
      slot.className = "km-home-recs__slot-empty";
      slot.innerHTML =
        '<span class="km-home-recs__slot-number">' + String(index + 1) + '</span>' +
        '<i class="fas fa-plus" aria-hidden="true"></i>' +
        '<span>Добавить место</span>';
      slot.addEventListener("click", openDialog);
      return slot;
    }

    function render() {
      slots.innerHTML = "";
      cards.forEach(function (card, index) {
        slots.appendChild(createCard(card, index));
      });
      for (var index = cards.length; index < maxItems; index += 1) {
        slots.appendChild(createEmptySlot(index));
      }
      counter.textContent = String(cards.length) + " из " + String(maxItems);
      fallback.hidden = cards.length > 0;
      openButton.disabled = isSaving || cards.length >= maxItems;
      root.classList.toggle("is-full", cards.length >= maxItems);
    }

    async function save(previousCards, successMessage) {
      setBusy(true);
      try {
        var response = await fetch(saveUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfInput ? csrfInput.value : "",
          },
          body: JSON.stringify({ place_ids: selectedIds() }),
        });
        var payload = await response.json();
        if (!response.ok || !payload.ok) {
          throw new Error(payload.error || "Не удалось сохранить изменения.");
        }
        showStatus(successMessage || "Изменения сохранены", "success");
      } catch (error) {
        cards = previousCards;
        render();
        showStatus(error.message || "Не удалось сохранить изменения.", "error");
        if (window.kmToast) {
          window.kmToast.error(error.message || "Обновите страницу и попробуйте ещё раз.");
        }
      } finally {
        setBusy(false);
        render();
      }
    }

    function renderCandidates(results) {
      candidatesNode.innerHTML = "";
      var chosen = selectedIds();
      var available = results.filter(function (item) {
        return chosen.indexOf(Number(item.id)) === -1;
      });

      if (!available.length) {
        var empty = document.createElement("p");
        empty.className = "km-home-recs__candidates-empty";
        empty.textContent = "Подходящие места не найдены.";
        candidatesNode.appendChild(empty);
        return;
      }

      available.forEach(function (candidate) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = "km-home-recs__candidate";

        var media = document.createElement("span");
        media.className = "km-home-recs__candidate-media";
        if (candidate.image_url) {
          var image = document.createElement("img");
          image.src = candidate.image_url;
          image.alt = "";
          image.loading = "lazy";
          media.appendChild(image);
        } else {
          media.innerHTML = '<i class="far fa-image" aria-hidden="true"></i>';
        }

        var copy = document.createElement("span");
        copy.className = "km-home-recs__candidate-copy";
        var title = document.createElement("strong");
        title.textContent = candidate.title || "Без названия";
        var meta = document.createElement("span");
        meta.textContent = [candidate.category, candidate.location].filter(Boolean).join(" · ");
        copy.appendChild(title);
        copy.appendChild(meta);

        var plus = document.createElement("i");
        plus.className = "fas fa-plus km-home-recs__candidate-plus";
        plus.setAttribute("aria-hidden", "true");

        button.appendChild(media);
        button.appendChild(copy);
        button.appendChild(plus);
        button.addEventListener("click", function () {
          if (cards.length >= maxItems || isSaving) return;
          var previous = cards.slice();
          cards.push(candidate);
          render();
          closeDialog();
          save(previous, "Место добавлено на главную");
        });
        candidatesNode.appendChild(button);
      });
    }

    async function loadCandidates(query) {
      candidatesNode.innerHTML = '<div class="km-home-recs__loading"><span></span><span>Загружаем места…</span></div>';
      try {
        var url = candidatesUrl + (query ? "?q=" + encodeURIComponent(query) : "");
        var response = await fetch(url, { credentials: "same-origin" });
        var payload = await response.json();
        if (!response.ok) throw new Error("Не удалось загрузить места.");
        renderCandidates(payload.results || []);
      } catch (error) {
        candidatesNode.innerHTML = "";
        var message = document.createElement("p");
        message.className = "km-home-recs__candidates-empty";
        message.textContent = error.message || "Не удалось загрузить места.";
        candidatesNode.appendChild(message);
      }
    }

    function openDialog() {
      if (cards.length >= maxItems || isSaving) return;
      searchInput.value = "";
      if (typeof dialog.showModal === "function") {
        dialog.showModal();
      } else {
        dialog.setAttribute("open", "open");
      }
      loadCandidates("");
      window.setTimeout(function () {
        searchInput.focus();
      }, 40);
    }

    function closeDialog() {
      if (typeof dialog.close === "function") {
        dialog.close();
      } else {
        dialog.removeAttribute("open");
      }
    }

    openButton.addEventListener("click", openDialog);
    closeButton.addEventListener("click", closeDialog);
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) closeDialog();
    });
    searchInput.addEventListener("input", function () {
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(function () {
        loadCandidates(searchInput.value.trim());
      }, 260);
    });

    render();
  });
})();
