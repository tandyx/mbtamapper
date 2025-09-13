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
 * @typedef {import("leaflet-search-types")}
 * @typedef {import("./utils.js")}
 * @typedef {import("./realtime/base.js")}
 * @typedef {import("./realtime/vehicles.js")}
 * @typedef {import("./realtime/facilities.js")}
 * @typedef {import("./realtime/shapes.js")}
 * @typedef {import("./realtime/stops.js")}
 * @typedef {import("leaflet-easybutton")}
 * @import {LeafletSidebar} from "./types"
 */
"use strict";
/**@type {L.Map?} for debug purposes*/
let _map;
/**@type {LeafletSidebar?} for reference purposes */
let _sidebar;
/**@type {L.Control.Search?} for reference purposes */
let _controlSearch;
/**@type {L.LayerGroup[]} */
let _realtimeLayers;

window.addEventListener("load", function () {
  const ROUTE_TYPE = window.location.href.split("/").slice(-2)[0];
  _map = createMap("map", ROUTE_TYPE);
  if (inIframe()) {
    setCssVar("--navbar-height", "0px");
    this.document.getElementsByTagName("nav")[0].remove();
  }
  Theme.fromExisting().set(localStorage, onThemeChange);

  setInterval(() => {
    document.querySelectorAll("[data-update-timestamp]").forEach((el) => {
      const now = new Date().valueOf() / 1000;
      const timestamp = parseFloat(el.dataset.updateTimestamp);
      el.innerHTML = ` ~ ${minuteify(now - timestamp)} ago`;
    });
  }, 1000);

  this.setTimeout(() => {
    const hash = this.window.location.hash.slice(1);
    if (!hash) return;
    const layerFinder = LayerFinder.fromGlobals();
    layerFinder.clickRoute(hash) ||
      layerFinder.clickStop(hash) ||
      layerFinder.clickVehicle(hash);
  }, 500);
});

/** map factory function for map.html
 * @param {string} id - id of the map div
 * @param {keyof RouteKeys} routeType - route type
 * @returns {L.map} map
 */
function createMap(id, routeType) {
  const isMobile = mobileCheck();
  const isIframe = inIframe();
  const theme = Theme.fromExisting();

  const map = L.map(id, {
    minZoom: routeType === "commuter_rail" ? 9 : 11,
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
    new Theme(event.name).set(localStorage, onThemeChange);
  });
  /**SIDEBAR OPS @type {LeafletSidebar?} */
  const sidebar = L.control
    .sidebar("sidebar", { closeButton: true, position: "right" })
    .addTo(map);
  _sidebar = sidebar;

  sidebar.on("hide", () => {
    document.documentElement.style.setProperty("--more-info-display", "unset");
  });
  sidebar.on("show", () => {
    document.documentElement.style.setProperty("--more-info-display", "none");
  });

  if (!isMobile && !isIframe) setTimeout(() => sidebar.show(), 500);

  const baseLayers = getBaseLayerDict();
  baseLayers[theme.theme].addTo(map);

  /**@type {LayerApiRealtimeOptions} */
  const baseOp = {
    textboxSize: { maxWidth: 375, minWidth: 250 },
    isMobile,
    sidebar,
    routeType,
    map,
    interactive: true,
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
    url: `vehicles?include=route,next_stop,stop_time&cache=12`,
    layer: L.markerClusterGroup({
      disableClusteringAtZoom: routeType == "commuter_rail" ? 10 : 12,
      name: "vehicles",
    }).addTo(map),
    interval: 12500,
    ...baseOp,
  });

  const facilityLayer = new FacilityLayer({
    url: "parking",
    layer: L.layerGroup(undefined, { name: "parking" }),
    ...baseOp,
  });

  const layers = [stopLayer, shapeLayer, vehicleLayer, facilityLayer];
  layers.forEach((layer) => layer.plot());
  const realtimeLayers = layers.map((ll) => ll.options.layer);
  _realtimeLayers = realtimeLayers;

  // createControlLayers(
  //   baseLayers,
  //   ...layers.map((layer) => layer.options.layer)
  // ).forEach((control) => control.addTo(map));

  /** @type {(btn: L.Control.EasyButton, map: L.Map)} */
  const _easyOnClick = (btn, map) => {
    _sidebar.toggle();
    if (!_sidebar.isVisible()) return btn.state("sidebar-close");
    btn.state("sidebar-open");
  };

  const easyButton = L.easyButton({
    states: [
      {
        stateName: "sidebar-open",
        icon: "<span class='fa'>&#xf053;</span>",
        title: "Toggle Sidebar",
        onClick: _easyOnClick,
      },
      {
        stateName: "sidebar-close",
        icon: "<span class='fa'>&#xf054;</span>",
        title: "Toggle Sidebar",
        onClick: _easyOnClick,
      },
    ],
  }).setPosition("topright");
  const locateControl = L.control.locate({
    enableHighAccuracy: true,
    initialZoomLevel: 15,
    metric: false,
    markerStyle: { zIndexOffset: 500 },
  });

  const layerControl = L.control.layers(
    baseLayers,
    Object.fromEntries(realtimeLayers.map((l) => [l.options?.name, l]))
  );

  const controlSearch = L.control.search({
    initial: false,
    propertyName: "searchName",
    zoom: 16,
    marker: false,
    textPlaceholder: "search",
    container: "findbox",
    collapsed: false,
    casesensitive: false,
    layer: L.layerGroup(realtimeLayers),
  });

  controlSearch.on("search:locationfound", (event) =>
    event.layer.fire("click")
  );
  _controlSearch = controlSearch;

  window.addEventListener("keydown", (keyEvent) => {
    if (
      keyEvent.code === "F3" ||
      ((keyEvent.ctrlKey || keyEvent.metaKey) && keyEvent.code === "KeyF")
    ) {
      keyEvent.preventDefault();
      controlSearch._input.focus();
    }
  });

  [locateControl, layerControl, controlSearch, easyButton].forEach((c) =>
    c.addTo(map)
  );

  map.on("zoomend", () => {
    if (map.getZoom() < 16) return map.removeLayer(facilityLayer.options.layer);
    map.addLayer(facilityLayer.options.layer);
  });

  map.on("click", () => {
    BaseRealtimeLayer.toggleSidebarDisplay(BaseRealtimeLayer.sideBarMainId);
    window.location.hash = "";
  });

  // easyButton.state;
  if (map.hasLayer(facilityLayer.options.layer)) {
    map.removeLayer(facilityLayer.options.layer);
  }

  // createSearch(map, { layer: L.layerGroup(realtimeLayers) });

  return map;
}
