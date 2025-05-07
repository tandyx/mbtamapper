/**
 * @file shapes.js - Plot stops on map in realtime, updating every 15 seconds
 * @module shapes
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @typedef {import("sorttable/sorttable.js").sorttable} sorttable
 * @import { sorttable } from "sorttable/sorttable.js"
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperty, PredictionProperty, AlertProperty, VehicleProperty, RealtimeLayerOnClickOptions, NextStop } from "../types/index.js"
 * @import { Layer, Realtime } from "leaflet";
 * @import {BaseRealtimeLayer} from "./base.js"
 * @exports VehicleLayer
 */

"use strict";

/**
 * encapsulating class to plot Vehicles on a leaflet map
 * after object creation, you can call `.plot` to plot it
 */
class VehicleLayer extends BaseRealtimeLayer {
  static #hex_css_map = {
    FFC72C:
      "filter: invert(66%) sepia(78%) saturate(450%) hue-rotate(351deg) brightness(108%) contrast(105%);",
    "7C878E":
      "filter: invert(57%) sepia(2%) saturate(1547%) hue-rotate(160deg) brightness(91%) contrast(103%);",
    "003DA5":
      "filter: invert(13%) sepia(61%) saturate(5083%) hue-rotate(215deg) brightness(96%) contrast(101%);",
    "008EAA":
      "filter: invert(40%) sepia(82%) saturate(2802%) hue-rotate(163deg) brightness(88%) contrast(101%);",
    "80276C":
      "filter: invert(20%) sepia(29%) saturate(3661%) hue-rotate(283deg) brightness(92%) contrast(93%);",
    "006595":
      "filter: invert(21%) sepia(75%) saturate(2498%) hue-rotate(180deg) brightness(96%) contrast(101%);",
    "00843D":
      "filter: invert(31%) sepia(99%) saturate(684%) hue-rotate(108deg) brightness(96%) contrast(101%);",
    DA291C:
      "filter: invert(23%) sepia(54%) saturate(7251%) hue-rotate(355deg) brightness(90%) contrast(88%);",
    ED8B00:
      "filter: invert(46%) sepia(89%) saturate(615%) hue-rotate(1deg) brightness(103%) contrast(104%);",
    ffffff:
      "filter: invert(100%) sepia(93%) saturate(19%) hue-rotate(314deg) brightness(105%) contrast(104%);",
  };

  static #direction_map = {
    0: "Outbound",
    1: "Inbound",
    0.0: "Outbound",
    1.0: "Inbound",
  };

  static #worcester_map = {
    515: "hub to heart",
    520: "heart to hub",
  };

  /**
   * string or html element of vehicle
   * @param {VehicleProperty} properties from geojson
   * @returns {L.DivIcon}
   */
  #getIcon(properties) {
    const iconHtml = /* HTML */ `
      <div class="vehicle_wrapper">
        <img
          src="static/img/icon.png"
          loading="lazy"
          alt="vehicle"
          width="60"
          height="60"
          style="
            ${VehicleLayer.#hex_css_map[properties.route_color] || ""}; 
            transform: rotate(${properties.bearing}deg);
          "
        />
        <span class="vehicle_text">${properties.display_name}</span>
      </div>
    `;

    return L.divIcon({ html: iconHtml, iconSize: [10, 10] });
  }
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  constructor(options) {
    super(options);
    this.iter = 0;
  }

  /**
   * @param {LayerApiRealtimeOptions?} options
   */
  plot(options) {
    const _this = this;
    options = { ..._this.options, ...options };
    const onClickOpts = { _this, idField: "vehicle_id" };
    const realtime = L.realtime(options.url, {
      interval: this.options.interval,
      // interval: 500,
      type: "FeatureCollection",
      container: options.layer,
      cache: false,
      removeMissing: true,
      getFeatureId: (f) => f.id,
      onEachFeature(f, l) {
        l.id = f.id;
        l.feature.properties.searchName = `${f.properties.trip_short_name} @ ${f.properties.route?.route_name}`;
        l.bindPopup(_this.#getPopupText(f.properties), options.textboxSize);
        if (!options.isMobile) l.bindTooltip(f.id);
        l.setIcon(_this.#getIcon(f.properties));
        l.setZIndexOffset(100);
        l.on("click", (_e) => {
          _this.#_onclick(_e, { ...onClickOpts, properties: f.properties });
        });
      },
    });

    // realtime.on("update", () => _this.iter++);
    realtime.on("update", function (_e) {
      this.iter++;
      _this.#fillDefaultSidebar(
        Object.values(_e.features).map((e) => e.properties)
      );
      Object.keys(_e.update).forEach(
        function (id) {
          /**@type {Layer} */
          const layer = this.getLayer(id);
          /**@type {GeoJSON.Feature<GeoJSON.Geometry, VehicleProperty} */
          const feature = _e.update[id];
          // const properties = feature.properties;
          const _onclick = () => {
            _this.#_onclick(_e, {
              ...onClickOpts,
              properties: feature.properties,
            });
          };
          const wasOpen = layer.getPopup()?.isOpen() || false;
          layer.id = feature.id;
          layer.feature.properties.searchName = `${feature.properties.trip_short_name} @ ${feature.properties.route?.route_name}`;
          layer.unbindPopup();
          if (wasOpen) layer.closePopup();
          layer.bindPopup(
            _this.#getPopupText(feature.properties),
            options.textboxSize
          );
          layer.setIcon(_this.#getIcon(feature.properties));
          if (wasOpen) {
            _this.options.map.setView(
              layer.getLatLng(),
              _this.options.map.getZoom(),
              { animate: true }
            );
            layer.openPopup();
            setTimeout(_onclick, 200);
          }
          layer.on("click", _onclick);
        }.bind(this)
      );
    });

    return realtime;
  }
  /**
   *
   * @param {VehicleProperty} properties
   * @returns
   */
  #getHeaderHTML(properties) {
    return /* HTML */ `<div>
      <div>
        <a
          href="${properties.route?.route_url}"
          target="_blank"
          style="color:#${properties.route_color};line-height: 1.35;"
          class="popup_header"
        >
          ${properties.trip_short_name}
        </a>
      </div>
      <div>
        ${VehicleLayer.#worcester_map[properties.trip_short_name] ||
        `${VehicleLayer.#direction_map[properties.direction_id] || "null"} to ${
          properties.headsign
        }`}
      </div>
      <hr />
    </div>`;
  }

  /**
   * sometimes the next stop on a vehicle is not available, so we infill it asynchronously
   *
   * MUTATES properties
   *
   * @param {VehicleProperty} properties pointer to this property
   * @param {{count?: number, delay?: number}} options
   * @returns {Promise<NextStop?>} pointer to `properties.next_stop`
   */
  async #infillNextStop(properties, options = {}) {
    if (!properties) return;
    if (properties.next_stop) return properties.next_stop;
    const { count = 5, delay = 1000 } = options || {};
    let _count = 0;
    while (!properties.next_stop && _count < count) {
      await asyncSleep(delay);
      properties.next_stop = (
        await fetchCache(
          `/api/vehicles?vehicle_id=${properties.vehicle_id}&include=next_stop`,
          {},
          { storage: null }
        )
      )?.at(0)?.next_stop;
    }
    return properties.next_stop;
  }

  /**
   * @param {VehicleProperty} properties
   */
  #getStatusHTML(properties) {
    const dominant =
      properties.next_stop?.arrival_time ||
      properties.next_stop?.departure_time;
    // for scheduled stops
    if (properties.stop_time) {
      if (properties.current_status !== "STOPPED_AT") {
        return `<div>${almostTitleCase(properties.current_status)} ${
          properties.stop_time.stop_name
        } - ${dominant ? formatTimestamp(dominant, "%I:%M %P") : ""}</div>`;
      }
      return `<div>${almostTitleCase(properties.current_status)} ${
        properties.stop_time.stop_name
      }</div>`;
    }
    if (!properties.next_stop) return "";
    // for added stops
    if (properties.current_status !== "STOPPED_AT") {
      return `<div>${almostTitleCase(properties.current_status)} ${
        properties.next_stop.stop_name
      } - ${dominant ? formatTimestamp(dominant, "%I:%M %P") : ""}</div>`;
    }
    return `<div>${almostTitleCase(properties.current_status)} ${
      properties.next_stop.stop_name
    }</div>`;
  }
  /**
   *
   * @param {VehicleProperty} properties
   * @returns
   */
  #getDelayHTML(properties) {
    if (!properties?.stop_time) return "";
    if ([null, undefined].includes(properties?.next_stop?.delay)) return "";
    const delay = Math.round(properties.next_stop.delay / 60);
    if (delay < 2 && delay >= 0) return "<i>on time</i>";
    const dClassName = getDelayClassName(properties.next_stop.delay);
    return /* HTML */ ` <i class="${dClassName}">
      ${Math.abs(delay)} minutes
      ${dClassName === "on-time" ? "early" : "late"}</i
    >`;
  }

  /**
   * @param {VehicleProperty} properties
   */
  #getOccupancyHTML(properties) {
    if (properties.occupancy_status === null) return "";
    // if (delay)

    return /* HTML */ `<div>
      <span
        class="${properties.occupancy_percentage >= 80
          ? "severe-delay"
          : properties.occupancy_percentage >= 60
          ? "moderate-delay"
          : properties.occupancy_percentage >= 40
          ? "slight-delay"
          : ""}"
      >
        ${properties.occupancy_percentage}% occupancy
      </span>
    </div>`;
  }

  /**
   * gets vehicle text
   * @param {VehicleProperty} properties
   * @returns {HTMLDivElement} - vehicle text
   */
  #getPopupText(properties) {
    const vehicleText = document.createElement("div");
    vehicleText.innerHTML = /* HTML */ ` ${this.#getHeaderHTML(properties)}
      <div style="margin-bottom: 3px;">
        ${properties.bikes_allowed
          ? `<span class="fa tooltip" data-tooltip="bikes allowed"
        >${BaseRealtimeLayer.iconSpacing("bike")}</span>`
          : ""}
        ${super.moreInfoButton(properties.vehicle_id)}
      </div>
      ${this.#getStatusHTML(properties)}
      <div>${this.#getDelayHTML(properties)}</div>
      ${this.#getOccupancyHTML(properties)}
      <div>
        ${properties.speed_mph != null
          ? Math.round(properties.speed_mph)
          : properties.speed_mph}
        mph
      </div>
      <div class="popup_footer">
        <div>
          ${properties.vehicle_id} @
          ${properties?.route?.route_name || "unknown"}
          ${properties.next_stop?.platform_code
            ? `track ${properties.next_stop.platform_code}`
            : ""}
        </div>
        <div>
          ${formatTimestamp(properties.timestamp, "%I:%M %P")}
          <i
            id="vehicle-${properties.vehicle_id}-timestamp-${this.iter || 1}"
          ></i>
        </div>
      </div>`;

    return vehicleText;
  }

  /**
   *
   * @param {VehicleProperty} properties
   * @param {AlertProperty[]} alerts
   * @param {PredictionProperty[]} predictions
   */
  async #fillSidebar(properties) {
    const container = BaseRealtimeLayer.toggleSidebarDisplay(
      BaseRealtimeLayer.sideBarOtherId
    );
    if (!container) return;
    super.moreInfoButton(properties.vehicle_id, { loading: true });
    /**@type {PredictionProperty[]}*/
    const predictions = await fetchCache(
      `/api/prediction?trip_id=${properties.trip_id}&include=stop_time`,
      {},
      super.defaultFetchCacheOpt
    );
    /** @type {AlertProperty[]} */
    const alerts = await fetchCache(
      `/api/alert?trip_id=${properties.trip_id}`,
      {},
      super.defaultFetchCacheOpt
    );
    super.moreInfoButton(properties.vehicle_id, {
      alert: Boolean(alerts.length),
    });

    container.innerHTML = /*HTML*/ `<div>
      ${this.#getHeaderHTML(properties)}
      ${this.#getStatusHTML(properties)}
      ${super.getAlertsHTML(alerts)}
      ${this.#getOccupancyHTML(properties)}
      <div style='margin-top:5px;'>
        <table class='data-table'>
        <tr><th>Stop</th><th>Estimate</th></tr>
        ${predictions
          ?.sort(
            (a, b) =>
              (a.departure_time || a.arrival_time) -
              (b.departure_time || b.arrival_time)
          )
          ?.map((d) => {
            const realDeparture = d.departure_time || d.arrival_time;
            if (!realDeparture || realDeparture < Date().valueOf()) return "";
            const delayText = getDelayText(d.delay);
            let stopTimeClass,
              tooltipText,
              htmlLogo = "";
            if (d.stop_time?.flag_stop) {
              stopTimeClass = "flag_stop tooltip";
              tooltipText = "flag stop";
              htmlLogo = "<i> f</i>";
            } else if (d.stop_time?.early_departure) {
              stopTimeClass = "early_departure tooltip";
              tooltipText = "early departure";
              htmlLogo = "<i> L</i>";
            }

            return `<tr>
              <td class='${stopTimeClass}' data-tooltip='${tooltipText}'>${
              d.stop_name
            } ${htmlLogo}</td>
              <td>
                ${formatTimestamp(realDeparture, "%I:%M %P")}
                <i class='${getDelayClassName(d.delay)}'>${delayText}</i>
              </td>
            </tr>
            `;
          })
          .join("")}
        </table>
      </div>  
    </div>
  </div>
  `;
  }

  /**
   * fills the default sidebar, the one on load
   * @param {VehicleProperty[]} properties
   */
  #fillDefaultSidebar(properties) {
    const container = document.getElementById(BaseRealtimeLayer.sideBarMainId);
    if (!container) return;
    // const findBox = "<div id='findBox'></div>";
    if (!properties.length) {
      container.innerHTML = /* HTML */ `
        <h2>${titleCase(this.options.routeType)}</h2>
        <p>No vehicles found</p>
      `;
      return;
    }
    container.innerHTML = /*HTML*/ `
    <h2>${titleCase(this.options.routeType)}</h2>
    <table class='mt-5 sortable data-table'>
      <thead>
        <tr><th>route</th><th>trip</th><th>next stop</th><th>delay</th></tr>
      </thead>
      <tbody>
      ${properties
        .map((prop) => {
          const encoded = btoa(JSON.stringify(prop));
          const lStyle = `style="color:#${prop.route.route_color};font-weight:600;"`;
          return /*HTML*/ `<tr>
          <td><a ${lStyle} id="to-r-${encoded}">${
            prop.route.route_name
          }</a></td>
          <td><a ${lStyle} id="to-v-${encoded}">${prop.trip_short_name}</a></td>
          <td><a  id="to-s-${encoded}"> ${
            prop.next_stop?.stop_name || prop.stop_time?.stop_name
          }</a></td>
          <td><i class='${getDelayClassName(
            prop.next_stop?.delay
          )}'>${getDelayText(prop.next_stop?.delay)}</i></td>
        </tr>`;
        })
        .join("")}
      </tbody>
      </table>
    `;

    for (const el of document.getElementsByClassName("sortable")) {
      sorttable.makeSortable(el);
    }
    for (const prop of properties) {
      const encoded = btoa(JSON.stringify(prop));
      document
        .getElementById(`to-v-${encoded}`)
        ?.addEventListener("click", () => super.clickVehicle(prop.vehicle_id));
      document
        .getElementById(`to-r-${encoded}`)
        ?.addEventListener("click", () => super.clickRoute(prop.route_id));
      document
        .getElementById(`to-s-${encoded}`)
        ?.addEventListener("click", () => super.clickStop(prop.stop_id));
    }
  }

  /**
   * to be called `onclick`
   *
   * supposed to be private but :P
   *
   * @param {DomEvent.PropagableEvent} event
   * @param {RealtimeLayerOnClickOptions<VehicleProperty>} options
   */
  #_onclick(event, options = {}) {
    super._onclick(event, options);
    /**@type {this} */
    const _this = options._this || this;
    _this.#infillNextStop(options.properties);
    _this.#fillSidebar(options.properties);

    super._updateTimestamp(
      `vehicle-${options.properties.vehicle_id}-timestamp-${_this.iter || 1}`,
      options.properties.timestamp
    );
  }
}
