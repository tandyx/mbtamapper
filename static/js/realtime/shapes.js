/**
 * @file facilities.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperties, PredictionProperty, AlertProperty, Facility, ShapeProperty } from "../types/index.js"
 * @import { Realtime } from "leaflet";
 * @import {_RealtimeLayer} from "./base.js"
 * @exports ShapeLayer
 */
"use strict";

/**
 * represents the shape layer
 */
class ShapeLayer extends _RealtimeLayer {
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
    const polyLineRender = L.canvas({ padding: 0.5, tolerance: 10 });
    const realtime = L.realtime(options.url, {
      interval: 3600000,
      type: "FeatureCollection",
      container: options.layer,
      cache: true,
      removeMissing: true,
      getFeatureId: (f) => f.id,
      onEachFeature(f, l) {
        l.setStyle({
          color: `#${f.properties.route_color}`,
          weight: 1.3,
          renderer: polyLineRender,
        });
        l.id = f.properties.route_id;
        l.feature.properties.searchName = f.properties.route_name;
        l.bindPopup(_this.#getPopupText(f.properties), options.textboxSize);
        if (!options.isMobile) l.bindTooltip(f.properties.route_name);
        l.once("click", () => _this.#fillAlertData(f.properties.route_id));
      },
    });
    realtime.on("update", super.handleUpdateEvent);
    return realtime;
  }

  /**
   * text for popup
   * @param {ShapeProperty} properties from geojson
   * @returns {HTMLDivElement} - vehicle props
   */
  #getPopupText(properties) {
    const shapeHtml = document.createElement("div");
    shapeHtml.innerHTML = /* HTML */ `
      <p>
        <a
          href="${properties.route_url}"
          rel="noopener"
          target="_blank"
          style="color:#${properties.route_color}"
          class="popup_header"
        >
          ${properties.route_name.replace("/", " / ")}
        </a>
      </p>
      <p class="popup_subheader">${properties.route_desc}</p>
      <hr />
      <span
        name="alert-shape-${properties.route_id}"
        class="fa hidden popup tooltip slight-delay"
        data-tooltip="alerts"
      >
        ${_RealtimeLayer.icons.alert}
      </span>
      <p>
        ${properties.route_id} @
        <a
          href="${properties.agency.agency_url}"
          rel="noopener"
          target="_blank"
        >
          ${properties.agency.agency_name}
        </a>
      </p>
      <p>${properties.agency.agency_phone}</p>
      <div class="popup_footer">
        <p>${formatTimestamp(properties.timestamp)}</p>
      </div>
    `;
    return shapeHtml;
  }

  /**
   * fill alert shape data
   * @param {string} route_id
   */
  async #fillAlertData(route_id) {
    for (const alertEl of document.getElementsByName(
      `alert-shape-${route_id}`
    )) {
      const popupId = `popup-alert-${route_id}`;
      super.popupLoadingIcon(alertEl, popupId, {
        style: "border-top: var(--border) solid var(--slight-delay);",
      });

      const popupText = document.createElement("span");
      popupText.classList.add("popuptext");
      popupText.style.minWidth = "350px";
      popupText.id = popupId;
      popupText.innerHTML = "...";
      /**@type {AlertProperty[]} */
      const _data = await (
        await fetch(`/api/alert?route_id=${route_id}&stop_id=null`)
      ).json();
      if (!_data.length) return alertEl.classList.add("hidden");
      popupText.innerHTML =
        "<table class='data-table'><tr><th>alert</th><th style='width:40%;'>period</th></tr>" +
        _data
          .map((d) => {
            const strf = "%m-%d";
            const start = d.active_period_start
              ? formatTimestamp(d.active_period_start, strf)
              : null;
            const end = d.active_period_end
              ? formatTimestamp(d.active_period_end, strf)
              : null;
            return `<tr>
                <td>${d.header}</td>
                <td>${start} to ${end}</td>
              </tr>`;
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
}
