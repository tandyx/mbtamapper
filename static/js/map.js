/**
 * @file map.js - main map script
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet.markercluster")}
 * @typedef {import("leaflet.locatecontrol")}
 * @typedef {import("leaflet-search-types")}
 * @typedef {import("leaflet-fullscreen")}
 * @typedef {import("leaflet-providers")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("leaflet-sidebar")}
 * @typedef {import("./utils.js")}
 * @typedef {import("./realtime/base.js")}
 * @typedef {import("./realtime/vehicles.js")}
 * @typedef {import("./realtime/facilities.js")}
 * @typedef {import("./realtime/shapes.js")}
 * @typedef {import("./realtime/stops.js")}
 */
"use strict";

window.addEventListener("load", function () {
  const ROUTE_TYPE = window.location.href.split("/").slice(-2)[0];
  createMap("map", ROUTE_TYPE);
});

window.addEventListener("load", function () {
  if (inIframe()) {
    setCssVar("--navbar-height", "0px");
    this.document.getElementsByTagName("nav")[0].remove();
  }
  Theme.fromExisting().set(sessionStorage, onThemeChange);
});

window.addEventListener("hashchange", () => {
  document.getElementById(window.location.hash.slice(1)).click();
});
/** map factory function for map.html
 * @param {string} id - id of the map div
 * @param {string} routeType - route type
 * @returns {L.map} map
 */
function createMap(id, routeType) {
  const isMobile = mobileCheck();
  const isIframe = inIframe();
  const theme = Theme.fromExisting();

  const map = L.map(id, {
    minZoom: routeType === "commuter_rail" ? 9 : 10,
    maxZoom: 20,
    maxBounds: L.latLngBounds(L.latLng(41, -73), L.latLng(43.5, -68)),
    fullscreenControl: true,
    fullscreenControlOptions: { position: "topleft" },
    attributionControl: true,
  });

  map.setView(
    [
      storageGet("lat", 42.3519, { parseFloat: true }),
      storageGet("lng", -71.0552, { parseFloat: true }),
    ],
    storageGet("zoom", routeType === "commuter_rail" ? 10 : 13, {
      parseFloat: true,
    })
  );

  map.on("move", () => {
    const cords = map.getCenter();
    sessionStorage.setItem("lat", cords.lat);
    sessionStorage.setItem("lng", cords.lng);
  });

  map.on("zoom", () => sessionStorage.setItem("zoom", map.getZoom()));
  map.on("baselayerchange", (event) => {
    new Theme(event.name).set(sessionStorage, onThemeChange);
  });

  const sidebar = L.control
    .sidebar("sidebar", {
      closeButton: true,
      position: "right",
    })
    .addTo(map);

  if (!isMobile || !isIframe) setTimeout(() => sidebar.show(), 500);

  const baseLayers = getBaseLayerDict();
  baseLayers[theme.theme].addTo(map);
  /**@type {LayerApiRealtimeOptions} */
  const baseOp = {
    textboxSize: { maxWidth: 375, minWidth: 250 },
    isMobile,
    sidebar,
    routeType,
    map,
  };

  const stopLayer = new StopLayer({
    url: "stops",
    layer: L.layerGroup(undefined, { name: "stops" }).addTo(map),
    ...baseOp,
  });

  const shapeLayer = new ShapeLayer({
    url: "shapes",
    layer: L.layerGroup(undefined, { name: "shapes" }).addTo(map),
    ...baseOp,
  });

  const vehicleLayer = new VehicleLayer({
    url: "vehicles?include=route,next_stop,stop_time,trip_properties",
    layer: L.markerClusterGroup({
      disableClusteringAtZoom: routeType == "commuter_rail" ? 10 : 12,
      name: "vehicles",
    }).addTo(map),
    ...baseOp,
  });

  const facilityLayer = new FacilityLayer({
    url: "parking",
    layer: L.layerGroup(undefined, { name: "parking" }),
    ...baseOp,
  });

  const layers = [stopLayer, shapeLayer, vehicleLayer, facilityLayer];
  layers.forEach((layer) => layer.plot());
  createControlLayers(
    baseLayers,
    ...layers.map((layer) => layer.options.layer)
  ).forEach((control) => control.addTo(map));

  map.on("zoomend", () => {
    if (map.getZoom() < 16) return map.removeLayer(facilityLayer.options.layer);
    map.addLayer(facilityLayer.options.layer);
  });

  if (map.hasLayer(facilityLayer.options.layer)) {
    map.removeLayer(facilityLayer.options.layer);
  }

  return map;
}

/** create control layers
 * @param {{light: TileLayer.Provider, dark: TileLayer.Provider}} tile_layers - base layers
 * @param {L.layerGroup[]} layers - layers to be added to the map
 * @returns {L.Control[]} control layers
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
