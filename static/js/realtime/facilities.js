/**
 * @file facilities.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperties, PredictionProperty, AlertProperty, Facility } from "../types/index.js"
 * @import { Realtime } from "leaflet";
 * @import {_RealtimeLayer} from "./base.js"
 * @exports FacilityLayer
 */
/**
 * represents the facility class
 */
class FacilityLayer extends _RealtimeLayer {
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
      interval: 3600000,
      type: "FeatureCollection",
      container: options.layer,
      cache: true,
      removeMissing: true,
      getFeatureId: (f) => f.id,
      onEachFeature(f, l) {
        l.bindPopup(_this.#getPopupText(f.properties), options.textboxSize);
        l.feature.properties.searchName = f.properties.facility_long_name;
        if (!options.isMobile) l.bindTooltip(f.properties.facility_long_name);
        l.setIcon(_this.#getIcon());
        l.setZIndexOffset(-150);
      },
    });
    realtime.on("update", super.handleUpdateEvent);
    return realtime;
  }

  #getIcon() {
    return L.icon({ iconUrl: "static/img/parking.png", iconSize: [15, 15] });
  }

  /**
   * text for popup
   * @param {Facility} properties from geojson
   * @returns {HTMLDivElement} - vehicle props
   */
  #getPopupText(properties) {
    const facilityHtml = document.createElement("div");
    const capac_acc = properties["capacity-accessible"];
    facilityHtml.innerHTML = /* HTML */ `
      <p>
        <a
          href="${properties["contact-url"]}"
          rel="noopener"
          target="_blank"
          class="facility_header popup_header"
        >
          ${properties.facility_long_name}
        </a>
      </p>
      <p class="popup_subheader">
        <a href="${properties["contact-url"]}" rel="noopener" target="_blank">
          ${properties.operator}
        </a>
      </p>
      <hr />
      <p>
        <span class="fa tooltip" data-tooltip="${properties.capacity} spots"
          >&#xf1b9;</span
        >&nbsp;&nbsp;&nbsp;
        ${capac_acc !== "0" && capac_acc
          ? `
        <span class='fa tooltip' data-tooltip='${capac_acc} spots'>&#xf193;</span>
      `
          : ""}
      </p>
      <p>${properties["fee-daily"]}</p>
      <p>
        <a href="${properties["payment-app-url"]}">
          ${properties["payment-app"]} ${properties["payment-app-id"]}
        </a>
      </p>
      <div class="popup_footer">
        <p>${properties.facility_id} @ ${properties.contact}</p>
        <p>${properties["contact-phone"]}</p>
        <p>${formatTimestamp(properties.timestamp)}</p>
      </div>
    `;
    return facilityHtml;
  }
}
