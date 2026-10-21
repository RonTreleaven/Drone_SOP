(function () {
  "use strict";

  var DATA_URL = "data/vnc-key.json";
  var cards = [];
  var activeCardIndex = -1;

  var elements = {
    loadError: document.getElementById("load-error"),
    status: document.getElementById("app-status"),
    layout: document.querySelector(".content-layout"),
    toc: document.getElementById("toc"),
    viewer: document.getElementById("viewer"),
    topicList: document.getElementById("topic-list"),
    tocCount: document.getElementById("toc-count"),
    search: document.getElementById("topic-search"),
    clearSearch: document.getElementById("clear-search"),
    noResults: document.getElementById("no-results"),
    cardTitle: document.getElementById("card-title"),
    category: document.getElementById("card-category"),
    sourceMeta: document.getElementById("source-meta"),
    image: document.getElementById("card-image"),
    interpretation: document.getElementById("card-interpretation"),
    significance: document.getElementById("card-significance"),
    references: document.getElementById("card-references"),
    verification: document.getElementById("card-verification"),
    position: document.getElementById("card-position"),
    previous: document.getElementById("previous-card"),
    next: document.getElementById("next-card"),
    returnToToc: document.getElementById("return-to-toc"),
    imageEnlarge: document.getElementById("image-enlarge"),
    imageDialog: document.getElementById("image-dialog"),
    closeImage: document.getElementById("close-image"),
    fullImage: document.getElementById("full-image"),
    imageCaption: document.getElementById("full-image-caption")
  };

  function setStatus(message) {
    elements.status.textContent = message;
  }

  function createElement(tagName, className, text) {
    var node = document.createElement(tagName);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function buildToc(query) {
    var normalized = query.trim().toLocaleLowerCase();
    var visible = cards.filter(function (card) {
      var haystack = [
        card.title,
        card.category,
        card.interpretation,
        card.rpasSignificance,
        card.keywords.join(" ")
      ].join(" ").toLocaleLowerCase();
      return !normalized || haystack.indexOf(normalized) !== -1;
    });
    var groups = [];

    visible.forEach(function (card) {
      var group = groups.find(function (candidate) {
        return candidate.name === card.category;
      });
      if (!group) {
        group = { name: card.category, cards: [] };
        groups.push(group);
      }
      group.cards.push(card);
    });

    elements.topicList.replaceChildren();
    groups.forEach(function (group) {
      var section = createElement("section", "topic-group");
      var heading = createElement("h3", "topic-group-title", group.name);
      var list = createElement("div", "topic-group-items");
      heading.id = "group-" + group.name.toLowerCase().replace(/[^a-z0-9]+/g, "-");
      list.setAttribute("aria-labelledby", heading.id);
      group.cards.forEach(function (card) {
        var button = createElement("button", "topic-link");
        button.append(createElement("span", "topic-number", String(cards.indexOf(card) + 1)), card.title);
        button.type = "button";
        button.dataset.cardId = card.id;
        if (cards[activeCardIndex] && cards[activeCardIndex].id === card.id) {
          button.setAttribute("aria-current", "page");
        }
        button.addEventListener("click", function () {
          selectCardById(card.id, true);
        });
        list.appendChild(button);
      });
      section.append(heading, list);
      elements.topicList.appendChild(section);
    });

    elements.tocCount.textContent = normalized ? visible.length + " of " + cards.length : cards.length + " topics";
    elements.noResults.hidden = visible.length !== 0;
    elements.clearSearch.hidden = !elements.search.value;
  }

  function makeReferenceList(references) {
    elements.references.replaceChildren();
    references.forEach(function (reference) {
      var item = document.createElement("li");
      var link = document.createElement("a");
      link.href = reference.url;
      link.textContent = reference.label;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      item.appendChild(link);
      elements.references.appendChild(item);
    });
  }

  function selectCard(index, updateHash) {
    if (index < 0 || index >= cards.length) return;
    activeCardIndex = index;
    var card = cards[index];
    var image = card.image;

    elements.viewer.hidden = false;
    elements.cardTitle.replaceChildren(createElement("span", "card-number", String(index + 1)), card.title);
    elements.category.textContent = card.category;
    elements.sourceMeta.textContent = "Source: infographic page " + card.sourcePage + ", panel " + card.sourcePanel;
    elements.image.src = image;
    elements.image.alt = card.title + " — panel " + card.sourcePanel + " from page " + card.sourcePage + " of the Drone_SOP VNC Quick Key infographic";
    elements.interpretation.textContent = card.interpretation;
    elements.significance.textContent = card.rpasSignificance;
    elements.verification.textContent = card.verificationStatus;
    elements.position.textContent = (index + 1) + " / " + cards.length;
    elements.previous.disabled = index === 0;
    elements.next.disabled = index === cards.length - 1;
    elements.fullImage.src = image;
    elements.fullImage.alt = elements.image.alt;
    elements.imageCaption.textContent = card.title + " · page " + card.sourcePage + ", panel " + card.sourcePanel;
    makeReferenceList(card.references);
    elements.layout.classList.add("showing-viewer");
    elements.layout.classList.toggle("mobile-viewing", window.matchMedia("(max-width: 800px)").matches);
    elements.toc.hidden = false;
    buildToc(elements.search.value);
    if (updateHash && window.location.hash !== "#" + card.id) {
      window.location.hash = card.id;
    }
    if (updateHash) {
      elements.viewer.scrollIntoView({ block: "start" });
    }
    setStatus(card.title + ", card " + (index + 1) + " of " + cards.length);
  }

  function selectCardById(id, updateHash) {
    var index = cards.findIndex(function (card) {
      return card.id === id;
    });
    if (index === -1) {
      elements.loadError.hidden = false;
      elements.loadError.textContent = "That reference topic was not found. Choose a topic from the table of contents.";
      return;
    }
    elements.loadError.hidden = true;
    selectCard(index, updateHash);
  }

  function showToc(updateHash) {
    elements.viewer.hidden = true;
    elements.layout.classList.remove("showing-viewer");
    elements.layout.classList.remove("mobile-viewing");
    elements.toc.hidden = false;
    if (updateHash && window.location.hash !== "#toc") {
      window.location.hash = "toc";
    }
    setStatus("Table of contents");
    elements.toc.scrollIntoView({ block: "start" });
    elements.search.focus({ preventScroll: true });
  }

  function openImageDialog() {
    elements.imageDialog.hidden = false;
    elements.closeImage.focus();
    document.body.style.overflow = "hidden";
  }

  function closeImageDialog() {
    elements.imageDialog.hidden = true;
    document.body.style.overflow = "";
    elements.imageEnlarge.focus();
  }

  function handleHashChange() {
    var id = window.location.hash.slice(1);
    if (!id || id === "toc") {
      if (id === "toc") showToc(false);
      return;
    }
    selectCardById(decodeURIComponent(id), false);
  }

  function bindEvents() {
    elements.search.addEventListener("input", function () {
      buildToc(elements.search.value);
    });
    elements.clearSearch.addEventListener("click", function () {
      elements.search.value = "";
      buildToc("");
      elements.search.focus();
    });
    elements.previous.addEventListener("click", function () {
      selectCard(activeCardIndex - 1, true);
    });
    elements.next.addEventListener("click", function () {
      selectCard(activeCardIndex + 1, true);
    });
    elements.returnToToc.addEventListener("click", function () {
      showToc(true);
    });
    elements.imageEnlarge.addEventListener("click", openImageDialog);
    elements.closeImage.addEventListener("click", closeImageDialog);
    elements.imageDialog.addEventListener("click", function (event) {
      if (event.target === elements.imageDialog) closeImageDialog();
    });
    window.addEventListener("hashchange", handleHashChange);
    window.addEventListener("resize", function () {
      if (!elements.viewer.hidden) {
        elements.layout.classList.toggle("mobile-viewing", window.matchMedia("(max-width: 800px)").matches);
      }
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && !elements.imageDialog.hidden) {
        closeImageDialog();
        return;
      }
      if (!elements.imageDialog.hidden || elements.viewer.hidden || event.altKey || event.ctrlKey || event.metaKey) return;
      if (event.target.matches("input, textarea, select, [contenteditable='true']")) return;
      if (event.key === "ArrowLeft" && activeCardIndex > 0) {
        event.preventDefault();
        selectCard(activeCardIndex - 1, true);
      } else if (event.key === "ArrowRight" && activeCardIndex < cards.length - 1) {
        event.preventDefault();
        selectCard(activeCardIndex + 1, true);
      }
    });
  }

  function start() {
    bindEvents();
    fetch(DATA_URL)
      .then(function (response) {
        if (!response.ok) throw new Error("Request failed with status " + response.status);
        return response.json();
      })
      .then(function (data) {
        if (!Array.isArray(data) || data.length !== 25) {
          throw new Error("Expected 25 reference cards in " + DATA_URL);
        }
        cards = data;
        buildToc("");
        var initialId = decodeURIComponent(window.location.hash.slice(1));
        if (initialId && initialId !== "toc") {
          selectCardById(initialId, false);
        }
      })
      .catch(function (error) {
        elements.loadError.hidden = false;
        elements.loadError.textContent = "Unable to load the VNC reference cards. " + error.message;
        elements.tocCount.textContent = "Unavailable";
        setStatus("Reference cards could not be loaded.");
      });
  }

  start();
}());
