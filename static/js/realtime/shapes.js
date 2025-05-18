/**
 * @file facilities.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperty, PredictionProperty, AlertProperty, Facility, ShapeProperty } from "../types/index.js"
 * @import { Realtime } from "leaflet";
 * @import {BaseRealtimeLayer} from "./base.js"
 * @exports ShapeLayer
 */
"use strict";

/**
 * represents the shape layer
 */
class ShapeLayer extends BaseRealtimeLayer {
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
    /** @type {BaseRealtimeOnClickOptions<ShapeProperty>} */
    const onClickOpts = { _this, idField: "route_id" };
    const polyLineRender = L.canvas({ padding: 0.5, tolerance: 7 });
    const realtime = L.realtime(options.url, {
      interval: 45000,
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
        l.bindPopup(_this.#getPopupHTML(f.properties), options.textboxSize);
        if (!options.isMobile) l.bindTooltip(f.properties.route_name);
        l.on("click", (_e) =>
          _this.#_onclick(_e, { ...onClickOpts, properties: f.properties })
        );
      },
    });
    realtime.on("update", (_e) => {
      Object.keys(_e.update).forEach(
        function (id) {
          /**@type {Layer} */
          const layer = realtime.getLayer(id);
          /**@type {GeoJSON.Feature<GeoJSON.Geometry, ShapeProperty} */
          const feature = _e.update[id];
          const wasOpen = layer.getPopup()?.isOpen() || false;
          const properties = feature.properties;
          layer.id = feature.id;
          layer.feature.properties.searchName = feature.properties.route_name;
          layer.unbindPopup();
          const onClick = () =>
            _this.#_onclick(_e, { ...onClickOpts, properties: properties });
          if (wasOpen) layer.closePopup();
          layer.bindPopup(_this.#getPopupHTML(properties), options.textboxSize);
          if (wasOpen) {
            layer.openPopup();
            setTimeout(onClick, 200);
          }
          layer.on("click", onClick);
        }.bind(this)
      );
    });
    return realtime;
  }

  /**
   * text for popup
   * @param {ShapeProperty} properties from geojson
   * @returns {HTMLDivElement} - vehicle props
   */
  #getPopupHTML(properties) {
    const shapeHtml = document.createElement("div");
    shapeHtml.innerHTML = /* HTML */ `
      ${this.#getHeaderHTML(properties)}
      ${super.moreInfoButton(properties.stop_id)}
      <div>
        ${properties.route_id} @
        <a
          href="${properties.agency.agency_url}"
          rel="noopener"
          target="_blank"
        >
          ${properties.agency.agency_name}
        </a>
      </div>
      <div>${properties.agency.agency_phone}</div>
      <div class="popup_footer">
        <div>${formatTimestamp(properties.timestamp)}</div>
      </div>
    `;
    return shapeHtml;
  }

  /**
   * to be called `onclick`
   *
   * supercedes public super method
   *
   * @param {DomEvent.PropagableEvent} event
   * @param {RealtimeLayerOnClickOptions<StopProperty>} options
   */
  #_onclick(event, options = {}) {
    super._onclick(event, options);
    /**@type {this} */
    const _this = options._this || this;
    _this.#fillSidebar(options.properties);
  }

  /**
   * @param {ShapeProperty} properties
   */
  #getHeaderHTML(properties) {
    return /* HTML */ ` <div>
      <div>
        <a
          href="${properties.route_url}"
          rel="noopener"
          target="_blank"
          style="color:#${properties.route_color}"
          class="popup_header"
        >
          ${properties.route_name.replace("/", " / ")}
        </a>
      </div>
      <div class="popup_subheader">${properties.route_desc}</div>
      <hr />
    </div>`;
  }

  /**
   *
   * @param {ShapeProperty} properties
   */
  async #fillSidebar(properties) {
    const container = BaseRealtimeLayer.toggleSidebarDisplay(
      BaseRealtimeLayer.sideBarOtherId
    );
    const sidebar = document.getElementById("sidebar");
    const timestamp = Math.round(new Date().valueOf() / 10000);
    if (!container || !sidebar) return;
    super.moreInfoButton(properties.stop_id, { loading: true });
    /**@type {PredictionProperty[]}*/
    sidebar.style.display = "flex";
    container.innerHTML = /* HTML */ `<div class="centered-parent">
      <div class="loader-large"></div>
    </div>`;

    const useSchedule =
      ["2", "4"].includes(properties.route_type) || properties.listed_route;

    /** @type {RouteProperty} */
    const route = (
      await fetchCache(
        `/api/route?route_id=${
          properties.route_id
        }&_=${timestamp}&include=alerts,predictions${
          (useSchedule && ",stop_times,trips") || ""
        }`,
        { cache: "force-cache" },
        super.defaultFetchCacheOpt
      )
    ).at(0);

    route.stop_times ||= [];

    const alerts = route.alerts.filter((a) => !a.stop_id);

    super.moreInfoButton(properties.stop_id, { alert: Boolean(alerts.length) });
    sidebar.style.display = "initial";

    const predictions = route.predictions
      .sort(
        (a, b) =>
          a.arrival_time - b.arrival_time || a.departure_time - b.departure_time
      )
      // .filter((p) => (p.arrival_time || p.departure_time) > timestamp)
      .filter((p) => {
        const subpre = route.predictions
          .filter((_p) => _p.trip_id === p.trip_id)
          .map((_p) => _p.stop_sequence);
        return p.stop_sequence === Math.min(...subpre);
      });

    const stoptimes = route.stop_times
      .sort(
        (a, b) =>
          a.arrival_timestamp - b.arrival_timestamp ||
          a.departure_timestamp - b.departure_timestamp
      )
      .filter((st) => {
        if (predictions.map((p) => p.trip_id).includes(st.trip_id)) {
          return false;
        }
        const subst = route.stop_times
          .filter((_st) => _st.trip_id === st.trip_id)
          .map((_st) => _st.stop_sequence);
        return st.stop_sequence === Math.min(...subst);
      })
      .filter(
        (st) =>
          (st.arrival_timestamp || st.departure_timestamp) >
          10 * timestamp - 300
      );

    container.innerHTML = /* HTML */ `<div>
      ${this.#getHeaderHTML(properties)} ${super.getAlertsHTML(alerts)}
      <div style="margin-top: -5px;">
        ${properties.route_id} @
        <a
          href="${properties.agency.agency_url}"
          rel="noopener"
          target="_blank"
        >
          ${properties.agency.agency_name}
        </a>
      </div>
      <div>${properties.agency.agency_phone}</div>
      <div class="my-5">
        <table class="data-table">
          <thead>
            <tr>
              <th>Trip</th>
              <th>Headsign</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${predictions
              .map((pred) => {
                const trip = route.trips
                  ?.filter((t) => t.trip_id === pred.trip_id)
                  ?.at(0);
                const _ps = route.predictions.filter(
                  (p) => p.trip_id === pred.trip_id
                );
                const headsign =
                  pred.headsign ||
                  trip?.trip_headsign ||
                  _ps
                    ?.filter(
                      (p) =>
                        p.stop_sequence ===
                        Math.max(..._ps.map((_p) => _p.stop_sequence))
                    )
                    ?.at(0)?.stop_name;

                return /* HTML */ `<tr>
                  <td>
                    <a
                      onclick="new LayerFinder(_map).clickVehicle('${pred.vehicle_id}')"
                      >${trip?.trip_short_name || pred.trip_id}</a
                    >
                  </td>
                  <td>${headsign}</td>
                  <td>
                    <span class="fa tooltip" data-tooltip="Next Stop"
                      >${BaseRealtimeLayer.icons.prediction}</span
                    >
                    <a
                      onclick="new LayerFinder(_map).clickStop('${pred.stop_id}')"
                      >${pred.stop_name}</a
                    >
                    @
                    ${formatTimestamp(
                      pred.arrival_time || pred.departure_time,
                      "%I:%M %P"
                    )}
                    <i class="${getDelayClassName(pred.delay)}"
                      >${getDelayText(pred.delay, false)}</i
                    >
                  </td>
                </tr>`;
              })
              .join("")}
            ${stoptimes
              .map((st) => {
                const trip = route.trips
                  ?.filter((t) => t.trip_id === st.trip_id)
                  ?.at(0);
                return /* HTML */ `<tr>
                  <td>${trip?.trip_short_name || st.trip_id}</td>
                  <td>${st.destination_label || trip?.trip_headsign}</td>
                  <td>
                    <span class="tooltip fa" data-tooltip="Schduled to leave"
                      >${BaseRealtimeLayer.icons.clock}</span
                    >
                    ${st.stop_name} @
                    ${formatTimestamp(
                      st.arrival_timestamp || st.departure_timestamp,
                      "%I:%M %P"
                    )}
                  </td>
                </tr>`;
              })
              .join("")}
          </tbody>
        </table>
      </div>
      <div class="popup_footer">
        <div>${formatTimestamp(properties.timestamp)}</div>
      </div>
    </div>`;
  }
}
