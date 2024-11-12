/**
 * @file map.js - main map script
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet.markercluster")}
 * @typedef {import("leaflet.locatecontrol")}
 * @typedef {import("leaflet-search-types")}
 * @typedef {import("leaflet-fullscreen")}
 * @typedef {import("leaflet-providers")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("./utils.js")}
 * @typedef {import("./realtime/base.js")}
 * @typedef {import("./realtime/vehicles.js")}
 * @typedef {import("./realtime/facilities.js")}
 * @typedef {import("./realtime/shapes.js")}
 * @typedef {import("./realtime/stops.js")}
 */
"use strict";
/** @type {L.Map?} */
// let map;
window.addEventListener("load", function () {
  const ROUTE_TYPE = window.location.href.split("/").slice(-2)[0];
  createMap("map", ROUTE_TYPE);
});

/** map factory function for map.html
 * @param {string} id - id of the map div
 * @param {string} route_type - route type
 * @returns {L.map} map
 */
function createMap(id, route_type) {
  const isMobile = mobileCheck();
  const theme = Theme.fromExisting();

  const textboxSize = { maxWidth: 375, minWidth: 250 };
  const map = L.map(id, {
    minZoom: 9,
    maxZoom: 20,
    maxBounds: L.latLngBounds(L.latLng(40, -74), L.latLng(44, -69)),
    fullscreenControl: true,
    fullscreenControlOptions: { position: "topleft" },
    attributionControl: true,
  }).setView(
    [
      sessionStorage.getItem("lat") || 42.3519,
      sessionStorage.getItem("lng") || -71.0552,
    ],
    sessionStorage.getItem("zoom") || route_type == "commuter_rail" ? 10 : 13
  );
  map.on("move", function () {
    const cords = map.getCenter();
    sessionStorage.setItem("lat", cords.lat);
    sessionStorage.setItem("lng", cords.lng);
  });

  map.on("zoom", () => sessionStorage.setItem("zoom", map.getZoom()));

  const baseLayers = getBaseLayerDict(...Array(2));
  baseLayers[theme.theme].addTo(map);
  const stop_layer = L.layerGroup(undefined, { name: "stops" }).addTo(map);
  const shape_layer = L.layerGroup(undefined, { name: "shapes" }).addTo(map);
  const vehicle_layer = L.markerClusterGroup({
    disableClusteringAtZoom: route_type == "commuter_rail" ? 10 : 12,
    name: "vehicles",
  }).addTo(map);

  const parking_lots = L.layerGroup(undefined, { name: "parking" });
  const baseOp = { textboxSize, isMobile };
  new StopLayer({ url: "stops", layer: stop_layer, ...baseOp }).plot();
  new ShapeLayer({ url: "shapes", layer: shape_layer, ...baseOp }).plot();
  new VehicleLayer({
    url: "vehicles?include=route,next_stop,stop_time,trip_properties",
    layer: vehicle_layer,
    ...baseOp,
  }).plot();
  new FacilityLayer({ url: "parking", layer: parking_lots, ...baseOp }).plot();

  createControlLayers(
    baseLayers,
    stop_layer,
    shape_layer,
    vehicle_layer,
    parking_lots
  ).forEach((control) => control.addTo(map));

  map.on("zoomend", () => {
    if (map.getZoom() < 16) map.removeLayer(parking_lots);
    if (map.getZoom() >= 16) map.addLayer(parking_lots);
  });
  map.on("baselayerchange", (event) => new Theme(event.name).set());

  if (map.hasLayer(parking_lots)) map.removeLayer(parking_lots);
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
    markerStyle: { zIndexOffset: 500 },
  });

  const controlSearch = L.control.search({
    layer: L.layerGroup(layers),
    initial: false,
    propertyName: "searchName",
    zoom: 16,
    marker: false,
    textPlaceholder: "search",
    autoCollapse: true,
  });

  controlSearch.on("search:locationfound", (event) => event.layer.openPopup());

  window.addEventListener("keydown", (keyEvent) => {
    if (
      keyEvent.code === "F3" ||
      ((keyEvent.ctrlKey || keyEvent.metaKey) && keyEvent.code === "KeyF")
    ) {
      keyEvent.preventDefault();
      controlSearch._input.focus();
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
 * @returns {{ light: TileLayer.Provider; dark: TileLayer.Provider}} - base layer dictionary
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
    light: L.tileLayer.provider(lightId, { id: "lightLayer", ...options }),
    dark: L.tileLayer.provider(darkId, { id: "darkLayer", ...options }),
  };

  for (const [key, value] of Object.entries(additionalLayers)) {
    baseLayers[key] = L.tileLayer.provider(value);
  }

  return baseLayers;
}
