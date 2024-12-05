/**
 * @file shapes.js - Plot stops on map in realtime, updating every 15 seconds
 * @module shapes
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperties, PredictionProperty, AlertProperty } from "../types/index.js"
 * @import { Realtime } from "leaflet";
 * @import {_RealtimeLayer} from "./base.js"
 * @exports VehicleLayer
 */

"use strict";

/**
 * encapsulating class to plot Vehicles on a leaflet map
 * after object creation, you can call `.plot` to plot it
 */
class VehicleLayer extends _RealtimeLayer {
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

  /**
   * string or html element of vehicle
   * @param {VehicleProperties} properties from geojson
   * @returns {L.DivIcon}
   */
  #getIcon(properties) {
    const iconHtml = `
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
  }

  /**
   * @param {LayerApiRealtimeOptions?} options
   */
  plot(options) {
    const _this = this;
    options = { ..._this.options, ...options };
    const realtime = L.realtime(options.url, {
      interval: 15000,
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
        l.on("click", () => _this.#fillDataWrapper(f.properties.trip_id));
      },
    });

    realtime.on("update", function (e) {
      Object.keys(e.update).forEach(
        function (id) {
          const layer = this.getLayer(id);
          const feature = e.update[id];
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
            setTimeout(_this.#fillDataWrapper, 200, feature.properties.trip_id);
          }
          layer.on("click", () => {
            setTimeout(_this.#fillDataWrapper, 200, feature.properties.trip_id);
          });
        }.bind(this)
      );
    });

    return realtime;
  }

  /**
   * gets vehicle text
   * @param {VehicleProperties} properties
   * @returns {HTMLDivElement} - vehicle text
   */
  #getPopupText(properties) {
    const vehicleText = document.createElement("div");
    const fmtmstp = formatTimestamp(properties.timestamp, "%I:%M %P");
    vehicleText.innerHTML = /* HTML */ `
      <p>
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
        ${properties.trip_short_name === "552"
          ? "heart to hub"
          : properties.trip_short_name === "549"
          ? "hub to heart"
          : `${
              VehicleLayer.#direction_map[properties.direction_id] || "null"
            } to ${properties.headsign}`}
      </p>
      <hr />
      <span class="fa tooltip" data-tooltip="bikes allowed"
        >${properties.bikes_allowed ? "&#xf206;&nbsp;&nbsp;&nbsp;" : ""}
      </span>
      <span
        name="pred-veh-${properties.trip_id}"
        class="fa hidden popup tooltip"
        data-tooltip="predictions"
      >
        &#xf239;&nbsp;&nbsp;&nbsp;
      </span>
      <span
        name="alert-veh-${properties.trip_id}"
        class="fa hidden popup tooltip slight-delay"
        data-tooltip="alerts"
      >
        &#xf071;&nbsp;&nbsp;&nbsp;
      </span>
      ${properties.stop_time
        ? `${
            properties.current_status != "STOPPED_AT"
              ? `
      <p>${almostTitleCase(properties.current_status)} ${
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
                }</p>
    `
              : `
      <p>${almostTitleCase(properties.current_status)} ${
                  properties.stop_time.stop_name
                }</p>`
          }
    ${
      properties.next_stop?.delay !== null
        ? `
      ${
        Math.round(properties.next_stop?.delay / 60) !== 0
          ? `
          <i 
            class='${getDelayClassName(properties.next_stop?.delay)}'
          > ${Math.abs(Math.round(properties.next_stop?.delay / 60))} minutes ${
              getDelayClassName(properties.next_stop?.delay) === "on-time"
                ? "early"
                : "late"
            }
          </i>`
          : "<i>on time</i>"
      }
    `
        : ""
    }
  `
        : properties.next_stop
        ? `
    ${
      properties.current_status != "STOPPED_AT"
        ? `
      <p>${almostTitleCase(properties.current_status)} ${
            properties.next_stop.stop_name
          } - ${fmtmstp}</p>
    `
        : `
      <p>${almostTitleCase(properties.current_status)} ${
            properties.next_stop.stop_name
          }</p>
    `
    }
  `
        : ""}
      ${properties.occupancy_status != null
        ? `
    <p>
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
    </p>
  `
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
        <p>${formatTimestamp(properties.timestamp)}</p>
      </div>
    `;
    return vehicleText;
  }

  /**
   * fill prediction data in for `pred-veh-{trip_id}` element
   * this appears as a popup on the map
   * @param {string} trip_id - vehicle id
   * @param {boolean} popup - whether to show the popup
   * @returns {void}
   */
  static async fillPredictionData(trip_id) {
    for (const predEl of document.getElementsByName(`pred-veh-${trip_id}`)) {
      const popupId = `popup-pred-${trip_id}`;
      predEl.onclick = function () {
        togglePopup(popupId);
      };

      const popupText = document.createElement("span");

      popupText.classList.add("popuptext");
      popupText.id = popupId;
      popupText.innerHTML = "...";
      /**@type {PredictionProperty[]}*/
      const _data = await (
        await fetch(`/api/prediction?trip_id=${trip_id}&include=stop_time`)
      ).json();
      if (!_data.length) return;
      predEl.classList.remove("hidden");
      popupText.innerHTML =
        "<table class='data-table'><tr><th>stop</th><th>estimate</th></tr>" +
        _data
          .sort(
            (a, b) =>
              (a.departure_time || a.arrival_time) -
              (b.departure_time || b.arrival_time)
          )
          .map(function (d) {
            const realDeparture = d.departure_time || d.arrival_time;
            if (!realDeparture || realDeparture < Date().valueOf()) return "";
            const delayText = getDelayText(d.delay);
            let stopTimeClass,
              tooltipText = "";
            if (d.stop_time?.flag_stop) {
              stopTimeClass = "flag_stop tooltip";
              tooltipText = "flag stop";
              // d.stop_name += " <span class='fa'>&#xf024;</span>";
              d.stop_name += "<i> f</i>";
            } else if (d.stop_time?.early_departure) {
              stopTimeClass = "early_departure tooltip";
              tooltipText = "early departure";
              d.stop_name += "<i> L</i>";
              // d.stop_name += " <span class='fa'>&#xf023;</span>";
            }

            return `<tr>
              <td class='${stopTimeClass}' data-tooltip='${tooltipText}'>${d.stop_name}</td>
              <td>
                ${formatTimestamp(realDeparture, "%I:%M %P")}
                <i class='${getDelayClassName(d.delay)}'>${delayText}</i>
              </td>
            </tr>
            `;
          })
          .join("") +
        "</table>";
      predEl.appendChild(popupText);
      setTimeout(() => {
        if (openPopups.includes(popupId)) togglePopup(popupId, true);
      }, 400);
    }
  }
  /**
   *  fill alert prediction data
   * @param {string} trip_id - vehicle id
   */
  static async fillAlertData(trip_id) {
    for (const alertEl of document.getElementsByName(`alert-veh-${trip_id}`)) {
      const popupId = `popup-alert-${trip_id}`;
      alertEl.onclick = function () {
        togglePopup(popupId);
      };

      const popupText = document.createElement("span");

      popupText.classList.add("popuptext");
      popupText.id = popupId;
      popupText.innerHTML = "...";
      /** @type {AlertProperty[]} */
      const _data = await (await fetch(`/api/alert?trip_id=${trip_id}`)).json();
      if (!_data.length) return;
      alertEl.classList.remove("hidden");
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
      alertEl.appendChild(popupText);
      setTimeout(() => {
        if (openPopups.includes(popupId)) togglePopup(popupId, true);
      }, 150);
    }
  }
  /**
   * wraps this.#fillPredictionData and this.#fillAlertData
   * @param {string} trip_id
   */
  #fillDataWrapper(trip_id) {
    VehicleLayer.fillAlertData(trip_id);
    VehicleLayer.fillPredictionData(trip_id);
  }
}
