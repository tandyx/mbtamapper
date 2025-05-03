/**
 * @file shapes.js - Plot stops on map in realtime, updating every 15 seconds
 * @module shapes
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @typedef {import("sorttable/sorttable.js").sorttable} sorttable
 * @import { sorttable } from "sorttable/sorttable.js"
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperty, PredictionProperty, AlertProperty, VehicleProperty } from "../types/index.js"
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
        l.on("click", (event) => {
          L.DomEvent.stopPropagation(event);
          _this.#fillDataWrapper(f.properties, _this);
        });
      },
    });

    // realtime.on("update", () => _this.iter++);
    realtime.on("update", function (event) {
      this.iter++;
      _this.#fillDefaultSidebar(
        Object.values(event.features).map((e) => e.properties)
      );
      Object.keys(event.update).forEach(
        function (id) {
          /**@type {Layer} */
          const layer = this.getLayer(id);
          /**@type {GeoJSON.Feature<GeoJSON.Geometry, VehicleProperty} */
          const feature = event.update[id];
          const _onclick = () => {
            L.DomEvent.stopPropagation(event);
            _this.#fillDataWrapper(feature.properties, _this);
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
   * gets vehicle text
   * @param {VehicleProperty} properties
   * @returns {HTMLDivElement} - vehicle text
   */
  #getPopupText(properties) {
    const vehicleText = document.createElement("div");
    const fmtmstp = formatTimestamp(properties.timestamp, "%I:%M %P");
    const delay = Math.round(properties.next_stop?.delay / 60);
    const dClassName = getDelayClassName(properties.next_stop?.delay);
    const toolTipClass = this.options?.isMobile ? "" : "tooltip";
    // console.log(`${properties.trip_id}: ${delay}`);
    vehicleText.innerHTML = /* HTML */ ` <p>
        <a
          href="${properties.route?.route_url ||
          `https://mbta.com/schedules/${properties.route_id}`}"
          target="_blank"
          style="color:#${properties.route_color}"
          class="popup_header"
        >
          ${properties.trip_short_name}
        </a>
      </p>
      <p>
        ${VehicleLayer.#worcester_map[properties.trip_short_name] ||
        `${VehicleLayer.#direction_map[properties.direction_id] || "null"} to ${
          properties.headsign
        }`}
      </p>
      <hr />
      ${properties.bikes_allowed
        ? `<span class="fa tooltip" data-tooltip="bikes allowed"
        >${BaseRealtimeLayer.iconSpacing("bike")}</span>`
        : ""}
      <span
        name="pred-veh-${properties.trip_id}"
        class="fa hidden popup ${toolTipClass}"
        data-tooltip="predictions"
      >
        ${BaseRealtimeLayer.iconSpacing("prediction")}
      </span>
      <span
        name="alert-veh-${properties.trip_id}"
        class="fa hidden popup ${toolTipClass} slight-delay"
        data-tooltip="alerts"
      >
        ${BaseRealtimeLayer.iconSpacing("alert")}
      </span>
      ${properties.stop_time
        ? `${
            properties.current_status != "STOPPED_AT"
              ? `<p>${almostTitleCase(properties.current_status)} ${
                  properties.stop_time.stop_name
                } - ${
                  properties.next_stop?.arrival_time ||
                  properties.next_stop?.departure_time
                    ? formatTimestamp(
                        properties.next_stop?.arrival_time ||
                          properties.next_stop?.departure_time,
                        "%I:%M %P"
                      )
                    : ""
                }</p>`
              : `<p>${almostTitleCase(properties.current_status)} ${
                  properties.stop_time.stop_name
                }</p>`
          }
    ${
      properties.next_stop?.delay !== null
        ? `
      ${
        delay !== delay
          ? ""
          : delay !== 0
          ? `
          <i class='${dClassName}'> ${Math.abs(delay)} minutes ${
              dClassName === "on-time" ? "early" : "late"
            }
          </i>`
          : "<i>on time</i>"
      }`
        : ""
    }`
        : properties.next_stop
        ? `${
            properties.current_status != "STOPPED_AT"
              ? `<p>${almostTitleCase(properties.current_status)} ${
                  properties.next_stop.stop_name
                } - ${fmtmstp}</p>`
              : `<p>${almostTitleCase(properties.current_status)} ${
                  properties.next_stop.stop_name
                }</p>`
          }`
        : ""}
      ${properties.occupancy_status != null
        ? `<p>
      <span class="${
        properties.occupancy_percentage >= 80
          ? "severe-delay"
          : properties.occupancy_percentage >= 60
          ? "moderate-delay"
          : properties.occupancy_percentage >= 40
          ? "slight-delay"
          : ""
      }">
        ${properties.occupancy_percentage}% occupancy
      </span>
    </p>`
        : ""}
      <p>
        ${properties.speed_mph != null
          ? Math.round(properties.speed_mph)
          : properties.speed_mph}
        mph
      </p>
      <div class="popup_footer">
        <p>
          ${properties.vehicle_id} @
          ${properties.route ? properties.route.route_name : "unknown"}
          ${properties.next_stop?.platform_code
            ? `track ${properties.next_stop.platform_code}`
            : ""}
        </p>
        <p>
          ${formatTimestamp(properties.timestamp, "%I:%M %P")}
          <i
            id="vehicle-${properties.vehicle_id}-timestamp-${this.iter || 1}"
          ></i>
        </p>
      </div>`;

    return vehicleText;
  }

  /**
   * fill prediction data in for `pred-veh-{trip_id}` element
   * this appears as a popup on the map
   * @param {string} trip_id - vehicle id
   * @param {boolean} popup - whether to show the popup
   */
  async #fillPredictionData(trip_id) {
    for (const predEl of document.getElementsByName(`pred-veh-${trip_id}`)) {
      const popupId = `popup-pred-${trip_id}`;
      super.popupLoadingIcon(predEl, popupId);
      const popupText = document.createElement("span");

      popupText.classList.add("popuptext");
      popupText.id = popupId;
      popupText.innerHTML = "...";
      /**@type {PredictionProperty[]}*/
      const _data = fetchCache(
        `/api/prediction?trip_id=${trip_id}&include=stop_time`,
        {},
        {
          clearAfter: this.options.interval - 50,
        }
      );

      if (!_data.length) {
        predEl.classList.add("hidden");
        return [];
      }
      popupText.innerHTML =
        "<table class='data-table'><tr><th>stop</th><th>estimate</th></tr>" +
        _data
          .sort(
            (a, b) =>
              (a.departure_time || a.arrival_time) -
              (b.departure_time || b.arrival_time)
          )
          .map((d) => {
            const realDeparture = d.departure_time || d.arrival_time;
            if (!realDeparture || realDeparture < Date().valueOf()) return "";
            const delayText = getDelayText(d.delay);
            let stopTimeClass,
              tooltipText = "";
            if (d.stop_time?.flag_stop) {
              stopTimeClass = "flag_stop tooltip";
              tooltipText = "flag stop";
              d.stop_name += "<i> f</i>";
            } else if (d.stop_time?.early_departure) {
              stopTimeClass = "early_departure tooltip";
              tooltipText = "early departure";
              d.stop_name += "<i> L</i>";
            }

            return `<tr>
              <td class='${stopTimeClass}' data-tooltip='${tooltipText}'>${
              d.stop_name
            }</td>
              <td>
                ${formatTimestamp(realDeparture, "%I:%M %P")}
                <i class='${getDelayClassName(d.delay)}'>${delayText}</i>
              </td>
            </tr>
            `;
          })
          .join("") +
        "</table>";
      predEl.innerHTML = BaseRealtimeLayer.iconSpacing("prediction");
      predEl.appendChild(popupText);
      setTimeout(() => {
        if (BaseRealtimeLayer.openPopupIds.includes(popupId)) {
          BaseRealtimeLayer.togglePopup(popupId, true);
        }
      }, 400);
      return _data;
    }
  }
  /**
   *  fill alert prediction data
   * @param {string} trip_id - vehicle id
   */
  async #fillAlertData(trip_id) {
    for (const alertEl of document.getElementsByName(`alert-veh-${trip_id}`)) {
      const popupId = `popup-alert-${trip_id}`;
      super.popupLoadingIcon(alertEl, popupId, {
        style: "border-top: var(--border) solid var(--slight-delay);",
      });
      const popupText = document.createElement("span");
      popupText.classList.add("popuptext");
      popupText.id = popupId;
      popupText.innerHTML = "...";
      /** @type {AlertProperty[]} */
      const _data = await (await fetch(`/api/alert?trip_id=${trip_id}`)).json();
      if (!_data.length) {
        alertEl.classList.add("hidden");
        return [];
      }
      popupText.innerHTML =
        "<table class='data-table'><tr><th>alert</th><th>timestamp</th></tr>" +
        _data
          .sort((a, b) => b.timestamp || 0 - a.timestamp || 0)
          .map(function (d) {
            return `<tr>
              <td>${d.header}</td>
              <td>${formatTimestamp(d.timestamp)}</td>
            </tr>
            `;
          })
          .join("") +
        "</table>";
      alertEl.innerHTML = BaseRealtimeLayer.iconSpacing("alert");
      alertEl.appendChild(popupText);
      setTimeout(() => {
        if (BaseRealtimeLayer.openPopupIds.includes(popupId)) {
          BaseRealtimeLayer.togglePopup(popupId, true);
        }
      }, 150);
      return _data;
    }
  }

  /**
   *
   * @param {VehicleProperty} properties
   * @param {AlertProperty[]} alerts
   * @param {PredictionProperty[]} predictions
   */
  #fillSidebar(properties, alerts, predictions) {
    const container = document.getElementById(BaseRealtimeLayer.sideBarOtherId);
    if (!container) return;
    document.getElementById(BaseRealtimeLayer.sideBarMainId).style.display =
      "none";
    container.style.display = "block";
    // container.innerHTML = /*HTML*/``; <span class="fa subheader">&#xf08e;</span>
    container.innerHTML = /*HTML*/ `
    <div>
      <a href="${properties.route?.route_url}" target="_blank" rel="noopener">
         <h2  class="sidebar-title" style="color:#${properties.route_color};">${
      properties.display_name
    }</h2>
      </a>
      <span>${
        VehicleLayer.#worcester_map[properties.trip_short_name] ||
        `${VehicleLayer.#direction_map[properties.direction_id] || "null"} to ${
          properties.headsign
        }`
      }
      </span>
      <hr />
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
   * wraps this.#fillPredictionData and this.#fillAlertData for a single vehicle
   *
   * basically, `onclick`
   *
   * @param {VehicleProperty} properties
   * @param {this} _this override `this`
   */
  #fillDataWrapper(properties, _this = null) {
    _this ||= this;
    window.location.hash = `#${properties.vehicle_id}`;
    Promise.all([
      _this.#fillPredictionData(properties.trip_id),
      _this.#fillAlertData(properties.trip_id),
    ]).then(([pred, alerts]) => _this.#fillSidebar(properties, alerts, pred));
    // _this.#fillAlertData(properties.trip_id);
    // _this.#fillPredictionData(properties.trip_id);
    _updateTimestamp(
      `vehicle-${properties.vehicle_id}-timestamp-${_this.iter || 1}`,
      properties.timestamp
    );
  }
}
