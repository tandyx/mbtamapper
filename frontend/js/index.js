/**
 * @file index.js - for the homepage. additional code must be used to render the map
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
 * @import {LeafletSidebar, RouteKey} from "./types/index.js"
 * @import { RouteKeys } from "./types/index.js"
 */

"use strict";

/**
 * @typedef {{htmlContent: string, cssClasses: string[]}} ContentArgs
 */

/**
 * creates the background map for the homepage and 404 page.
 * @param {string | HTMLElement} id
 * @param {RouteKeys} routeKeys
 * @param {ContentArgs} content
 * @returns {L.Map}
 */
function createHomepageMap(id, routeKeys, content) {
  /**@type {HTMLElement} */
  id = typeof id === "string" ? document.getElementById(id) : id;
  id.style.cursor = "default";

  /**@type {(keyof RouteKeys)[]} */
  const keys = Object.keys(routeKeys);

  const routeType = keys[Math.floor(Math.random() * keys.length)];
  const zoom = routeType === "commuter_rail" ? 11 : 13;

  const map = L.map("map", {
    zoomControl: false,
    maxZoom: zoom,
    minZoom: zoom,
  }).setView([42.3519, -71.0552], zoom);

  map.on("baselayerchange", (event) => {
    const theme = new Theme(event.name).set(localStorage, onThemeChange);
    if (typeof updateToggle === "function") updateToggle("modeToggle", theme);
  });

  const baseLayers = getBaseLayerDict();
  baseLayers[Theme.fromExisting().theme].addTo(map);

  const shapeLayer = new ShapeLayer({
    url: `/${routeType}/shapes`,
    layer: L.layerGroup(undefined, { name: "shapes" }).addTo(map),
    isMobile: mobileCheck(),
    routeType: routeType,
    map,
    textboxSize: { maxWidth: 375, minWidth: 250 },
    interactive: false,
    interval: 1000 * 60 * 5000,
  });

  const shapeRealtime = shapeLayer.plot();
  shapeRealtime.off("click");

  map.dragging.disable();
  map.touchZoom.disable();
  map.doubleClickZoom.disable();
  map.scrollWheelZoom.disable();
  map.boxZoom.disable();
  map.keyboard.disable();
  map?.tap?.disable();

  const textControl = L.control.textbox({
    position: "middlecenter",
    ...content,
  });
  textControl.addTo(map);
  L.control
    .layers(
      Object.fromEntries(
        Object.entries(baseLayers).map(([k, v]) => [titleCase(k), v])
      )
    )
    .addTo(map);
  return map;
}

/**
 * we want to include these corners
 */
L.Map.include({
  _initControlPos: function () {
    const corners = (this._controlCorners = {});
    const l = "leaflet-";
    const container = (this._controlContainer = L.DomUtil.create(
      "div",
      l + "control-container",
      this._container
    ));

    function createCorner(vSide, hSide) {
      const className = l + vSide + " " + l + hSide;
      corners[vSide + hSide] = L.DomUtil.create("div", className, container);
    }

    createCorner("top", "left");
    createCorner("top", "right");
    createCorner("bottom", "left");
    createCorner("bottom", "right");

    createCorner("top", "center");
    createCorner("middle", "center");
    createCorner("middle", "left");
    createCorner("middle", "right");
    createCorner("bottom", "center");
  },
});

L.Control.textbox = L.Control.extend({
  /**
   * executes on add. draws this.options.htmlText
   *
   * @param {L.Map} map
   * @param {string} htmlText
   * @returns {HTMLDivElement}
   */
  onAdd: function (map) {
    const text = L.DomUtil.create("div");
    text.classList.add("leaflet-text-control");
    text.innerHTML = this.options.htmlContent;
    return text;
  },

  /**
   * executes on remove.
   * @param {L.Map} map
   */
  onRemove: function (map) {
    // Nothing to do here
  },
});

/**
 * custom element - html textbox
 * @param {L.ControlOptions & ContentArgs} options
 * @returns
 */
L.control.textbox = function (options) {
  return new L.Control.textbox(options);
};
