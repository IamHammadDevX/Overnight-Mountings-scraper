(function () {
  const control = document.getElementById("color-control");
  if (!control) {
    return;
  }

  const elements = document.getElementsByClassName("color-option");

  const selectedColor =
    (window.selectedOptions && window.selectedOptions.color) ||
    (typeof queryColor !== "undefined" ? queryColor : "");

  // White-metal styles carry their metal as the color value (a Platinum
  // style has color "Platinum"), but the swatch list only renders White
  // for them — highlight the White swatch in that case.
  const whiteMetalColors = ["Platinum", "Silver", "Palladium"];

  function updateColorUI(colorValue) {
    const displayColor = whiteMetalColors.includes(String(colorValue || "").trim())
      ? "White"
      : colorValue;
    Array.from(elements).forEach((element) => {
      const chooseColor = element.getAttribute("data-value");
      const isSelected = chooseColor === displayColor;
      if (isSelected) {
        element.style.border = "1px solid #64748B";
      } else {
        element.style.border = "1px solid transparent";
      }
      element.setAttribute("aria-checked", isSelected ? "true" : "false");
      element.classList.toggle("is-selected", isSelected);
    });
  }

  window.updateColorUI = updateColorUI;
  updateColorUI(selectedColor);

  Array.from(elements).forEach((element) => {
    const chooseColor = element.getAttribute("data-value");
    element.addEventListener("click", () => {
      if (element.dataset.disabled === "true") {
        return;
      }
      updateQueryParam("color", chooseColor);
    });
    element.addEventListener("keydown", (event) => {
      if (element.dataset.disabled === "true") {
        return;
      }
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        element.click();
      }
    });
  });

  function normalizeMetalValue(value) {
    return String(value || "").trim().toLowerCase();
  }

  function updateColorState(metalValue) {
    const normalized = normalizeMetalValue(metalValue);
    const isPlatinumOrPalladium =
      normalized.includes("platinum") || normalized.includes("palladium");
    const disableRoseFor10k =
      normalized.includes("10k") ||
      normalized.includes("10 kt") ||
      /^10\s?kt?$/.test(normalized) ||
      normalized.startsWith("10");
    const options = document.getElementById("color-options");
    const disabledNote = document.getElementById("color-disabled-note");

    if (control) {
      control.dataset.disabled = isPlatinumOrPalladium ? "true" : "false";
    }

    // For Platinum/Palladium: keep options visible but disable Yellow and Rose, and activate White.
    if (options) {
      options.hidden = false;
      const whiteEls = options.querySelectorAll('.color-option[data-value="White"]');
      const yellowEls = options.querySelectorAll('.color-option[data-value="Yellow"]');
      const roseEls = options.querySelectorAll('.color-option[data-value="Rose"]');
      const allEls = options.querySelectorAll(".color-option");

      const toggleDisabledFor = (els, shouldDisable) => {
        els.forEach((el) => {
          if (shouldDisable) {
            el.dataset.disabled = "true";
            el.style.opacity = "0.45";
            el.style.pointerEvents = "none";
            el.setAttribute("aria-disabled", "true");
            el.setAttribute("tabindex", "-1");
          } else {
            delete el.dataset.disabled;
            el.style.opacity = "";
            el.style.pointerEvents = "";
            el.removeAttribute("aria-disabled");
            el.setAttribute("tabindex", "0");
          }
        });
      };

      toggleDisabledFor(yellowEls, isPlatinumOrPalladium);
      toggleDisabledFor(roseEls, isPlatinumOrPalladium);
      // ensure White is enabled
      toggleDisabledFor(whiteEls, false);
      if (isPlatinumOrPalladium) {
        allEls.forEach((el) => {
          const value = (el.getAttribute("data-value") || "").trim().toLowerCase();
          const isAllowed = ["white"].includes(value);
          toggleDisabledFor([el], !isAllowed);
        });
      }

      // If Platinum/Palladium, make White the active selection
      if (isPlatinumOrPalladium) {
        const params = new URLSearchParams(window.location.search);
        const currentColor = (params.get("color") || window.selectedOptions?.color || "")
          .trim()
          .toLowerCase();
        const allowedColors = ["white", "platinum", "palladium"];
        if (!currentColor || !allowedColors.includes(currentColor)) {
          if (typeof updateQueryParam === "function") {
            updateQueryParam("color", "White");
          } else {
            updateColorUI("White");
          }
        }
      }
    }

    // Hide the generic disabled note (we now disable specific colors instead)
    if (disabledNote) {
      disabledNote.hidden = true;
    }

    // Disable Rose option when metal is 10K (legacy rule) — keep existing behavior
    const roseElsLegacy = document.querySelectorAll(
      '.color-option[data-value*="Rose"], .color-option[data-value="Tricolor"]'
    );
    if (roseElsLegacy && roseElsLegacy.length > 0) {
      roseElsLegacy.forEach((el) => {
        if (disableRoseFor10k) {
          el.dataset.disabled = "true";
          el.style.opacity = "0.45";
          el.style.pointerEvents = "none";
          el.setAttribute("aria-disabled", "true");
          el.setAttribute("tabindex", "-1");
        } else if (!isPlatinumOrPalladium) {
          delete el.dataset.disabled;
          el.style.opacity = "";
          el.style.pointerEvents = "";
          el.removeAttribute("aria-disabled");
          el.setAttribute("tabindex", "0");
        }
      });

      if (disableRoseFor10k) {
        const params = new URLSearchParams(window.location.search);
        const currentColor = params.get("color") || window.selectedOptions?.color;
        const normalized = String(currentColor || "").trim().toLowerCase();
        if (normalized && (normalized.includes("rose") || normalized === "tricolor")) {
          const enabled = Array.from(document.querySelectorAll(".color-option")).find(
            (el) => !el.dataset.disabled
          );
          const fallback = enabled ? enabled.getAttribute("data-value") : "White";
          if (typeof updateQueryParam === "function") {
            updateQueryParam("color", fallback);
          }
        }
      }
    }
  }

  window.updateColorState = updateColorState;
  const initialMetal =
    new URLSearchParams(window.location.search).get("metal") ||
    window.selectedOptions?.metal ||
    (typeof currentdefaults !== "undefined" ? currentdefaults[0] : "");
  updateColorState(initialMetal);

  function hasColorPreviewImages(urls) {
    if (!Array.isArray(urls) || !urls.length) {
      return false;
    }
    return urls.some((entry) => typeof entry === "string" && entry.includes(".alt"));
  }

  function updateColorPreviewNote() {
    const note = document.getElementById("color-no-previews");
    if (!note) {
      return;
    }
    const colorOptions = document.querySelectorAll("#color-options .color-option");
    const hasMultipleColors = colorOptions.length > 1;
    const urls = Array.isArray(window.fileURLs)
      ? window.fileURLs
      : typeof fileURLs !== "undefined"
      ? fileURLs
      : [];
    const showNote = hasMultipleColors && !hasColorPreviewImages(urls);
    note.classList.toggle("hidden", !showNote);
  }

  window.updateColorPreviewNote = updateColorPreviewNote;
  updateColorPreviewNote();
})();
