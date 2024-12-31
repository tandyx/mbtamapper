/**
 * @file base.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperties, PredictionProperty, AlertProperty } from "../types/index.js"
 * @exports _RealtimeLayer
 */

"use strict";

const _icons = {
  alert: "&#xf071;",
  prediction: "&#xf239;",
  bike: "&#xf206;",
  wheelchair: "&#xf193;",
  parking: "&#xf1b9;",
  space: "&nbsp;&nbsp;",
};

/** @typedef {typeof _icons} Icons */

/**
 * base encapsulating class for plotting realtime layers
 */
class _RealtimeLayer {
  /** @name _icons */
  /** @type {Icons} typehint shennagins, ref to global var */
  static icons = _icons;
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  constructor(options) {
    this.options = options;
  }
  /**
   * plots the layer and returns the actual realtime layer
   * @param {LayerApiRealtimeOptions?} options from geojson
   * @returns {L.Realtime}
   */
  plot() {}

  /**
   * string or html element of icon
   * @param {LayerProperty} properties from geojson
   * @returns {string | HTMLElement}
   */
  #getIcon(properties) {}
  /**
   * text for popup
   * @param {LayerProperty} properties from geojson
   * @returns {HTMLDivElement} - vehicle props
   */
  #getPopupText() {}

  /**
   * @param {LayerApiRealtimeOptions} options
   */
  #getRealtime(options) {}

  /** Handle update event for realtime layers
   * @param {(event: RealtimeUpdateEvent) => void} fn - realtime layer to update
   * @returns {void}
   */
  handleUpdateEvent(fn) {
    Object.keys(fn.update).forEach(
      function (id) {
        const feature = fn.update[id];
        updateLayer.call(this, id, feature);
      }.bind(this)
    );
  }

  /**
   * gives a popup icon a loading symbol. this preps the icon
   * @param {HTMLElement} element the icon
   * @param {string} popupId popupId for `togglePopup`
   * @returns {string} original html
   */
  loadingIcon(element, popupId) {
    const prevHtml = element.innerHTML;
    element.onclick = () => togglePopup(popupId);
    element.classList.remove("hidden");
    element.innerHTML = `<div class='loader'></div>`;
    return prevHtml;
  }

  /**
   * adds spacing to selected icon (or any string)
   * @template {keyof Icons} T
   * @param {T} icon
   * @returns {`${Icons[T]}${Icons["space"]}`} icon html with html spacing
   */
  static iconSpacing(icon) {
    return (this.icons[icon] || icon) + this.icons.space;
  }
}
