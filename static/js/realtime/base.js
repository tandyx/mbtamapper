/**
 * @file base.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @typedef {import("../map.js")}
 * @import { DomEvent } from "leaflet";
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperty as string, PredictionProperty, AlertProperty, FetchCacheOptions, RouteProperty } from "../types/index.js"
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
  clock: "&#xf017;",
  track: "&#xf074;",
};

/** @typedef {typeof _icons} Icons */

/**
 * base encapsulating class for plotting realtime layers
 */
class BaseRealtimeLayer {
  static sideBarMainId = "sidebar-main";
  static sideBarOtherId = "sidebar-other";

  /** @type {StopProperty["stop_id"][]} - array of (starting) stop ids where we want to consider to label commuter rail tracks on certain tables */
  static starStations = [
    "NEC-2287",
    "BNT-0000",
    "NEC-2276", // back bay
    "NEC-1851",
    "NEC-2265",
    "DB-0095", // readville
    "FB-0095", // readville
    "NEC-2192", // readville
    "WML-0012", // back bay
    "NEC-2237",
    "NEC-2139", //cntnjc
    "SB-0150", //cntnjc
  ];

  static trackExceptions = [
    { stop_id: "WML-0025-07", direction_id: 0 },
    { stop_id: "WML-0025-05", direction_id: 1 },
  ];

  /** @name _icons */
  /** @type {Icons} typehint shennagins, ref to global var */
  static icons = _icons;
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  constructor(options) {
    options.interactive = [null, undefined].includes(options.interactive)
      ? options.interactive === true
      : Boolean(options.interactive);
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
   * returns the html for the popup && || sidebar footer
   * @param {LayerProperty} properties
   * @returns {string}
   */
  #getFooterHTML(properties) {}

  /**
   * text for popup
   * @param {LayerProperty} properties from geojson
   * @returns {HTMLDivElement} - vehicle props
   */
  #getPopupHTML() {}

  /**
   * @param {LayerApiRealtimeOptions} options
   */
  #getRealtime(options) {}

  /**
   * fills the sidebar with the properties
   * @param {LayerProperty} options
   */
  #fillSidebar(properties) {}

  /**
   * returns the header for the popup and sidebar
   * @param {LayerProperty} options
   * @returns {string}
   */
  #getHeaderHTML() {}

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
   *
   * @param {AlertProperty[]} alerts
   */
  getAlertsHTML(alerts) {
    return /* HTML */ `<div>
      ${alerts
        ?.map((a) => {
          const delayClass =
            a.severity === "SEVERE" ? "severe-delay" : "slight-delay";

          return /* HTML */ `<div
            class="alert-box"
            style="border: 2px solid var(--${delayClass});"
          >
            <div class="alert-timestamp text-align-center">
              <div style="font-size:xxx-large">
                <a
                  style="text-decoration:none;"
                  class="fa ${delayClass}"
                  rel="noopener"
                  target="_blank"
                  href="${a.url}"
                  >${BaseRealtimeLayer.icons.alert}</a
                >
              </div>
              <div>${formatTimestamp(a.timestamp, "%I:%M %P")}</div>
            </div>
            <div class="alert-header">${a.header}</div>
          </div>`;
        })
        ?.join("")}
    </div>`;
  }

  /**
   * @returns {FetchCacheOptions} default fetch cache options
   */
  get defaultFetchCacheOpt() {
    /**@type {FetchCacheOptions} */
    return { type: "json", storage: null };
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
   *
   * @template {LayerProperty} T
   *
   * @typedef {{stopPropagation?: boolean, properties: T, _this?: this, idField?: keyof T}} BaseRealtimeOnClickOptions
   *
   * to be called `onclick`
   *
   * @param {DomEvent.PropagableEvent} event
   * @param {BaseRealtimeOnClickOptions<T>} options
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
    /**@type {HTMLElement} */
    const sidebarDiv = _this.options.sidebar._contentContainer;
    sidebarDiv.onscroll = null;
  }

  /**
   * after click event
   *
   * @param {DomEvent.PropagableEvent} event
   * @param {BaseRealtimeOnClickOptions<T>} options
   */
  _afterClick(event, options = {}) {
    const { _this = this, properties, idField = "id" } = options || {};

    /**@type {HTMLElement} */
    const sidebarDiv = _this.options.sidebar._contentContainer;

    const scrollStorageId = `sidebar-scroll-${properties[idField]}`;

    const scrollTop = memStorage.getItem(scrollStorageId);
    if (scrollTop) sidebarDiv.scroll({ top: parseInt(scrollTop) });

    // DO NOT CHANGE TO ADDEVENTLISTENER
    sidebarDiv.onscroll = (event) => {
      memStorage.setItem(scrollStorageId, event.target.scrollTop);
    };

    for (const el of document.querySelectorAll("[data-route-id]")) {
      if (!el.onclick || el.dataset.onclick === "false") continue;
      /**@type {HTMLElement?} */
      const tbody =
        el.parentElement?.parentElement?.parentElement?.querySelector("tbody");
      if (!tbody) continue;
      tbody.classList.toggle(
        "hidden",
        localStorage.getItem(`route-${el.dataset.routeId}-hidden`) === "true"
      );

      const carrot = el.querySelector(`.fa`);
      if (!carrot) continue;
      carrot.innerHTML = tbody.classList.contains("hidden")
        ? `&#xf054;`
        : `&#xf078;`;
    }
  }
  // `route-${this.dataset.routeId}-hidden`
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
    const { loading = false, alert = false, coords } = options;
    const _id = `infobutton-${idfield}`;
    let _icon = loading
      ? "<div style='display: inline-block;' class='loader'></div>"
      : /* HTML */ `<span
          class="fa tooltip"
          data-tooltip="View Info"
          style="cursor: pointer;"
          >${BaseRealtimeLayer.iconSpacing("prediction", 3)}</span
        >`;
    if (alert && !loading)
      _icon += /* HTML */ `<span
        class="fa slight-delay tooltip"
        data-tooltip="open alerts"
        style="cursor: pointer;"
        >${BaseRealtimeLayer.iconSpacing("alert")}</span
      >`;

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
   * table header html
   * @param {RouteProperty} properties
   * @param {{colspan?: number, onclick?: boolean}} options - colspan = 2,
   * @param {number}
   */
  tableHeaderHTML(properties, options = {}) {
    const { onclick = true, colspan = 2 } = options;
    const _onclick = () => {
      /**@type {HTMLElement} */
      const tbody =
        this.parentElement.parentElement.parentElement.querySelector(`tbody`);
      if (!tbody) return;
      const nowHidden = !!tbody.classList.toggle(`hidden`);
      localStorage.setItem(
        `route-${this.dataset.routeId}-hidden`,
        nowHidden.toString()
      );
      const carrot = this.querySelector(`.fa`);
      if (!carrot) return;
      carrot.innerHTML = nowHidden ? `&#xf054;` : `&#xf078;`;
    };

    const color = getContrastYIQ(properties.route_color, 138);
    return /* HTML */ `<tr>
      <th
        colspan="${colspan}"
        data-route-id="${properties.route_id}"
        data-onclick="${onclick}"
        style="background-color: #${properties.route_color}"
        class="table-header-route"
        onclick="${onclick ? `(${_onclick.toString()})()` : ""}"
      >
        <a
          onclick="LayerFinder.fromGlobals().clickRoute('${properties.route_id}')"
          style="color:var(--${color}-text-color);"
          >${properties.route_name}</a
        >
        ${onclick
          ? `<div style="float:right;color:var(--${color}-text-color);" class="fa">&#xf078;</div>`
          : ""}
      </th>
    </tr>`;
  }
  /**
   *
   * returns the key of the HTML for the special stop
   *
   * @param {StopTimeAttrObj[]?} attrs if this array is provided, then the html will be shown if and only if the array has valid elements
   * @returns {string} html for the special stop key
   */
  static specialStopKeyHTML(attrs) {
    const _html = /* HTML */ `<div class="special-stoptime-key">
      <div>
        <span class="flag_stop">Flag Stop <i>f</i></span> - Must be visible on
        platform & alert conductor to leave.
      </div>
      <div>
        <span class="early_departure">Early Departure <i>L</i></span> - Train
        may depart before scheduled time.
      </div>
      <div>
        Many Platforms
        <span class="fa">${BaseRealtimeLayer.icons.track}</span> - Hover to see
        track (non-standard).
      </div>
    </div>`;
    if (!attrs) return _html;
    if (!attrs.filter((s) => Object.values(s).filter(Boolean).length).length) {
      return "";
    }

    return _html;
  }

  /**
   *
   * @param {{stop_id: string, platform_code?: string, direction_id?: number, route_type: string}} properties
   * @param {{mode?: "auto" | "star" | "all"}} [options = {mode: "auto"}]
   */
  static trackIconHTML(properties, options = {}) {
    let { stop_id, platform_code, direction_id, route_type } = properties;
    const { mode = "auto" } = options;

    const star = this.starStations.find((s) => stop_id.startsWith(s));

    if (mode === "star" && !star) return "";

    if (!platform_code) {
      const strSplit = stop_id.split("-");
      platform_code = strSplit.length < 3 ? "" : strSplit.at(-1);
    }

    const pc_num = Number(platform_code);

    if (!platform_code) return "";

    if (
      (mode === "auto" &&
        !star &&
        route_type === "2" &&
        Number(direction_id) + 1 === pc_num) ||
      Number.isNaN(pc_num) ||
      this.trackExceptions.filter(
        (a) => a.stop_id === stop_id && a.direction_id === direction_id
      ).length
    ) {
      return "";
    }

    // if ( trackExceptions
    //   mode === "auto" &&
    //   !star &&
    //   !Number.isNaN(pc_num) &&
    //   !(
    //     properties.route_type === "2" &&
    //     Number(properties.direction_id) + 1 === pc_num
    //   )
    // ) {
    //   return "";
    // }

    return /* HTML */ `<span class="fa tooltip" data-tooltip="Track ${pc_num}">
      ${this.icons.space} ${this.icons.track}</span
    >`;
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
