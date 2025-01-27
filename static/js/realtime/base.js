/**
 * @file base.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperties as string, PredictionProperty, AlertProperty } from "../types/index.js"
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
    /**@type {((id: string, feature: L.FeatureGroup) => void)} */
    const updateLayer = (id, feature) => {
      /**@type {L.Layer} */
      const layer = this.getLayer(id);
      const wasOpen = layer.getPopup().isOpen();
      layer.unbindPopup();
      if (wasOpen) layer.closePopup();
      layer.bindPopup(feature.properties.popupContent, {
        maxWidth: "auto",
      });
      if (wasOpen) layer.openPopup();
    };

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
   * @param {{style?: string, classList?: string[]}?} options
   * @returns {string} original html
   */
  loadingIcon(element, popupId, options) {
    const prevHtml = element.innerHTML;
    const classList = ["loader", ...(options?.classList || [])];
    element.onclick = () => togglePopup(popupId);
    element.classList.remove("hidden");
    element.innerHTML = /* HTML */ ` <div
      class="${classList.join(" ")}"
      style="${options?.style}"
    ></div>`;
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
