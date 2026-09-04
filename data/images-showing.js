(function () {
  const imagesScript = document.getElementById("product-images");
  const videosScript = document.getElementById("product-videos");
  if (!imagesScript || !videosScript) {
    return;
  }

  const color =
    (window.selectedOptions && window.selectedOptions.color) ||
    (typeof queryColor !== "undefined" ? queryColor : "");
  let allImages = [];
  let videos = [];
  try {
    allImages = JSON.parse(imagesScript.textContent || "[]");
  } catch (error) {
    console.error("Failed to parse product images:", error);
  }
  try {
    videos = JSON.parse(videosScript.textContent || "[]");
  } catch (error) {
    console.error("Failed to parse product videos:", error);
  }

  const resolveColorKey = (selectedColor) => {
    const lowerColor = (selectedColor || "").toLowerCase();
    if (lowerColor.includes("yellow")) {
      return "yellow";
    }
    if (lowerColor.includes("rose")) {
      return "rose";
    }
    if (
      lowerColor.includes("white") ||
      lowerColor.includes("platinum") ||
      lowerColor.includes("silver") ||
      lowerColor.includes("palladium")
    ) {
      return "white";
    }
    return "white";
  };

  const getImageAltKey = (entry) => {
    const lowerEntry = String(entry || "").toLowerCase();
    if (lowerEntry.includes(".alt4") || lowerEntry.includes(".alt1")) {
      return "rose";
    }
    if (lowerEntry.includes(".alt2") || (lowerEntry.includes(".alt") && !lowerEntry.includes(".alt1"))) {
      return "yellow";
    }
    return "white";
  };

  const filterImagesByColor = (items, selectedColor) => {
    const safeItems = Array.isArray(items) ? items : [];
    const baseItems = safeItems.filter((entry) => !entry.includes(".cat"));
    if (!selectedColor) {
      return baseItems;
    }

    const colorKey = resolveColorKey(selectedColor);
    const filtered = baseItems.filter((entry) => getImageAltKey(entry) === colorKey);
    return filtered.length ? filtered : baseItems;
  };

  const resolveVideoByColor = (items, selectedColor) => {
    const safeItems = Array.isArray(items) ? items : [];
    if (safeItems.length === 0) {
      return null;
    }
    const colorKey = resolveColorKey(selectedColor);
    const token = colorKey === "yellow" ? ".yellow" : colorKey === "rose" ? ".rose" : ".white";
    const match = safeItems.find((entry) => String(entry).toLowerCase().includes(token));
    return match || safeItems[0];
  };

  const extractShapeFromMedia = (media) => {
    const match = String(media || "").toLowerCase().match(/\.(rd|ov|em|sq|cu|as|ra|pe|mq|he)\./);
    return match ? match[1] : "";
  };

  const shapeLabelFromCode = (code) => {
    const map = {
      rd: "Round",
      ov: "Oval",
      em: "Emerald",
      sq: "Princess",
      cu: "Cushion",
      as: "Asscher",
      ra: "Radiant",
      pe: "Pear",
      mq: "Marquise",
      he: "Heart",
    };
    return map[String(code || "").toLowerCase()] || "";
  };

  const extractImageAngle = (src) => {
    const match = String(src || "").toLowerCase().match(/\.(set|side|angle|ver|alt)\./);
    return match ? match[1] : "";
  };

  const getProductTitle = () => {
    const cartButton = document.getElementById("cart-button");
    const title = cartButton?.dataset?.productTitle || "";
    return title || "Product";
  };

  const addKeyboardActivation = (element, handler) => {
    if (!element || typeof handler !== "function") {
      return;
    }
    element.setAttribute("role", "button");
    element.setAttribute("tabindex", "0");
    element.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        handler();
      }
    });
  };

  function filterImagesByShape(images, shapeName) {
    if (!shapeName) {
      return images;
    }
    return images.filter((image) => image.includes("." + shapeName + "."));
  }

  function updateSelectedShape() {
    const selectedShape = document.querySelector(".preview-shape-item.selectedshape");
    const shapeName = selectedShape?.dataset?.shape || "";
    if (shapeName && shapeName !== window.shapeforDL) {
      window.shapeforDL = shapeName;
    }
    return shapeName;
  }

  function filterVideosByShape(videoItems, shapeName) {
    if (!shapeName) {
      return videoItems;
    }
    return videoItems.filter((video) => video.includes("." + shapeName + "."));
  }

  const selectVideoForShape = (items, selectedShape, selectedColor) => {
    const primaryList = filterVideosByShape(items, selectedShape);
    const primaryVideo = resolveVideoByColor(primaryList, selectedColor);
    if (primaryVideo) {
      return primaryVideo;
    }
    return resolveVideoByColor(items, selectedColor);
  };

  function updateProductMedia(selectedColor) {
    let images = filterImagesByColor(allImages, selectedColor);
    const selectedShape = updateSelectedShape();
    images = filterImagesByShape(images, selectedShape);
    const assetsBox = document.getElementById("product-detail-assets");
    const showBox = document.getElementById("image-show");

    if (!assetsBox || !showBox) {
      return;
    }

    const previousActive = assetsBox.querySelector(".review-item.active");
    const previousWasVideo = Boolean(previousActive && previousActive.classList.contains("video-review"));
    const previousImageSrc = previousActive?.querySelector("img")?.getAttribute("src") || "";
    const previousAngle = extractImageAngle(previousImageSrc);

    if (!images.length) {
      images = Array.isArray(allImages) ? allImages.slice() : [];
    }

    const video = selectVideoForShape(videos, selectedShape, selectedColor);
    const videoShapeCode = extractShapeFromMedia(video);
    const videoLabel = shapeLabelFromCode(videoShapeCode) || "Round";
    const videoFallback = Boolean(selectedShape && videoShapeCode && selectedShape !== videoShapeCode);
    const hasMultipleShapePreviews =
      document.querySelectorAll("#previewshape-container .preview-shape-item").length > 1;

    const hasVideo = Boolean(video);

    const setShowVideo = () => {
      if (!video) {
        showBox.innerHTML = "";
        return;
      }
      showBox.innerHTML = `
        <video
        id="productvideo"
        class="w-full h-full object-contain left-0 top-0 mx-auto"
        style="border: none !important;"
        autoplay
        muted
        playsinline loop controls>
        <source type="video/mp4" src=${video} />
        </video>`;

      if (document.getElementById("view-full-icon")) {
        document.getElementById("view-full-icon").href = video;
      }
    };

    const setShowImage = (src) => {
      if (!src) {
        showBox.innerHTML = "";
        return;
      }
      const imgShow = document.createElement("img");
      imgShow.className = "w-full h-full object-contain";
      imgShow.src = src;
      imgShow.decoding = "async";
      imgShow.setAttribute("onclick", "magnify(event)");

      showBox.innerHTML = "";
      showBox.appendChild(imgShow);

      if (document.getElementById("view-full-icon")) {
        document.getElementById("view-full-icon").href = src;
      }
    };

    const clearActive = () => {
      assetsBox.querySelectorAll(".video-review.active, .images-review.active").forEach((el) => {
        el.classList.remove("active");
        el.setAttribute("aria-pressed", "false");
      });
    };

    const setActive = (element) => {
      clearActive();
      element.classList.add("active");
      element.setAttribute("aria-pressed", "true");
    };

    assetsBox.innerHTML = "";
    showBox.innerHTML = "";

    const productTitle = getProductTitle();

    if (hasVideo) {
      const firstVideo = document.createElement("div");
      firstVideo.className =
        "flex-1 h-24 relative bg-white overflow-hidden cursor-pointer video-review review-item";
      firstVideo.setAttribute("aria-label", `${productTitle} video preview`);
      firstVideo.setAttribute("aria-pressed", "false");
	  let vidthumby = images[0] || allImages[0] || "";
	  if (!fileURLs.toString().includes(".yellow.")) { vidthumby = vidthumby.replace(".alt", ""); }
	  if (!fileURLs.toString().includes(".rose.")) { vidthumby = vidthumby.replace(".alt1", ""); }
      firstVideo.innerHTML = `
        <img class="w-full h-full" src="${vidthumby}" loading="lazy" decoding="async" alt="${productTitle} video thumbnail" />
        <div data-property-1="Default" class="inset-0  flex justify-center items-center absolute">
          <div class="w-12 h-12 p-3 bg-white rounded-[50px] border border-gray-200 flex justify-center items-center">
            <img src="/static/img/icons/360_small.png" style="scale: 1.25">
          </div>
        </div>
        ${hasMultipleShapePreviews ? `
        <div class="absolute bottom-1 px-2 py-0.5 rounded-full bg-white/80 text-slate-500 text-[10px] font-bold font-['Lato'] leading-4 whitespace-nowrap" style="left: 50%; transform: translateX(-50%);">
          ${videoLabel} View
        </div>` : ""}
      `;
      const wrapper = document.createElement("div");
      wrapper.className = "p-1";
      wrapper.appendChild(firstVideo);
      assetsBox.appendChild(wrapper);

      const handleVideoSelect = () => {
        setShowVideo();
        setActive(firstVideo);
      };
      firstVideo.addEventListener("click", handleVideoSelect);
      addKeyboardActivation(firstVideo, handleVideoSelect);
    }

    const pickPreferredImage = (imageList, preferredSrc, preferredAngle) => {
      if (!Array.isArray(imageList) || !imageList.length) {
        return "";
      }
      if (preferredSrc && imageList.includes(preferredSrc)) {
        return preferredSrc;
      }
      if (preferredAngle) {
        const match = imageList.find((image) => image.includes(`.${preferredAngle}.`));
        if (match) {
          return match;
        }
      }
      return imageList[0];
    };

    const preferredImage = pickPreferredImage(images, previousImageSrc, previousAngle);
    const shouldPreferVideo = hasVideo && previousWasVideo && !videoFallback;
    let imageSelected = false;

    images.forEach((image) => {
      const imageBox = document.createElement("div");
      imageBox.className =
        "flex-1 h-24 relative bg-white overflow-hidden cursor-pointer hover:scale-110 images-review review-item";
      imageBox.style.transition = "all ease .3s";
      imageBox.setAttribute("aria-label", `${productTitle} image preview`);
      imageBox.setAttribute("aria-pressed", "false");
      imageBox.innerHTML = `<img class="w-24 h-24 left-0 top-0 absolute object-contain" src=${image} loading="lazy" decoding="async" alt="${productTitle} thumbnail" />`;

      const handleImageSelect = () => {
        setShowImage(image);
        setActive(imageBox);
      };
      imageBox.addEventListener("click", handleImageSelect);
      addKeyboardActivation(imageBox, handleImageSelect);
      const wrapper = document.createElement("div");
      wrapper.className = "p-1";
      wrapper.appendChild(imageBox);
      assetsBox.appendChild(wrapper);

      if (!shouldPreferVideo && !imageSelected && image === preferredImage) {
        setShowImage(image);
        setActive(imageBox);
        imageSelected = true;
      }
    });

    if (hasVideo && shouldPreferVideo) {
      setShowVideo();
      const videoTile = assetsBox.querySelector(".video-review");
      if (videoTile) {
        videoTile.classList.add("active");
      }
    } else if (!imageSelected && images.length > 0) {
      setShowImage(images[0]);
      const firstImageTile = assetsBox.querySelector(".images-review");
      if (firstImageTile) {
        setActive(firstImageTile);
      }
    }
	
	// Catch rose-less image oddity when yellow was last selected:
	const wrongselect = document.querySelector('body:has(.color-option.is-selected[data-value*="Rose"]) #product-detail-assets .active:has(img[src*=".alt."])');
	// Set the image selection & active one to white, if it's available:
	if (wrongselect) {
		const correctedlink = wrongselect.children[0].src.replace(".alt.", ".");
		if (fileURLs.includes(correctedlink)) {
			document.querySelector("#product-detail-assets .images-review:has(img[src='" + correctedlink + "'])").classList.add("active");
			wrongselect.classList.remove("active");
			setShowImage(correctedlink);
		}
	}
  }

  function setProductMedia(nextImages, nextVideos, selectedColor) {
    allImages = Array.isArray(nextImages) ? nextImages : [];
    videos = Array.isArray(nextVideos) ? nextVideos : [];
    updateProductMedia(selectedColor || "");
  }

  window.setProductMedia = setProductMedia;
  window.updateProductMedia = updateProductMedia;
  updateProductMedia(color);

  window.showShapeV2 = function showShapeV2(shape) {
    const shapeName = shape.dataset.shape;
    const shapeLabel = shape.querySelector("img")?.title || shapeName;
    const selectedShapeLabel = document.getElementById("selected-shape-name");
    if (selectedShapeLabel) {
      selectedShapeLabel.textContent = shapeLabel;
    }
    const shapeItems = document.querySelectorAll(".preview-shape-item");
    shapeItems.forEach((item) => {
      item.classList.remove("selectedshape");
      item.setAttribute("aria-pressed", "false");
    });
    shape.classList.add("selectedshape");
    shape.setAttribute("aria-pressed", "true");
    window.shapeforDL = shapeName;
    updateProductMedia(window.selectedOptions.color);
  };

  function normalizeShapeName(name) {
    return String(name || "").toLowerCase().replace(/[^a-z]/g, "");
  }

  function updateShapePreviewForRequirement(shapeName) {
    const container = document.getElementById("previewshape-container");
    if (!container || !shapeName) {
      return;
    }

    const shapeMap = {
      round: "rd",
      roundbrilliant: "rd",
      oval: "ov",
      emerald: "em",
      radiant: "ra",
      square: "sq",
      princess: "sq",
      cushion: "cu",
      asscher: "as",
      pear: "pe",
      marquise: "mq",
      heart: "he",
    };

    const candidates = String(shapeName)
      .split(/[\/,]/)
      .map((entry) => entry.trim())
      .filter(Boolean);

    for (const candidate of candidates.length ? candidates : [shapeName]) {
      const code = shapeMap[normalizeShapeName(candidate)];
      if (!code) {
        continue;
      }
      const target = container.querySelector(`.preview-shape-item[data-shape="${code}"]`);
      if (target) {
        window.showShapeV2(target);
        break;
      }
    }
  }

  window.updateShapePreviewForRequirement = updateShapePreviewForRequirement;

  let blockcancel = false;

  window.updateQRframe = function updateQRframe() {
    /*if (!window.location.pathname.endsWith("/")) {
      window.location.pathname = window.location.pathname + "/";
    }*/

    document.getElementById("QRframe").src =
      "/QRgen?img=" +
      document.querySelector("#product-detail-assets img").src +
      "&data=" +
      window.location.href;
  };

  window.notesaction = function notesaction(name, cancel) {
    let notebtn = document.querySelector(".notesbtn." + name);
    let popupname = document.querySelector(".popuphaver." + name);
    let popupinput = popupname.querySelector(".popupinput");

    // When Save is pressed...
    if (!cancel) {
      popupinput.value = popupinput.value.trim();

      // If the main input does not equal the initial value...
      if (name !== "popfingers") {
        if (popupinput.value !== popupinput.getAttribute("data-initial")) {
          notebtn.classList.add("noteadded");
        } else {
          notebtn.classList.remove("noteadded");
        }
      }

      // Set the button title, and the input stored value:
      notebtn.title = popupinput.value;
      notebtn.nextElementSibling.value = popupinput.value;
      popupinput.setAttribute("data-previous", popupinput.value);

      // If the current window is the finger size one AND variants exist AND variant style numbers end with S:
      if (
        name == "popfingers" &&
        document.querySelector("#variantticks") &&
        document.querySelector("#variantticks").children[0].getAttribute("data-stylenum").endsWith("S")
      ) {
        changevari(document.querySelector("#variantticks").value);
      }
      // If the current window is the engraving one, set the button's value to the chosen font:
      else if (name == "popengrave") {
        notebtn.nextElementSibling.nextElementSibling.value =
          popupname.querySelector("input[type='radio']:checked").value;
        notebtn.setAttribute("value", popupname.querySelector("input[type='radio']:checked").value);
        setoptions(notebtn.nextElementSibling);
        setoptions(notebtn.nextElementSibling.nextElementSibling);
      }
      // Add the value to the search:
      else {
        setoptions(notebtn.nextElementSibling);
      }

      // Set review table info:
      document.querySelector("#RT" + popupinput.name).textContent = popupinput.value;

      popdown(name);
    }
    // When cancelled and not during an input selection...
    else if (!blockcancel) {
      if (popupinput.value !== popupinput.getAttribute("data-previous")) {
        if (window.confirm("Are you sure you want to cancel? Information entered may be lost.")) {
          cancelinput();
        }
      } else {
        cancelinput();
      }
    }

    function cancelinput() {
      popdown(name);

      popupinput.value = popupinput.getAttribute("data-previous");

      // If the current window is the finger size one, set the slider's value:
      if (name == "popfingers") {
        popupname.querySelector("input[type='range']").value = popupinput.value;
        liveslider(popupname.querySelector("input[type='range']"));
      }
    }

    blockcancel = false;
  };

  window.changeImage = function changeImage() {
    const mainImage = document.getElementById("main-product-image");
    const thumbImage = document.getElementById("thumbnail-image");
    if (mainImage && thumbImage) {
      const tempSrc = mainImage.src;
      mainImage.src = thumbImage.src;
      thumbImage.src = tempSrc;
    }
  };

  const COLLECTION_CONFIG = {
    "Engagement Rings": { url: "/engagement_rings", name: "Engagement Rings" },
    Heads: { url: "/heads", name: "Heads" },
    "Mens Bands": { url: "/wedding_bands/men", name: "Mens Bands" },
    "Wedding Bands": { url: "/wedding_bands", name: "Wedding Bands" },
    "Gents Rings": { url: "/fashion_rings/men", name: "Mens Rings" },
    "Color Rings": { url: "/fashion_rings/color", name: "Color Rings" },
    "Fashion Rings": { url: "/fashion_rings", name: "Fashion Rings" },
    Bracelets: { url: "/bracelets", name: "Bracelets" },
    Earrings: { url: "/earrings", name: "Earrings" },
    Necklaces: { url: "/necklaces", name: "Necklaces" },
    Pendants: { url: "/pendants", name: "Pendants" },
    Monograms: { url: "/personalized_jewelry", name: "Personalized Jewelry" },
    "Personalized Jewelry": { url: "/personalized_jewelry", name: "Personalized Jewelry" },
  };

  const PRIORITY_ORDER = [
    "Engagement Rings",
    "Heads",
    "Mens Bands",
    "Wedding Bands",
    "Gents Rings",
    "Color Rings",
    "Fashion Rings",
    "Bracelets",
    "Earrings",
    "Necklaces",
    "Pendants",
    "Monograms",
    "Personalized Jewelry",
  ];

  function handleFashionRingsSpecialCase(httpReferer, collstring) {
    if (!httpReferer || !httpReferer.includes("fashion_rings")) {
      if (collstring.includes("Engagement Rings")) {
        return COLLECTION_CONFIG["Engagement Rings"];
      }
      if (collstring.includes("Wedding Bands")) {
        return COLLECTION_CONFIG["Wedding Bands"];
      }
      return COLLECTION_CONFIG["Fashion Rings"];
    }

    if (httpReferer.includes("/color")) {
      return { url: "/fashion_rings/color", name: "Color Rings" };
    }
    if (httpReferer.includes("/men")) {
      return { url: "/fashion_rings/men", name: "Men's Rings" };
    }
    return { url: "/fashion_rings/", name: "Fashion Rings" };
  }

  function findCollectionByPriority(collstring) {
    for (const key of PRIORITY_ORDER) {
      if (collstring.includes(key)) {
        return COLLECTION_CONFIG[key];
      }
    }
    return null;
  }

  function getCollectionInfo(collections, httpReferer = "") {
    const collstring = Array.isArray(collections) ? collections.join(",") : String(collections);

    if (
      collstring.includes("Fashion Rings") &&
      (collstring.includes("Engagement Rings") || collstring.includes("Wedding Bands"))
    ) {
      return handleFashionRingsSpecialCase(httpReferer, collstring);
    }

    const result = findCollectionByPriority(collstring);
    if (result) {
      return result;
    }

    return { url: "#", name: "Previous Page", useHistoryBack: true };
  }

  function updateBreadcrumb(collections, httpReferer = "") {
    const breadcrumbContainer = document.getElementById("breadcrumb-container");
    if (!breadcrumbContainer) {
      return;
    }

    const collstring = collections.toString();
    const result = getCollectionInfo(collstring, httpReferer);

    if (result.useHistoryBack) {
      breadcrumbContainer.href = "#";
      breadcrumbContainer.onclick = (event) => {
        event.preventDefault();
        window.history.back();
      };
    } else {
      let finalURL = result.url;
      if (typeof isIframe !== "undefined" && isIframe) {
        finalURL = "/iframes" + result.url + "?store-embed=1&customer_id=" + (new URLSearchParams(window.location.search)).get("customer_id");
      }
      breadcrumbContainer.href = finalURL;
      breadcrumbContainer.onclick = null;
    }
    breadcrumbContainer.innerHTML = `<div class="justify-start text-slate-500 text-sm font-normal font-['Lato'] leading-5">${result.name}</div>`;
  }

  const initBreadcrumb = () => {
    const productCollections = Array.isArray(window.productCollections)
      ? window.productCollections
      : typeof collections !== "undefined"
      ? collections
      : [];
    const httpReferer = document.referrer || "";
    console.log(productCollections, httpReferer);
    updateBreadcrumb(productCollections, httpReferer);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBreadcrumb);
  } else {
    initBreadcrumb();
  }
  
  //Add the image list to the merchant metadata:
  LDJSONimg();
})();