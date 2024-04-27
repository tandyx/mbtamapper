/**
 * @file map.js - main map script
 */
window.addEventListener("load", function () {
  const ROUTE_TYPE = window.location.href.split("/").slice(-2)[0];
  document.addEventListener("click", function (event) {
    // Check if the clicked element is not inside the navbar
    if (!event.target.closest(".nav")) {
      // Close the hamburger menu
      let menuToggle = document.getElementById("menu-toggle");
      if (menuToggle.checked) {
        menuToggle.checked = false;
      }
    }
  });
  createMap("map", ROUTE_TYPE);
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
  }).setView([42.3519, -71.0552], route_type == "commuter_rail" ? 10 : 13);

  const baseLayers = getBaseLayerDict(...Array(2));
  baseLayers[getDefaultCookie("darkMode", "light")].addTo(map);
  let stop_layer = L.layerGroup().addTo(map);
  stop_layer.name = "stops";

  let shape_layer = L.layerGroup().addTo(map);
  shape_layer.name = "shapes";

  let vehicle_layer = L.markerClusterGroup({
    disableClusteringAtZoom: route_type == "commuter_rail" ? 10 : 12,
  }).addTo(map);
  vehicle_layer.name = "vehicles";

  let parking_lots = L.layerGroup();
  parking_lots.name = "parking";

  plotStops({
    url: "stops",
    layer: stop_layer,
    textboxSize: textboxSize,
    isMobile: isMobile,
  });
  plotShapes({
    url: "shapes",
    layer: shape_layer,
    textboxSize: {
      maxWidth: textboxSize.maxWidth + 175,
      minWidth: textboxSize.minWidth,
    },
    isMobile: isMobile,
  });
  plotVehicles({
    url: "vehicles?include=route,next_stop,stop_time",
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
    setCookie("darkMode", event.name);
  });

  if (map.hasLayer(parking_lots)) map.removeLayer(parking_lots);

  // setTimeout(() => {
  //   sidebar.open("summary_");
  // }, 2000);

  return map;
}
/** create control layers
 * @param {Object} tile_layers - base layers
 * @param {L.layerGroup} layers - layers to be added to the map
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

  const controlSearch = L.control.search({
    layer: L.layerGroup(layers),
    initial: false,
    propertyName: "name",
    zoom: 16,
    marker: false,
    textPlaceholder: "",
  });
  controlSearch.on("search:locationfound", function (event) {
    event.layer.openPopup();
  });

  const layerControl = L.control.layers(
    tile_layers,
    Object.fromEntries(layers.map((layer) => [layer.name, layer]))
  );

  return [locateControl, controlSearch, layerControl];
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
  const baseLayers = {
    light: L.tileLayer.provider(lightId),
    dark: L.tileLayer.provider(darkId),
  };

  for (const [key, value] of Object.entries(additionalLayers)) {
    baseLayers[key] = L.tileLayer.provider(value);
  }

  return baseLayers;
}

/**
 * @param {L.map} map - Leaflet map object
 * @param {boolean} show - Whether to show the sidebar
 * @param {Object} options - Options for the sidebar
 * @returns {L.control.sidebar} sidebar
 */
function addSidebar(map, show = true, options = {}) {
  const sidebar = L.control.sidebar(options);
  if (show) sidebar.addTo(map);
  return sidebar;
}

// document.getElementById("edit2").addEventListener("click", function () {
//   document.getElementById("edit2").classList.add("hidden");
//   document.getElementById("check2").classList.remove("hidden");
//   document.getElementById("move2").classList.remove("hidden");
//   document.getElementById("move2").classList.add("visible");
// });

// document.getElementById("check2").addEventListener("click", function () {
//   document.getElementById("check2").classList.add("hidden");
//   document.getElementById("edit2").classList.remove("hidden");
//   document.getElementById("move2").classList.add("hidden");
//   document.getElementById("move2").classList.remove("visible");
// });

// for (const element of document.querySelectorAll(".edit")) {
//   element.addEventListener("click", function () {
//     element.classList.add("hidden");
//     element.nextElementSibling.classList.remove("hidden");
//     element.nextElementSibling.nextElementSibling.classList.remove("hidden");
//     element.nextElementSibling.nextElementSibling.classList.add("visible");
//   });
// }
