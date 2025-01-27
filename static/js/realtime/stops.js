/**
 * @file facilities.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperties, PredictionProperty, AlertProperty, Facility, StopProperty, AlertProperty } from "../types/index.js"
 * @import { Realtime } from "leaflet";
 * @import {_RealtimeLayer} from "./base.js"
 * @exports StopLayer
 */

"use strict";

/**
 * encapsulates stops
 */
class StopLayer extends _RealtimeLayer {
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  constructor(options) {
    super(options);
  }
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  plot(options) {
    const _this = this;
    options = { ...this.options, ...options };
    const realtime = L.realtime(options.url, {
      interval: 120000,
      type: "FeatureCollection",
      container: options.layer,
      cache: true,
      removeMissing: true,
      getFeatureId: (f) => f.id,
      onEachFeature(f, l) {
        l.bindPopup(_this.#getPopupText(f.properties), options.textboxSize);
        l.feature.properties.searchName = f.properties.stop_name;
        if (!options.isMobile) l.bindTooltip(f.properties.stop_name);
        l.setIcon(_this.#getIcon());
        l.setZIndexOffset(-100);
        l.on("click", () => _this.fillDataWrapper(f.properties));
      },
    });
    realtime.on("update", (e) => {
      Object.keys(e.update).forEach(
        function (id) {
          /**@type {L.Layer} */
          const layer = realtime.getLayer(id);
          const feature = e.update[id];
          const _onclick = () => {
            _this.#fillDataWrapper(feature.properties.trip_id, _this);
          };
          layer.feature.properties.searchName = feature.properties.stop_name;
          const wasOpen = layer.getPopup()?.isOpen() || false;
          layer.unbindPopup();
          if (wasOpen) layer.closePopup();
          layer.bindPopup(
            _this.#getPopupText(feature.properties),
            options.textboxSize
          );
          if (wasOpen) {
            layer.openPopup();
            setTimeout(_onclick, 200);
          }
          layer.off("click", _onclick);
          layer.once("click", _onclick);
        }.bind(realtime)
      );
    });
    return realtime;
  }

  #getIcon() {
    return L.icon({ iconUrl: "static/img/mbta.png", iconSize: [12, 12] });
  }

  /**
   * text for popup
   * @param {StopProperty} properties from geojson
   * @returns {HTMLDivElement} - vehicle props
   */
  #getPopupText(properties) {
    const stopHtml = document.createElement("div");
    const primeRoute = properties.routes
      .sort((a, b) => a.route_type - b.route_type)
      ?.at(0);
    stopHtml.innerHTML = /* HTML */ ` <p>
        <a
          href="${properties.stop_url}"
          rel="noopener"
          target="_blank"
          style="color:#${primeRoute?.route_color || "var(--text-color)"}"
          class="popup_header"
        >
          ${properties.stop_name.replace("/", " / ")}
        </a>
      </p>
      <p class="popup_subheader">${properties.zone_id || "zone-1A"}</p>
      <hr />
      ${
        ["0", "1"].includes(properties.wheelchair_boarding)
          ? `<span
        class="fa tooltip"
        data-tooltip="wheelchair accessible ${
          properties.wheelchair_boarding == "0" ? "w/ caveats" : ""
        }"
      >${_RealtimeLayer.icons.wheelchair}
      </span>${_RealtimeLayer.icons.space}`
          : ""
      }
        <span
          name="predictions-stop-${properties.stop_id}"
          class="fa hidden popup tooltip"
          data-tooltip="predictions"
        >
          ${_RealtimeLayer.iconSpacing("prediction")}
        </span>
        <span
          name="alert-stop-${properties.stop_id}"
          class="fa hidden popup tooltip slight-delay"
          data-tooltip="alerts"
        >
          ${_RealtimeLayer.icons.alert}
        </span>
        <p>
          ${properties.routes
            .map(
              (r) =>
                `<a href="${r.route_url}" rel="noopener" target="_blank" style="color:#${r.route_color}">${r.route_name}</a>`
            )
            .join(", ")}
        </p>
        <div class="popup_footer">
          <p>${properties.stop_id} @ ${properties.stop_address}</p>
          <p>${formatTimestamp(properties.timestamp)}</p>
        </div></span
      >`;

    return stopHtml;
  }

  /**
   * wrapper for this.#fillAlertData and this.#fillPredictionsData
   * @param {StopProperty} properties
   */
  fillDataWrapper(properties) {
    this.#fillAlertData(properties.stop_id);
    this.#fillPredictionData(properties.stop_id, properties.child_stops);
  }

  /**
   * wraps this.#fillPredictionData and this.#fillAlertData
   * @param {string} trip_id
   * @param {this} _this override `this`
   */
  #fillDataWrapper(trip_id, _this = null) {
    _this ||= this;
    _this.#fillAlertData(trip_id);
    _this.#fillPredictionData(trip_id);
  }

  /**
   *
   * @param {string} stop_id
   */
  async #fillAlertData(stop_id) {
    for (const alertEl of document.getElementsByName(`alert-stop-${stop_id}`)) {
      const popupId = `popup-alert-${stop_id}`;
      // const oldTooltip = alertEl.getAttribute("data-tooltip");
      super.loadingIcon(alertEl, popupId, {
        style: "border-top: var(--border) solid var(--slight-delay);",
      });
      const popupText = document.createElement("span");
      popupText.classList.add("popuptext");
      popupText.style.minWidth = "350px";
      popupText.id = popupId;
      /**@type {StopProperty[]} */
      const _data = await (
        await fetch(`/api/stop?stop_id=${stop_id}&include=alerts`)
      ).json();
      if (!_data || !_data.length || !_data[0].alerts.length) {
        return alertEl.classList.add("hidden");
      }
      popupText.innerHTML =
        "<table class='data-table'><tr><th>alert</th><th>timestamp</th></tr>" +
        _data[0].alerts
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
      alertEl.innerHTML = _RealtimeLayer.icons.alert;
      alertEl.appendChild(popupText);
      setTimeout(() => {
        if (openPopups.includes(popupId)) togglePopup(popupId, true);
      }, 500);
    }
  }
  /**
   *
   * @param {string} stop_id
   * @param {StopProperty[]} child_stops
   */
  async #fillPredictionData(stop_id, child_stops) {
    for (const predEl of document.getElementsByName(
      `predictions-stop-${stop_id}`
    )) {
      const popupId = `popup-predictions-${stop_id}`;
      const currTime = new Date().getTime() / 1000;
      const prevHtml = super.loadingIcon(predEl, popupId);
      // alertEl.innerHTML = "<span class='loader'></span>";
      const popupText = document.createElement("span");
      popupText.classList.add("popuptext");
      popupText.id = popupId;
      popupText.innerHTML = "...";
      const _data = [];
      for (const child of child_stops.filter((s) => s.location_type == 0)) {
        _data.push(
          ...(await (
            await fetch(
              `/api/prediction?stop_id=${child.stop_id}&departure_time>${currTime}&include=route,stop_time,trip`
            )
          ).json())
        );
      }

      if (!_data.length) return predEl.classList.add("hidden");

      popupText.innerHTML =
        "<table class='data-table' style='min-width:400px'><tr><th>route</th><th>trip</th><th>dest</th><th>est</th></tr>" +
        _data
          .sort(
            (a, b) =>
              (a.departure_time || a.arrival_time) -
              (b.departure_time || b.arrival_time)
          )
          .map(function (d) {
            const realDeparture = d.departure_time || d.arrival_time;
            let delayText = d.delay ? `${Math.floor(d.delay / 60)}` : "";
            if (delayText === "0") {
              delayText = "";
            } else if (d.delay > 0) {
              delayText = `+${delayText}`;
            }
            if (delayText) {
              delayText += " min";
            }
            // const realTime = d.departure_time || d.arrival_time;
            return `<tr>
              <td style='color:#${
                d.route.route_color
              }'>${d.route.route_name.replace(" Line", "").replace("/", " / ")}</td>
              <td>${d.trip?.trip_short_name || d.trip_id}</td>
              <td>${d.headsign}</td>
              <td>
                ${formatTimestamp(realDeparture, "%I:%M %P")}
                <i class='${getDelayClassName(d.delay)}'>${delayText}</i>
              </td>
            </tr>
            `;
          })
          .join("") +
        "</table>";
      predEl.innerHTML = _RealtimeLayer.iconSpacing("prediction");
      predEl.appendChild(popupText);
      setTimeout(() => {
        if (openPopups.includes(popupId)) togglePopup(popupId, true);
      }, 500);
    }
  }
}
