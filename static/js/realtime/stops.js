/**
 * @file facilities.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperty, PredictionProperty, AlertProperty, Facility, StopProperty, AlertProperty, StopTime } from "../types/index.js"
 * @import { Realtime } from "leaflet";
 * @import {BaseRealtimeLayer} from "./base.js"
 * @exports StopLayer
 */

"use strict";

/**
 * encapsulates stops
 */
class StopLayer extends BaseRealtimeLayer {
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
    const onClickOpts = { _this, idField: "stop_id" };
    const realtime = L.realtime(options.url, {
      interval: 45000,
      type: "FeatureCollection",
      container: options.layer,
      cache: true,
      removeMissing: true,
      getFeatureId: (f) => f.id,
      onEachFeature(fea, lay) {
        // lay.setStyle({
        //   renderer: L.canvas({ padding: 0.5, tolerance: 10 }),
        // });
        lay.id = fea.id;
        lay.bindPopup(_this.#getPopupHTML(fea.properties), options.textboxSize);
        lay.feature.properties.searchName = fea.properties.stop_name;
        if (!options.isMobile) lay.bindTooltip(fea.properties.stop_name);
        lay.setIcon(_this.#getIcon());
        lay.setZIndexOffset(-100);
        lay.on("click", (_e) =>
          _this.#_onclick(_e, { ...onClickOpts, properties: fea.properties })
        );
      },
    });
    realtime.on("update", (_e) => {
      Object.keys(_e.update).forEach(
        function (id) {
          /**@type {Layer} */
          const layer = realtime.getLayer(id);
          /**@type {GeoJSON.Feature<GeoJSON.Geometry, StopProperty} */
          const feature = _e.update[id];
          const wasOpen = layer.getPopup()?.isOpen() || false;
          const properties = feature.properties;
          layer.id = feature.id;
          layer.feature.properties.searchName = feature.properties.stop_name;
          layer.unbindPopup();
          const onClick = () =>
            _this.#_onclick(_e, { ...onClickOpts, properties: properties });
          if (wasOpen) layer.closePopup();
          layer.bindPopup(_this.#getPopupHTML(properties), options.textboxSize);
          layer.setIcon(_this.#getIcon(properties));
          if (wasOpen) {
            _this.options.map.setView(
              layer.getLatLng(),
              _this.options.map.getZoom(),
              { animate: true }
            );
            layer.openPopup();
            setTimeout(onClick, 200);
          }
          layer.once("click", onClick);
        }.bind(this)
      );
    });
    return realtime;
  }

  #getIcon() {
    return L.icon({ iconUrl: "static/img/mbta.png", iconSize: [12, 12] });
  }
  /**
   *
   * @param {StopProperty} properties
   */
  #getHeaderHTML(properties) {
    const primeRoute = properties.routes
      .sort((a, b) => a.route_type - b.route_type)
      ?.at(0);

    return /* HTML */ `<div>
      <div>
        <a
          href="${properties.stop_url}"
          rel="noopener"
          target="_blank"
          style="color:#${primeRoute?.route_color || "var(--text-color)"}"
          class="popup_header"
        >
          ${properties.stop_name.replace("/", " / ")}
        </a>
      </div>
      <div class="popup_subheader">${properties.zone_id || "zone-1A"}</div>
      <hr />
    </div>`;
  }
  /**
   *
   * @param {StopProperty} properties
   */
  #getWheelchairHTML(properties) {
    if (["0", "1"].includes(properties.wheelchair_boarding)) {
      return /* HTML */ `<span
        class="fa tooltip"
        data-tooltip="wheelchair accessible ${properties.wheelchair_boarding ==
        "0"
          ? "w/ caveats"
          : ""}"
        >${BaseRealtimeLayer.iconSpacing("wheelchair")}</span
      >`;
    }
    return "";
  }
  /**
   *
   * @param {StopProperty} properties
   */
  #getFooterHTML(properties) {
    return /* HTML */ ` <div class="popup_footer">
      <p>${properties.stop_id} @ ${properties.stop_address}</p>
      <p>${formatTimestamp(properties.timestamp)}</p>
    </div>`;
  }

  /**
   * text for popup
   * @param {StopProperty} properties from geojson
   * @returns {HTMLDivElement} - vehicle props
   */
  #getPopupHTML(properties) {
    const stopHtml = document.createElement("div");

    stopHtml.innerHTML = /* HTML */ `<div>
      ${this.#getHeaderHTML(properties)} ${this.#getWheelchairHTML(properties)}
      ${super.moreInfoButton(properties.stop_id)}
      <div>
        ${properties.routes
          .map(
            (r) =>
              `<a href="${r.route_url}" rel="noopener" target="_blank" style="color:#${r.route_color}">${r.route_name}</a>`
          )
          .join(", ")}
      </div>
      ${this.#getFooterHTML(properties)}
    </div>`;

    return stopHtml;
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
   *
   * @param {StopProperty} properties
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

    /** @type {StopProperty[]} */
    const stop = await fetchCache(
      `/api/stop?stop_id=${properties.stop_id}&_=${timestamp}&include=alerts,predictions`,
      { cache: "force-cache" },
      super.defaultFetchCacheOpt
    );
    /**@type {StopTime[]} */
    const stopTimes = (
      await Promise.all(
        properties.child_stops
          .filter((cs) => cs.location_type == 0 && cs.vehicle_type == 2)
          .map(
            async (cs) =>
              await fetchCache(
                `/api/stoptime?stop_id=${cs.stop_id}&departure_timestamp>${
                  timestamp * 10 - 60
                }&include=trip`,
                { cache: "force-cache" },
                super.defaultFetchCacheOpt
              )
          )
      )
    ).flat();

    console.log(stopTimes);

    const alerts = stop.flatMap((s) => s.alerts);
    const predictions = stop.flatMap((s) => s.predictions);
    super.moreInfoButton(properties.stop_id, { alert: Boolean(alerts.length) });
    sidebar.style.display = "initial";

    container.innerHTML = /* HTML */ `<div>
      ${this.#getHeaderHTML(properties)} ${super.getAlertsHTML(alerts)}
      <div>
        ${properties.routes
          .map((route) => {
            const _predictions = predictions
              .filter((p) => p.route_id === route.route_id)
              .sort(
                (a, b) =>
                  a.arrival_time - b.arrival_time ||
                  a.departure_time - b.departure_time
              );
            const _stoptimes = stopTimes.filter(
              (st) =>
                st.trip?.route_id === route.route_id &&
                !_predictions.map((p) => p.trip_id).includes(st.trip_id)
            );

            return /* HTML */ `<div style="margin-bottom: 5px;">
              <table class="data-table">
                <thead>
                  ${super.tableHeaderHTML(route, 3)}
                  ${((_predictions.length || _stoptimes.length) &&
                    `<tr>
                    <th>Trip</th>
                    <th>Time</th>
                    <th>Destination</th>
                  </tr>`) ||
                  ""}
                </thead>
                <tbody>
                  ${_predictions
                    .map((pred) => {
                      const st = stopTimes
                        .filter((st) => pred.trip_id === st.trip_id)
                        .at(0);
                      return /* HTML */ `<tr>
                        <td>
                          <a
                            onclick="new LayerFinder(_map).clickVehicle('${pred.vehicle_id}')"
                            >${st?.trip?.trip_short_name || pred.trip_id}</a
                          >
                        </td>
                        <td>
                          ${formatTimestamp(
                            pred.arrival_time || pred.departure_time,
                            "%I:%M %P"
                          )}
                          <i class="${getDelayClassName(pred.delay)}"
                            >${getDelayText(pred.delay)}</i
                          >
                        </td>
                        <td>${st?.stop_headsign || pred.headsign}</td>
                      </tr>`;
                    })
                    .join("")}
                  ${_stoptimes
                    .map(
                      (st) => /* HTML */ `<tr>
                        <td>${st.trip?.trip_short_name || st.trip_id}</td>
                        <td>
                          ${formatTimestamp(
                            st.arrival_timestamp || st.departure_timestamp,
                            "%I:%M %P"
                          )}
                          <span class="tooltip fa" data-tooltip="Scheduled Only"
                            >&#xf017;</span
                          >
                        </td>
                        <td>${st.stop_headsign || st.trip?.trip_headsign}</td>
                      </tr>`
                    )
                    .join("")}
                </tbody>
              </table>
            </div>`;
          })
          .join("")}
      </div>
      ${this.#getFooterHTML(properties)}
    </div>`;
  }
}
