/**
 * @file map.js - main map script
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet.markercluster")}
 * @typedef {import("leaflet.locatecontrol")}
 * @typedef {import("leaflet-search")}
 * @typedef {import("leaflet-fullscreen")}
 * @typedef {import("leaflet-providers")}
 * @typedef {import("leaflet-realtime")}
 * @typedef {import("./utils.js")}
 * @typedef {import("./shapes.js")}
 * @typedef {import("./stops.js")}
 * @typedef {import("./vehicles.js")}
 * @typedef {import("./facilities.js")}
 * @exports mapsPlaceholder
 */

/**@class L.Map */

"use strict";
/**
 * @type {Array<L.Map>} mapsPlaceholder
 */
const mapsPlaceholder = [];
L.Map.addInitHook(function () {
  mapsPlaceholder.push(this);
});

/**
 * @name L.Map#findLayer
 * @memberof! L.Map.prototype
 * @description Find a layer by id
 * @param {string | L.Layer} layer the id NOT leaflet ID of the layer or the layer itself
 * @param {boolean} click  if true, the layer will be clicked
 * @param {null | integer} zoom  the zoom level to zoom to
 * @returns {L.Layer | null} the layer if found, null otherwise
 */
L.Map.prototype.findLayer = function (layer, click = false, zoom = null) {
  /** @type {L.MarkerCluster | null} */

  /**
   * @param {L.Layer} _layer
   */
  const _execLayer = (_layer) => {
    if (click) {
      _layer.fire("click");
      _layer.closeTooltip();
    }
    this.setView(_layer.getLatLng(), zoom || 15);
    return _layer;
  };
  let mcg;
  const matchWithoutZoom = Object.values(this._layers).filter((l) => {
    if (l instanceof L.MarkerClusterGroup) mcg = l; //**acceptable** side affect
    if (layer instanceof L.Layer && layer == l) return l;
    if (l.id == layer) return l;
  });
  if (matchWithoutZoom.length) return _execLayer(matchWithoutZoom[0]);
  const initialBounds = this.getBounds();
  this.fitBounds(this.options.maxBounds);
  if (!(layer instanceof L.Layer)) {
    this.eachLayer((layer_) => {
      if (layer_?.id == layer) {
        _execLayer(layer_);
        layer = layer_;
      }
    });
  } else {
    _execLayer(layer);
  }
  if (!(layer instanceof L.Layer)) layer = null;
  if (mcg) mcg.enableClustering();
  if (!layer || !zoom) this.fitBounds(initialBounds);
  return layer;
};

window.addEventListener("load", function () {
  const ROUTE_TYPE = window.location.href.split("/").slice(-2)[0];
  document.addEventListener("click", function (event) {
    if (!event.target.closest(".nav")) {
      const menuToggle = document.getElementById("menu-toggle");
      if (menuToggle.checked) menuToggle.checked = false;
    }
  });
  createMap("map", ROUTE_TYPE);
  addSidebarDrag();
});

/** map factory function for map.html
 * @param {string} id - id of the map div
 * @param {string} route_type - route type
 * @returns {L.map} map
 */
function createMap(id, route_type) {
  const isMobile = window.mobileCheck();
  const textboxSize = {
    maxWidth: 375,
    minWidth: 250,
  };

  const map = L.map(id, {
    minZoom: 9,
    maxZoom: 20,
    maxBounds: L.latLngBounds(L.latLng(40, -74), L.latLng(44, -69)),
    fullscreenControl: true,
    fullscreenControlOptions: {
      position: "topleft",
    },
    attributionControl: true,
  }).setView(
    [getDefaultCookie("lat", 42.3519), getDefaultCookie("lng", -71.0552)],
    getDefaultCookie("zoom", route_type == "commuter_rail" ? 10 : 13)
  );
  map.on("move", function () {
    const cords = map.getCenter();
    setCookie("lat", cords.lat);
    setCookie("lng", cords.lng);
  });

  map.on("zoom", () => {
    setCookie("zoom", map.getZoom());
  });

  // map.on("resize", (e) => {
  //   console.log("resized");
  // });

  const baseLayers = getBaseLayerDict(...Array(2));
  baseLayers[getDefaultCookie("darkMode", "light", 90)].addTo(map);
  const stop_layer = L.layerGroup(undefined, { name: "stops" }).addTo(map);
  const shape_layer = L.layerGroup(undefined, { name: "shapes" }).addTo(map);
  const vehicle_layer = L.markerClusterGroup({
    disableClusteringAtZoom: route_type == "commuter_rail" ? 10 : 12,
    name: "vehicles",
  }).addTo(map);
  const parking_lots = L.layerGroup(undefined, { name: "parking" });

  plotStops({
    url: "stops",
    layer: stop_layer,
    textboxSize: textboxSize,
    isMobile: isMobile,
  });
  plotShapes({
    url: "shapes",
    layer: shape_layer,
    textboxSize: textboxSize,
    isMobile: isMobile,
  });
  plotVehicles({
    url: "vehicles?include=route,next_stop,stop_time,trip_properties",
    layer: vehicle_layer,
    textboxSize: textboxSize,
    isMobile: isMobile,
    // sidebar: sidebar,
  });
  plotFacilities({
    url: `parking`,
    layer: parking_lots,
    textboxSize: textboxSize,
    isMobile: isMobile,
  });

  createControlLayers(
    baseLayers,
    stop_layer,
    shape_layer,
    vehicle_layer,
    parking_lots
  ).forEach((control) => control.addTo(map));

  map.on("zoomend", function () {
    if (map.getZoom() < 16) map.removeLayer(parking_lots);
    if (map.getZoom() >= 16) map.addLayer(parking_lots);
  });

  map.on("baselayerchange", function (event) {
    setCookie("darkMode", event.name, 90);
  });

  if (map.hasLayer(parking_lots)) map.removeLayer(parking_lots);

  // setTimeout(() => {
  //   sidebar.open("summary_");
  // }, 2000);

  return map;
}
/** create control layers
 * @param {Object} tile_layers - base layers
 * @param {L.layerGroup[]} layers - layers to be added to the map
 * @returns {Array} control layers
 */
function createControlLayers(tile_layers, ...layers) {
  const locateControl = L.control.locate({
    enableHighAccuracy: true,
    initialZoomLevel: 15,
    metric: false,
    markerStyle: {
      zIndexOffset: 500,
    },
  });
  const searchContainerId = "findBox";
  /**@type {L.Control} */
  const controlSearch = L.control.search({
    layer: L.layerGroup(layers),
    container: searchContainerId,
    initial: false,
    propertyName: "searchName",
    zoom: 16,
    marker: false,
    textPlaceholder: "",
  });
  controlSearch.on("search:locationfound", function (event) {
    event.layer.openPopup();
  });

  window.addEventListener("keydown", (keyEvent) => {
    if (
      (keyEvent.code === "F3" ||
        ((keyEvent.ctrlKey || keyEvent.metaKey) && keyEvent.code === "KeyF")) &&
      !window.mobileCheck()
    ) {
      keyEvent.preventDefault();
      controlSearch._button.click();
    }
  });

  const layerControl = L.control.layers(
    tile_layers,
    Object.fromEntries(layers.map((layer) => [layer.options?.name, layer]))
  );

  return [locateControl, layerControl, controlSearch];
}

/** Get base layer dictionary
 * @summary Get base layer dictionary
 * @param {string} lightId - id of light layer
 * @param {string} darkId - id of dark layer
 * @param {object} additionalLayers - additional layers to add to dictionary
 * @returns {object} - base layer dictionary
 */
function getBaseLayerDict(
  lightId = "CartoDB.Positron",
  darkId = "CartoDB.DarkMatter",
  additionalLayers = {}
) {
  const options = {
    attribution:
      "<a href='https://www.openstreetmap.org/copyright' target='_blank' rel='noopener'>open street map</a> @ <a href='https://carto.com/attribution' target='_blank' rel='noopener'>carto</a>",
  };
  const baseLayers = {
    light: L.tileLayer.provider(lightId, options),
    dark: L.tileLayer.provider(darkId, options),
  };

  for (const [key, value] of Object.entries(additionalLayers)) {
    baseLayers[key] = L.tileLayer.provider(value);
  }

  return baseLayers;
}

function addSidebarDrag() {
  const minWidth = 450; // minimum sidebar width
  setCssVar(
    "--sidebar-width",
    getDefaultCookie("sidebarWidth", `${minWidth}px`, 2)
  );
  const sidebar = document.getElementById("sidebar");
  const sidebarHandle = document.getElementById("sidebar-handle");

  function resize(e) {
    document.body.classList.add("noselect");
    const size = parseInt(getStyle(document.body, "width").trimEnd("px")) - e.x;
    if (size < minWidth || size > window.innerWidth) return;
    setCssVar("--sidebar-width", `${size}px`);
    setCookie("sidebarWidth", `${size}px`, 1);
  }

  sidebarHandle.addEventListener("mousedown", (event) => {
    document.addEventListener("mousemove", resize, false);
    document.addEventListener(
      "mouseup",
      () => {
        document.removeEventListener("mousemove", resize, false);
        document.body.classList.remove("noselect");
      },
      false
    );
  });
}

/**
 * Set sidebar content
 * @param {string} content - content to set
 * @param {"sidebar-content" | "sidebar-default-content" | HTMLElement} id - id of the sidebar
 * @returns {void}
 */
function setSideBarContent(content, id = "sidebar-content") {
  const sidebar = typeof id === "string" ? document.getElementById(id) : id;
  if (
    !sidebar ||
    !["sidebar-content", "sidebar-default-content"].includes(sidebar.id)
  ) {
    console.error("Sidebar not found");
    return;
  }
  sidebar.classList.remove("hidden");
  document
    .getElementById(
      sidebar.id === "sidebar-content"
        ? "sidebar-default-content"
        : "sidebar-content"
    )
    .classList.add("hidden");

  sidebar.innerHTML = content;
}
