/**
 * @file base.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @typedef {import("../map.js")}
 * @import { DomEvent } from "leaflet";
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperty as string, PredictionProperty, AlertProperty, FetchCacheOptions } from "../types/index.js"
 * @exports BaseRealtimeLayer
 */

"use strict";

const _icons = {
  alert: "&#xf071;",
  prediction: "&#xf239;",
  bike: "&#xf206;",
  wheelchair: "&#xf193;",
  parking: "&#xf1b9;",
  space: "&nbsp;",
};

/** @typedef {typeof _icons} Icons */

/**
 * base encapsulating class for plotting realtime layers
 */
class BaseRealtimeLayer {
  static sideBarMainId = "sidebar-main";
  static sideBarOtherId = "sidebar-other";

  static openPopupIds = [];

  /**
   * Toggles a popup
   * @param {string | HTMLElement} id - the id of the popup or the popup element
   * @param {boolean | "auto"} show - whether or not to show the popup
   * @returns {void}
   */
  static togglePopup(id, show = "auto") {
    const popup = typeof id === "string" ? document.getElementById(id) : id;
    if (!popup) return;
    const identifier = popup.id || popup.name;
    if (window.chrome || navigator.userAgent.indexOf("AppleWebKit") != -1) {
      popup.classList.add("popup-solid-bg"); // just use firefox
    }
    if (!popup.classList.contains("show")) {
      BaseRealtimeLayer.openPopupIds.push(identifier);
    } else {
      BaseRealtimeLayer.openPopupIds.splice(
        BaseRealtimeLayer.openPopupIds.indexOf(identifier),
        1
      );
    }
    if (show === "auto") {
      popup.classList.toggle("show");
      return;
    }
    if (show) {
      popup.classList.add("show");
      if (!popup.classList.contains("show")) {
        BaseRealtimeLayer.openPopupIds.push(identifier);
      }
      return;
    }
    popup.classList.remove("show");
    BaseRealtimeLayer.openPopupIds.splice(
      BaseRealtimeLayer.openPopupIds.indexOf(identifier),
      1
    );
  }

  /** @name _icons */
  /** @type {Icons} typehint shennagins, ref to global var */
  static icons = _icons;
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  constructor(options) {
    options.interval = options.interval || 15000;
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

  /**
   * fills the sidebar with the properties
   * @param {LayerProperty} options
   */
  #fillSidebar(properties) {}

  /** Handle update event for realtime layers
   * @param {(event: RealtimeUpdateEvent) => void} fn - realtime layer to update
   * @returns {void}
   */
  handleUpdateEvent(fn) {
    /**@type {((id: string, feature: L.FeatureGroup) => void)} */
    const updateLayer = (id, feature) => {
      /**@type {L.Layer} */
      const layer = this.getLayer(id);
      layer.id = feature.id;
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
   * finds layer based on predicate and options
   * @typedef {{click?: boolean, autoZoom?: boolean, zoom?: number, latLng?: L.LatLng}} FindLayerOptions
   * @param {(value: L.LayerGroup<L.GeoJSON<LayerProperty>>, index: number, array: any[]) => L.Layer?} fn
   * @param {FindLayerOptions} options
   * @returns {L.Layer?}
   */
  findLayer(fn, options = {}) {
    options = { click: true, autoZoom: true, ...options };
    this.options.map.setZoom(this.options.map.options.minZoom, {
      animate: false,
    });
    /**@type {L.Layer[]} */
    const initialLayers = Object.values(this.options.map._layers);
    let layer = initialLayers.find(fn);
    /** @type {L.MarkerCluster?} */
    let mcluster;
    if (!layer) {
      mcluster = initialLayers
        .find((a) => a.options.name === "vehicles")
        ?.disableClustering();
      layer = Object.values(this.options.map._layers).find(fn);
      mcluster?.enableClustering();
    }
    if (!layer) {
      console.error(`layer not found`);
      return layer;
    }
    if (this.options.map.options.maxZoom && options.autoZoom) {
      this.options.map.setView(
        options.latLng || layer.getLatLng(),
        options.zoom || this.options.map.options.maxZoom
      );
    }
    if (options.click) layer.fire("click");
    return layer;
  }

  /**
   * fires click event and zooms in on stop
   * @param {string} stopId
   * @param {FindLayerOptions} options
   * @returns {L.Layer?} stop
   */
  clickStop(stopId, options = {}) {
    return (
      this.findLayer(
        (e) =>
          e?.feature?.properties?.child_stops
            ?.map((c) => c.stop_id)
            ?.includes(stopId) || e?.feature?.id === stopId
      ),
      { zoom: 15, ...options }
    );
  }

  /**
   * fires click event and zooms in on route
   * @param {string} routeId
   * @param {FindLayerOptions} options
   * @returns {L.Layer?} shape
   */
  clickRoute(routeId, options = {}) {
    return this.findLayer((e) => e?.feature?.properties?.route_id === routeId, {
      zoom: this.options.map.options.minZoom,
      latLng: this.options.map.getCenter(),
      ...options,
    });
  }
  /**
   * fires click event and zooms in on vehicle
   * wrapper for `findLayer`
   * @param {string} vehicleId
   * @param {FindLayerOptions} options
   * @returns {L.Layer?} vehicle
   */
  clickVehicle(vehicleId, options = {}) {
    return this.findLayer(
      (e) => e?.feature?.properties?.vehicle_id === vehicleId,
      { zoom: 15, ...options }
    );
  }
  /**
   *
   * @param {AlertProperty[]} alerts
   */
  getAlertsHTML(alerts) {
    return `<div>${alerts
      ?.map(
        (a) => `<div class="alert-box">
      <div class="alert-timestamp text-align-center">
      <div style='font-size:xxx-large'>
      <a style='text-decoration:none;' class='fa slight-delay' rel='noopener' target='_blank' href='${
        a.url
      }'>${BaseRealtimeLayer.icons.alert}</a>
      </div>
      <div>${formatTimestamp(a.timestamp, "%I:%M %P")}</div></div>
      <div class="alert-header">${a.header}</div>

    </div>`
      )
      ?.join("")}</div>`;
  }

  /**
   * gives a popup icon a loading symbol. this preps the icon
   * @param {HTMLElement} element the icon
   * @param {string} popupId popupId for `togglePopup`
   * @param {{style?: string, classList?: string[]}?} options
   * @returns {string} original html
   */
  popupLoadingIcon(element, popupId, options = {}) {
    const prevHtml = element.innerHTML;
    const classList = ["loader", ...(options?.classList || [])];
    element.onclick = () => BaseRealtimeLayer.togglePopup(popupId);
    element.classList.remove("hidden");
    element.innerHTML = /* HTML */ ` <div
      class="${classList.join(" ")}"
      style="${options?.style}"
    ></div>`;
    return prevHtml;
  }
  /**
   * @returns {FetchCacheOptions} default fetch cache options
   */
  get defaultFetchCacheOpt() {
    /**@type {FetchCacheOptions} */
    return {
      clearAfter: this.options.interval - 50,
      type: "json",
      storage: memStorage,
    };
  }

  /**
   * adds spacing to selected icon (or any string)
   * @template {keyof Icons} T
   * @param {T} icon
   * @param {number} [spaces = 2] how many spaces @default 2
   * @returns {`${Icons[T]}${Icons["space"]}`} icon html with html spacing
   */
  static iconSpacing(icon, spaces = 2) {
    return (
      (this.icons[icon] || icon) +
      new Array(spaces)
        .fill()
        .map((_) => (_ = this.icons.space))
        .join("")
    );
  }

  /**
   * to be called `onclick`
   *
   * supposed to be private but :P
   *
   * @template {LayerProperty} T
   *
   * @param {DomEvent.PropagableEvent} event
   * @param {{stopPropagation?: boolean, properties: T, _this?: this, idField?: keyof T}} options
   */
  _onclick(event, options = {}) {
    const {
      stopPropagation = true,
      _this = this,
      properties,
      idField = "id",
    } = options || {};
    const _id = properties[idField];
    try {
      if (_id) window.location.hash = `#${_id}`;
    } catch (error) {
      console.error(error);
    }
    if (stopPropagation) L.DomEvent.stopPropagation(event);
  }

  /**
   *
   * gets the more info button
   *
   * updates it if it already exists, but does not update if parent element is specified.
   *
   * if no parent element is specified and the element doesn't exist, click events may not work.
   *
   * @param {string} idfield
   * @param {{parent?: string | HTMLElement, loading: boolean, alert: boolean}} options
   * @returns {string}
   */
  moreInfoButton(idfield, options = {}) {
    // if (!this.options.isMobile || !this.options.sidebar.isVisible()) return "";
    const { loading = false, alert = false } = options;
    const _id = `infobutton-${idfield}`;
    let _icon = loading
      ? "<div style='display: inline-block;' class='loader'></div>"
      : `<span class='fa tooltip' data-tooltip='View Info'>${BaseRealtimeLayer.iconSpacing(
          "prediction",
          3
        )}</span>`;
    if (alert && !loading)
      _icon += `<span class='fa slight-delay tooltip' data-tooltip='open alerts'>${BaseRealtimeLayer.iconSpacing(
        "alert"
      )}</span>`;

    const _html = `<span
      name="${_id}"
      class="more-info-button"
      onclick="_sidebar.show()"
    >
      ${_icon}
    </span>`;

    if (options.parent) {
      const parEl =
        typeof options.parent === "string"
          ? document.getElementById(options.parent)
          : options.parent;
      if (parEl) parEl.innerHTML = _html;
    } else {
      document.getElementsByName(_id).forEach((el) => (el.outerHTML = _html));
    }

    return _html;
  }

  /**
   * there's def a better way to do this but fuck im too lazy to google this shit
   *
   * async updates the innerHTML of a element to "1 second ago" or something like that
   * @param {string} _id the id
   * @param {number} _timestamp the timestamp
   * @param {number} [sleep=15000] ms to sleep
   */
  async _updateTimestamp(_id, _timestamp, sleep = 15000) {
    while (true) {
      const el = document.getElementById(_id);
      if (!el) {
        await asyncSleep(1000);
        continue;
      }
      const _time = new Date().valueOf() / 1000 - _timestamp;
      let humanReadable;
      if (_time < 60) {
        humanReadable = `< 1m`;
      } else if (_time < 3600) {
        humanReadable = `~ ${Math.floor(_time / 60)}m`;
      } else if (_time < 86400) {
        humanReadable = `~ ${Math.floor(_time / 3600)}h`;
      } else {
        humanReadable = `~ ${Math.floor(_time / 86400)}d`;
      }
      el.innerHTML = `${humanReadable} ago`;
      await asyncSleep(sleep);
    }
  }
  /**
   * toggles the sidebar display
   * @param {typeof this.sideBarMainId | typeof this.sideBarOtherId | undefined} id force show this one and hide the other
   * @returns {HTMLElement} the shown element
   */
  static toggleSidebarDisplay(id) {
    const main = document.getElementById(this.sideBarMainId);
    const other = document.getElementById(this.sideBarOtherId);
    // use hidden class
    if (id === this.sideBarMainId) {
      main.classList.remove("hidden");
      other.classList.add("hidden");
      return main;
    }
    if (id === this.sideBarOtherId) {
      other.classList.remove("hidden");
      main.classList.add("hidden");
      return other;
    }
    if (main.classList.contains("hidden")) {
      main.classList.remove("hidden");
      other.classList.add("hidden");
      return main;
    }
    other.classList.remove("hidden");
    main.classList.add("hidden");
    return other;
  }
}
