const ROUTE_COLOR_DICT = {
  subway: "#00843D",
  rapid_transit: "#DA291C",
  commuter_rail: "#80276C",
  bus: "#FFC72C",
  ferry: "#008EAA",
  all_routes: "#7C878E",
};

window.mobileCheck = function () {
  /** Check if user is on mobile
   * @returns {boolean} - whether or not user is on mobile
   */
  let check = false;
  (function (a) {
    if (
      /(android|bb\d+|meego).+mobile|avantgo|bada\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\.(browser|link)|vodafone|wap|windows ce|xda|xiino/i.test(
        a
      ) ||
      /1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\-(n|u)|c55\/|capi|ccwa|cdm\-|cell|chtm|cldc|cmd\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\-s|devi|dica|dmob|do(c|p)o|ds(12|\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\-|_)|g1 u|g560|gene|gf\-5|g\-mo|go(\.w|od)|gr(ad|un)|haie|hcit|hd\-(m|p|t)|hei\-|hi(pt|ta)|hp( i|ip)|hs\-c|ht(c(\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\-(20|go|ma)|i230|iac( |\-|\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\/)|klon|kpt |kwc\-|kyo(c|k)|le(no|xi)|lg( g|\/(k|l|u)|50|54|\-[a-w])|libw|lynx|m1\-w|m3ga|m50\/|ma(te|ui|xo)|mc(01|21|ca)|m\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\-2|po(ck|rt|se)|prox|psio|pt\-g|qa\-a|qc(07|12|21|32|60|\-[2-7]|i\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\-|oo|p\-)|sdk\/|se(c(\-|0|1)|47|mc|nd|ri)|sgh\-|shar|sie(\-|m)|sk\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\-|v\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\-|tdg\-|tel(i|m)|tim\-|t\-mo|to(pl|sh)|ts(70|m\-|m3|m5)|tx\-9|up(\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\-|your|zeto|zte\-/i.test(
        a.substr(0, 4)
      )
    )
      check = true;
  })(navigator.userAgent || navigator.vendor || window.opera);
  return check;
};

function hoverImage(image_id, interval = 250) {
  /** Scale image up by 7% on hover
   * @param {string} image_id - id of image to scale
   * @param {number} interval - time in ms to scale image
   * @returns {void}
   */

  const image = document.getElementById(image_id);
  image.animate({ transform: "scale(1.07)" }, interval).onfinish = function () {
    image.style.transform = "scale(1.07)";
  };
}

function unhoverImage(image_id, interval = 250) {
  /** Scale image down by 7% on unhover
   * @param {string} image_id - id of image to scale
   * @param {number} interval - time in ms to scale image
   * @returns {void}
   */
  const image = document.getElementById(image_id);
  image.animate({ transform: "scale(1)" }, interval).onfinish = function () {
    image.style.transform = "scale(1)";
  };
}
function openMiniPopup(popupId) {
  /** Open mini popup
   * @param {string} popupId - id of popup to open
   * @returns {void}
   */
  const miniPopup = document.getElementById(popupId);
  miniPopup.classList.toggle("show");
}

function titleCase(str, split = "_") {
  /** Title case a string
   * @param {string} str - string to title case
   * @param {string} split - character to split string on
   * @returns {string} - title cased string
   */
  return str
    .toLowerCase()
    .split(split)
    .map(function (word) {
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}

function setFavicon(route_type) {
  /** Set favicon to route type
   * @param {string} route_type - route type to set favicon to
   * @returns {void}
   */
  for (let link of document.getElementsByTagName("link")) {
    if (link.rel in ["shortcut_icon", "apple-touch-icon", "mask-icon"]) {
      link.href = `${window.href}/static/img/${route_type.toLowerCase()}.ico`;
    }
    if (link.rel == "icon") {
      link.href = `${route_type.toLowerCase()}/static/img/${route_type.toLowerCase()}.png`;
    }
  }
}

function setDescriptions(route_type) {
  /** Set descriptions to route type
   * @param {string} route_type - route type to set descriptions to
   * @returns {void}
   */

  for (const [key, value] of Object.entries({
    description: "name",
    "og:description": "property",
    "twitter:description": "name",
  })) {
    document
      .querySelector(`meta[${value}="${key}"]`)
      .setAttribute(
        "content",
        "MBTA Realtime map for the MBTA's " + titleCase(route_type) + "."
      );
  }
}

function setUrls() {
  /** Set urls to route type
   * @returns {void}
   */

  for (const [key, value] of Object.entries({
    "og:url": "property",
    "twitter:url": "name",
  })) {
    document
      .querySelector(`meta[${value}="${key}"]`)
      .setAttribute("content", window.location.href);
  }
}

function setTitles(route_type) {
  /** Set titles to title string
   * @param {string} titleString - title string to set titles to
   * @returns {void}
   */
  document.title = "MBTA " + titleCase(route_type) + " Realtime Map";

  for (const [key, value] of Object.entries({
    "og:title": "property",
    "twitter:title": "name",
  })) {
    document
      .querySelector(`meta[${value}="${key}"]`)
      .setAttribute("content", document.title);
  }
}

function setImages(route_type) {
  /** Set images to route type
   * @param {string} route_type - route type to set images to
   * @returns {void}
   */

  for (const [key, value] of Object.entries({
    "og:image": "property",
    "twitter:image": "name",
  })) {
    document.querySelector(`meta[${value}="${key}"]`).setAttribute(
      "content",
      `/${window.href}/static/img/${route_type.toLowerCase()}.png`
      // `{{ url_for('static', filename='img/${route_type.toLowerCase()}.png') }}`
    );
  }
}

function setNavbar(navbarId, route_type, mobile = false) {
  /** Set navbar to route type
   * @param {string} navbarId - id of navbar to set
   * @param {string} route_type - route type to set navbar to
   * @param {boolean} mobile - whether or not to display navbar on mobile
   * @returns {void}
   */

  let navbar = document.getElementById(navbarId);
  const accent_color = ROUTE_COLOR_DICT[route_type.toLowerCase()];

  if (inIframe()) {
    navbar.style.display = "none";
    return;
  }

  navbar.style.borderBottom = `4px solid ${accent_color}`;

  for (let child of navbar.childNodes) {
    if (child.nodeName == "#text") continue;

    const childAccentColor = ROUTE_COLOR_DICT[child.id] || accent_color;

    if (mobile && child.id != route_type.toLowerCase() && child.id != "home") {
      navbar.removeChild(child);
    }

    if (child.id == route_type.toLowerCase()) {
      child.href = "#";
      child.style.color = accent_color;

      child.addEventListener(
        "mouseenter",
        function (event) {
          event.target.animate({ color: "#f2f2f2" }, 125).onfinish =
            function () {
              event.target.style.color = "#f2f2f2";
            };
        },
        false
      );

      child.addEventListener(
        "mouseleave",
        function (event) {
          event.target.animate({ color: accent_color }, 125).onfinish =
            function () {
              event.target.style.color = accent_color;
            };
        },
        false
      );
    }

    child.addEventListener(
      "mouseenter",
      function (event) {
        event.target.animate({ background: childAccentColor }, 125).onfinish =
          function () {
            event.target.style.background = childAccentColor;
          };
      },
      false
    );
    child.addEventListener(
      "mouseleave",
      function (event) {
        event.target.animate({ background: "none" }, 125).onfinish =
          function () {
            event.target.style.background = "none";
          };
      },
      false
    );
  }
}

function inIframe() {
  /** Check if user is in iframe
   * @returns {boolean} - whether or not user is in iframe
   */
  try {
    return window.self !== window.top;
  } catch (e) {
    return true;
  }
}

function plotVehicles(url, layer) {
  /** Plot vehicles on map in realtime, updating every 15 seconds
   * @param {string} url - url to geojson
   * @param {L.layerGroup} layer - layer to plot vehicles on
   * @returns {L.realtime} - realtime layer
   */

  const realtime = L.realtime(url, {
    // interval: !["BUS", "ALL_ROUTES"].includes(ROUTE_TYPE) ? 15000 : 45000,
    interval: 15000,
    type: "FeatureCollection",
    container: layer,
    cache: false,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      const icon = L.divIcon({
        html: f.properties.icon,
        iconSize: [15, 15],
      });
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
      l.setIcon(icon);
      l.setZIndexOffset(100);
    },
  });

  realtime.on("update", function (e) {
    Object.keys(e.update).forEach(
      function (id) {
        const layer = this.getLayer(id);
        const feature = e.update[id];
        const wasOpen = layer.getPopup().isOpen();
        layer.unbindPopup();
        if (wasOpen) layer.closePopup();
        layer.bindPopup(feature.properties.popupContent, {
          maxWidth: "auto",
        });
        layer.setIcon(
          L.divIcon({
            html: feature.properties.icon,
            iconSize: [15, 15],
          })
        );
        if (wasOpen) layer.openPopup();
      }.bind(this)
    );
  });
  return realtime;
}

function plotStops(url, layer) {
  /** Plot stops on map in realtime, updating every hour
   * @param {string} url - url to geojson
   * @param {L.layerGroup} layer - layer to plot stops on
   * @returns {L.realtime} - realtime layer
   */

  const stopIcon = L.icon({
    iconUrl: "static/img/mbta.png",
    iconSize: [15, 15],
  });

  const realtime = L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
      l.setIcon(stopIcon);
      l.setZIndexOffset(-100);
    },
  });

  realtime.on("update", handleUpdateEvent);
  return realtime;
}

function plotShapes(url, layer, interactive = true) {
  /** Plot shapes on map in realtime, updating every hour
   * @param {string} url - url to geojson
   * @param {L.layerGroup} layer - layer to plot shapes on
   * @param {boolean} interactive - whether or not to make shapes interactive
   * @returns {L.realtime} - realtime layer
   */
  const polyLineRender = L.canvas({ padding: 0.5, tolerance: 10 });

  const realtime = L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.setStyle({
        color: f.properties.color,
        opacity: f.properties.opacity,
        weight: 1.3,
        renderer: polyLineRender,
      });
      if (interactive) {
        l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
        l.bindTooltip(f.properties.name);
      }
    },
  });

  realtime.on("update", handleUpdateEvent);
  return realtime;
}

function plotFacilities(url, layer) {
  /** Plot facilities on map in realtime, updating every hour
   * @param {string} url - url to geojson
   * @param {L.layerGroup} layer - layer to plot facilities on
   * @returns {L.realtime} - realtime layer
   */

  const facilityIcon = L.icon({
    iconUrl: "static/img/parking.png",
    iconSize: [15, 15],
  });

  const realtime = L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
      l.setIcon(facilityIcon);
      l.setZIndexOffset(-150);
    },
  });
  realtime.on("update", handleUpdateEvent);
  return realtime;
}

function handleUpdateEvent(entity) {
  /** Handle update event for realtime layers
   * @param {L.realtime}
   * @returns {void}
   */
  Object.keys(entity.update).forEach(
    function (id) {
      const feature = entity.update[id];
      updateLayer.call(this, id, feature);
    }.bind(this)
  );
}

function updateLayer(id, feature) {
  /** Update layer
   * @param {string} id - id of layer to update
   * @param {L.feature}
   * @returns {void}
   */
  const layer = this.getLayer(id);
  const wasOpen = layer.getPopup().isOpen();
  layer.unbindPopup();

  if (wasOpen) layer.closePopup();

  layer.bindPopup(feature.properties.popupContent, {
    maxWidth: "auto",
  });

  if (wasOpen) layer.openPopup();
}

function getBaseLayerDict(
  lightId = "CartoDB.Positron",
  darkId = "CartoDB.DarkMatter",
  additionalLayers = {}
) {
  /** Get base layer dictionary
   * @summary Get base layer dictionary
   * @param {string} lightId - id of light layer
   * @param {string} darkId - id of dark layer
   * @param {object} additionalLayers - additional layers to add to dictionary
   * @returns {object} - base layer dictionary
   */

  const baseLayers = {
    Light: L.tileLayer.provider(lightId),
    Dark: L.tileLayer.provider(darkId),
  };

  for (const [key, value] of Object.entries(additionalLayers)) {
    baseLayers[key] = L.tileLayer.provider(value);
  }

  return baseLayers;
}

// const positron = L.tileLayer(
//   "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
//   {
//     // attribution:
//     //   '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
//     subdomains: "abcd",
//     maxZoom: 20,
//   }
// );

// const darkMatter = L.tileLayer(
//   "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
//   {
//     // attribution:
//     //   '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
//     subdomains: "abcd",
//     maxZoom: 20,
//   }
// );
