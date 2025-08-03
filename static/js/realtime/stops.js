/**
 * @file facilities.js
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperty, PredictionProperty, AlertProperty, Facility, StopProperty, AlertProperty, StopTimeProperty } from "../types/index.js"
 * @import { Realtime } from "leaflet";
 * @import {BaseRealtimeLayer} from "./base.js"
 * @exports StopLayer
 */

"use strict";

/**
 * encapsulates stops
 */
class StopLayer extends BaseRealtimeLayer {
  /**@type {((event: L.LeafletMouseEvent) => void)[] } */
  static onClickArry = [];

  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  constructor(options) {
    options.interval = options.interval || 45000;
    super(options);
  }
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  plot(options) {
    const _this = this;
    options = { ...this.options, ...options };
    /** @type {BaseRealtimeOnClickOptions<StopProperty>} */
    const onClickOpts = { _this, idField: "stop_id" };
    const realtime = L.realtime(options.url, {
      interval: options.interval,
      type: "FeatureCollection",
      container: options.layer,
      cache: true,
      removeMissing: true,
      interactive: options.interactive,
      getFeatureId: (f) => f.id,
      onEachFeature(fea, l) {
        // lay.setStyle({
        //   renderer: L.canvas({ padding: 0.5, tolerance: 10 }),
        // });
        l.id = fea.id;
        l.bindPopup(_this.#getPopupHTML(fea.properties), options.textboxSize);
        l.feature.properties.searchName = fea.properties.stop_name;
        if (!options.isMobile) l.bindTooltip(fea.properties.stop_name);
        l.setIcon(_this.#getIcon());
        l.setZIndexOffset(-100);
        /** @type {(event: L.LeafletMouseEvent) => void } */
        const onClick = (_e) => {
          _this.#_onclick(_e, { ...onClickOpts, properties: fea.properties });
        };
        StopLayer.onClickArry.forEach((fn) => l.off("click", fn));
        StopLayer.onClickArry.push(onClick);
        l.on("click", onClick);
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
          StopLayer.onClickArry.forEach((fn) => layer.off("click", fn));
          StopLayer.onClickArry.push(onClick);
          layer.on("click", onClick);
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
        data-tooltip="Wheelchair Accessible ${properties.wheelchair_boarding ==
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
      <p>${formatTimestamp(properties.timestamp, "%Y%m%d %I:%M %P")}</p>
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
  async #_onclick(event, options = {}) {
    super._onclick(event, options);
    /**@type {this} */
    const _this = options._this || this;
    await _this.#fillSidebar(options.properties);
    super._afterClick(event, options);
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
    const timestamp = Math.round(new Date().valueOf() / 1000);
    if (!container || !sidebar) return;
    super.moreInfoButton(properties.stop_id, { loading: true });
    /**@type {PredictionProperty[]}*/
    sidebar.style.display = "flex";
    container.innerHTML = /* HTML */ `<div class="centered-parent">
      <div class="loader-large"></div>
    </div>`;

    /** @type {StopProperty[]} */
    const stop = await fetchCache(
      `/api/stop?stop_id=${properties.stop_id}&_=${Math.round(
        timestamp / 10
      )}&include=alerts,predictions`,
      { cache: "force-cache" },
      super.defaultFetchCacheOpt
    );
    const childStops = Boolean(properties.child_stops.length)
      ? properties.child_stops
      : [properties];

    /**@type {StopTimeProperty[]} */
    const stopTimes = (
      await Promise.all(
        childStops
          .filter(
            (cs) =>
              (cs.location_type == 0 && ["2", "4"].includes(cs.vehicle_type)) ||
              cs.stop_name.toLowerCase().includes("shuttle")
          )
          .map(
            async (cs) =>
              await fetchCache(
                `/api/stoptime?stop_id=${
                  cs.stop_id
                }&operates_today=True&_=${formatTimestamp(
                  timestamp,
                  "%Y%m%d"
                )}&include=trip`,
                { cache: "force-cache" },
                super.defaultFetchCacheOpt
              )
          )
      )
    ).flat();

    const alerts = stop.flatMap((s) => s.alerts);
    super.moreInfoButton(properties.stop_id, { alert: Boolean(alerts.length) });
    sidebar.style.display = "initial";

    /**@type {StopTimeAttrObj[]} */
    const specialStopTimes = [];

    container.innerHTML = /* HTML */ `<div>
      ${this.#getHeaderHTML(properties)} ${super.getAlertsHTML(alerts)}
      ${this.#getWheelchairHTML(properties)}
      <div>
        ${properties.routes
          .map((route) => {
            const _predictions = stop
              .flatMap((s) => s.predictions)
              .filter((p) => p.route_id === route.route_id)
              .sort(
                (a, b) =>
                  a.arrival_time - b.arrival_time ||
                  a.departure_time - b.departure_time
              );
            const _stoptimes = stopTimes
              .filter(
                (st) =>
                  st.trip?.route_id === route.route_id &&
                  !_predictions.map((p) => p.trip_id).includes(st.trip_id) &&
                  (st.arrival_timestamp || st.departure_timestamp) > timestamp
              )
              .sort(
                (a, b) =>
                  a.arrival_timestamp - b.arrival_timestamp ||
                  a.departure_timestamp - b.departure_timestamp
              );

            return /* HTML */ `<div class="my-5">
              <table class="data-table">
                <thead>
                  ${super.tableHeaderHTML(route, {
                    colspan: 3,
                    onclick: Boolean(_predictions.length || _stoptimes.length),
                  })}
                  ${((_predictions.length || _stoptimes.length) &&
                    `<tr>
                    <th>Trip</th>
                    <th>Time</th>
                    <th>Destination</th>
                  </tr>`) ||
                  ""}
                </thead>
                <tbody class="directional">
                  ${_predictions
                    .map((pred) => {
                      const st = stopTimes
                        .filter((st) => pred.trip_id === st.trip_id)
                        .at(0);
                      const dom = pred.arrival_time || pred.departure_time; // sometimes i want one
                      const stAttrs = specialStopTimeAttrs(st, route);
                      specialStopTimes.push(stAttrs);
                      return /* HTML */ `<tr
                        data-direction-${parseInt(pred.direction_id)}
                      >
                        <td>
                          <a
                            class="${stAttrs.cssClass} ${stAttrs.tooltip &&
                            "tooltip"}"
                            data-tooltip="${stAttrs.tooltip}"
                            onclick="LayerFinder.fromGlobals().clickVehicle('${pred.vehicle_id}')"
                            >${st?.trip?.trip_short_name || pred.trip_id}
                          </a>
                          ${BaseRealtimeLayer.trackIconHTML({
                            stop_id: pred.stop_id,
                            direction_id: pred.direction_id,
                            route_type: route.route_type,
                          })}
                        </td>
                        <td>
                          <span
                            class="tooltip fa"
                            data-tooltip="${minuteify(dom - timestamp, [
                              "seconds",
                            ]) || "0 min"} away"
                            >${BaseRealtimeLayer.icons.prediction}</span
                          >
                          ${formatTimestamp(
                            pred.arrival_time || pred.departure_time,
                            "%I:%M %P"
                          )}
                          <i class="${getDelayClassName(pred.delay)}"
                            >${getDelayText(pred.delay)}</i
                          >
                        </td>
                        <td>
                          ${st?.destination_label ||
                          st?.stop_headsign ||
                          pred.headsign}
                        </td>
                      </tr>`;
                    })
                    .join("")}
                  ${_stoptimes
                    .map((st) => {
                      const stAttrs = specialStopTimeAttrs(st, route);
                      specialStopTimes.push(stAttrs);
                      const dom =
                        st.arrival_timestamp || st.departure_timestamp; // mommy?
                      return /* HTML */ `<tr
                        data-direction-${parseInt(st?.trip?.direction_id)}
                      >
                        <td>
                          <span
                            class="${stAttrs.cssClass} ${stAttrs.tooltip &&
                            "tooltip"}"
                            data-tooltip="${stAttrs.tooltip}"
                            >${st.trip?.trip_short_name || st.trip_id}
                          </span>
                          ${BaseRealtimeLayer.trackIconHTML({
                            stop_id: st.stop_id,
                            direction_id: st.trip?.direction_id,
                            route_type: route.route_type,
                          })}
                        </td>
                        <td>
                          <span
                            class="tooltip fa"
                            data-tooltip="Scheduled in ${minuteify(
                              dom - timestamp,
                              ["seconds"]
                            )}"
                            >${BaseRealtimeLayer.icons.clock}</span
                          >
                          ${formatTimestamp(dom, "%I:%M %P")}
                        </td>
                        <td>
                          ${st.destination_label ||
                          st.stop_headsign ||
                          st.trip?.trip_headsign}
                        </td>
                      </tr>`;
                    })
                    .join("")}
                </tbody>
              </table>
            </div>`;
          })
          .join("")}
      </div>
      ${BaseRealtimeLayer.specialStopKeyHTML(specialStopTimes)}
      ${this.#getFooterHTML(properties)}
    </div>`;
  }
}
