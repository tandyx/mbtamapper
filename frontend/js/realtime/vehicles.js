/**
 * @file shapes.js - Plot stops on map in realtime, updating every 15 seconds
 * @module vehicles
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("../utils.js")}
 * @import { * } from "sorttable/sorttable.js"
 * @import { LayerProperty, LayerApiRealtimeOptions, VehicleProperty, PredictionProperty, AlertProperty, VehicleProperty, RealtimeLayerOnClickOptions, NextStop } from "../types/index.js"
 * @import { Layer, Realtime } from "leaflet";
 * @import { BaseRealtimeLayer } from "./base.js"
 * @exports VehicleLayer
 */

"use strict";

/**
 * encapsulating class to plot Vehicles on a leaflet map
 * after object creation, you can call `.plot` to plot it
 */
class VehicleLayer extends BaseRealtimeLayer {
  /**@type {((event: L.LeafletMouseEvent) => void)[]} */
  static onClickArry = [];

  /**
   * string or html element of vehicle
   * @param {VehicleProperty} properties from geojson
   * @returns {L.DivIcon}
   */
  #getIcon(properties) {
    const delayClassName = getDelayClassName(properties?.next_stop?.delay || 0);
    const delayStyle =
      (properties?.next_stop?.delay || 0) < 5 * 60
        ? ""
        : `text-decoration: underline 2px var(--vehicle-${delayClassName});
        -webkit-text-decoration-line: underline;
        -webkit-text-decoration-color: var(--vehicle-${delayClassName});
        -webkit-text-decoration-thickness: 2px;
        text-decoration-thickness: 2px;
      `;

    const fillColor = mixHexColors(properties.route_color, "#e6e6e6");
    const textColor =
      getContrastYIQ(fillColor, 85) === "dark" ? "#121212" : "#f2f2f2";

    const iconHtml = /* HTML */ `
      <?xml version="1.0" encoding="UTF-8" standalone="no"?>
      <svg
        width="30"
        height="40"
        viewBox="0 0 60 80"
        version="1.1"
        id="svg1"
        xmlns="http://www.w3.org/2000/svg"
        class="vehicle_wrapper"
        style="transform: translate(-50%, -50%) rotate(${properties.bearing}deg);"
      >
        <g id="layer1">
          <g id="g1" transform="matrix(1,0,0,0.98572755,-74.932602,-77.714414)">
            <circle
              style="fill:#${properties.route_color};fill-opacity:1;stroke-width:0.219878"
              id="path1"
              cx="105"
              cy="130"
              r="30"
            />
            <path
              style="fill:#${properties.route_color};fill-opacity:1;stroke-width:0.264583"
              id="path3"
              d="m 76.977614,114.21636 c -1.586634,2.808 -28.955165,2.12783 -32.18028,2.15777 -3.225115,0.0299 -30.576306,1.21799 -32.214788,-1.56008 C 10.944065,112.03599 25.217367,88.674224 26.804,85.866225 28.390634,83.058227 41.037345,58.777374 44.262461,58.74744 c 3.225115,-0.02993 16.320344,24.011989 17.958825,26.790053 1.638482,2.778064 16.342961,25.870867 14.756328,28.678867 z"
              transform="matrix(0.80648273,0,0,0.73594934,68.78865,35.606553)"
            />
            <circle
              style="fill:${fillColor};stroke-width:0.19056"
              id="path1-3"
              cx="104.9079"
              cy="130.83835"
              r="26"
            />
            <text
              x="104.9079"
              y="130.83835"
              dominant-baseline="middle"
              text-anchor="middle"
              class="vehicle_text"
              style="color:${textColor};fill:${textColor};border-bottom:2px var(--vehicle-${delayClassName});"
              transform="rotate(${-properties.bearing}, 104.9079, 130.83835)"
            >
              ${properties.display_name}
            </text>
            ${(properties?.next_stop?.delay || 0) >= 5 * 60
              ? /*XML*/ `<line
         x1="90" x2="120"
         y1="142" y2="142"
         stroke="var(--vehicle-${delayClassName})"
         stroke-width="4"
         transform="rotate(${-properties.bearing}, 104.9079, 130.83835)"
       />`
              : ""}
          </g>
        </g>
      </svg>
    `;

    // <span class="vehicle_text" style="${delayStyle}"
    //   >${properties.display_name}</span
    // >

    return L.divIcon({ html: iconHtml, iconSize: [10, 10] });
  }
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  constructor(options) {
    options.interval = options.interval || 12500;
    super(options);
  }

  /**
   * @param {LayerApiRealtimeOptions?} options
   */
  plot(options) {
    const _this = this;
    options = { ..._this.options, ...options };
    /**@type {BaseRealtimeOnClickOptions<VehicleProperty>} */
    const onClickOpts = { _this, idField: "vehicle_id" };
    const realtime = L.realtime(options.url, {
      interval: options.interval,
      type: "FeatureCollection",
      container: options.layer,
      cache: true,
      removeMissing: true,
      interactive: options.interactive,
      getFeatureId: (f) => f.id,
      /**@type {(f: GeoJSON.Feature<GeoJSON.Geometry, VehicleProperty>, l: L.Layer) => void} */
      onEachFeature(f, l) {
        l.id = f.id;
        l.feature.properties.searchName = `${f.properties.trip_short_name} @ ${f.properties.route?.route_name}`;
        l.bindPopup(_this.#getPopupHTML(f.properties), options.textboxSize);
        if (!options.isMobile) l.bindTooltip(f.properties.label || f.id);
        l.setIcon(_this.#getIcon(f.properties));
        l.setZIndexOffset(100);
        /** @type {(event: L.LeafletMouseEvent) => void} */
        const onClick = (_e) => {
          _this.#_onclick(_e, { ...onClickOpts, properties: f.properties });
        };
        VehicleLayer.onClickArry.forEach((fn) => l.off("click", fn));
        VehicleLayer.onClickArry.push(onClick);
        l.on("click", onClick);
      },
    });

    realtime.on("update", function (_e) {
      _this.#fillDefaultSidebar(
        Object.values(_e.features).map((e) => e.properties),
      );
      Object.keys(_e.update).forEach(
        function (id) {
          /**@type {Layer} */
          const layer = this.getLayer(id);
          /**@type {GeoJSON.Feature<GeoJSON.Geometry, VehicleProperty} */
          const feature = _e.update[id];
          const wasOpen = layer.getPopup()?.isOpen() || false;
          const properties = feature.properties;
          layer.id = feature.id;
          layer.feature.properties.searchName = `${properties.trip_short_name} @ ${properties.route?.route_name}`;
          layer.unbindPopup();
          /** @type {(event: L.LeafletMouseEvent) => void } */
          const onClick = () =>
            _this.#_onclick(_e, { ...onClickOpts, properties: properties });
          if (wasOpen) layer.closePopup();
          layer.bindPopup(_this.#getPopupHTML(properties), options.textboxSize);
          layer.setIcon(_this.#getIcon(properties));
          if (wasOpen) {
            _this.options.map.setView(
              layer.getLatLng(),
              _this.options.map.getZoom(),
              { animate: true },
            );
            layer.openPopup();
            setTimeout(onClick, 200);
          }
          VehicleLayer.onClickArry.forEach((fn) => layer.off("click", fn));
          VehicleLayer.onClickArry.push(onClick);
          layer.on("click", onClick);
        }.bind(this),
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
      <div>${this.#customHeadsign(properties)}</div>
      <div style="color: var(--lighter-dark-background)">
        ${properties.trip_note || ""}
      </div>
      <hr />
    </div>`;
  }

  /**
   * generates vehicle description
   * @param {VehicleProperty} properties
   */
  #customHeadsign(properties) {
    if (
      properties.route.route_fare_class === "Special" &&
      properties.headsign
    ) {
      return properties.headsign;
    }

    const direction_map = { 0: "Outbound", 1: "Inbound" };
    const description = `${
      direction_map[parseInt(properties.direction_id)] || "unknown"
    } to ${properties.headsign || "unknown"}`;

    const customDescriptions = {
      621: "🦊",
      926: "🦊",
      666: "😈",
      6666: "😈",
      888: "♠️",
      67: "🫩",
      69: "💀",
      1738: "(feat. Remy Boyz)",
      679: "(feat. Remy Boyz)",
      420: "🌲",
      21: "🤓",
      standalones: {
        515: "Hub to Heart",
        520: "Heart to Hub",
      },
      /**
       * @template {keyof typeof this | keyof typeof this["standalones"]} T
       * @param {T} trip_name key of this obj
       * @param {string} [prepend=""] prepend this to item
       * @param {...*} args passed to sub functions
       * @returns {(keyof typeof this | keyof typeof this["standalones"])[T] | ""}
       */
      formulate(trip_name, prepend = "", ...args) {
        const item = this[trip_name];
        if ([null, undefined].includes(item)) {
          return this.standalones[trip_name] || "";
        }
        if (typeof item === "function") {
          return item(...args);
        }
        return prepend + item;
      },
    };

    return (
      customDescriptions.formulate(
        properties.trip_short_name,
        description + " ",
      ) || description
    );
  }

  // static #direction_map = {
  //   0: "Outbound",
  //   1: "Inbound",
  // };

  // static #worcester_map = {
  //   515: "Hub to Heart",
  //   520: "Heart to Hub",
  // };

  /**
   * @param {VehicleProperty} properties
   */
  #getStatusHTML(properties) {
    const dominant =
      properties.next_stop?.arrival_time ||
      properties.next_stop?.departure_time;
    const _status = almostTitleCase(properties.current_status);
    const tmstmp =
      properties.current_status !== "STOPPED_AT" && dominant
        ? formatTimestamp(dominant, "%I:%M %P")
        : "";

    const stopHTML = `<a style="cursor: pointer;" onclick="LayerFinder.fromGlobals().clickStop('${
      properties.stop_id
    }')">${
      properties.stop_time
        ? properties.stop_time.stop_name
        : properties?.next_stop?.stop_name
    }</a>`;

    // for scheduled stops
    if (properties.stop_time) {
      if (tmstmp) return `<div>${_status} ${stopHTML} - ${tmstmp}</div>`;
      return `<div>${_status} ${stopHTML}</div>`;
    }

    if (!properties.next_stop) return "";
    // for added stops
    if (tmstmp) return `<div>${_status} ${stopHTML} - ${tmstmp}</div>`;
    return /* HTML */ `<div>${_status} ${stopHTML}</div>`;
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
    const _abs = Math.abs(delay);
    return /* HTML */ ` <i class="${dClassName}">
      ${_abs} minute${(_abs > 1 && "s") || ""}
      ${dClassName === "on-time" ? "early" : "late"}</i
    >`;
  }

  /**
   * @param {VehicleProperty} properties
   */
  #getOccupancyHTML(properties) {
    if ([null, undefined].includes(properties.occupancy_status)) return "";
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
   * bike icon html
   * @param {VehicleProperty} properties
   */
  #getBikeHTML(properties) {
    if (!properties.bikes_allowed) return "";
    return /* HTML */ `<span class="fa tooltip" data-tooltip="Bikes Allowed"
      >${BaseRealtimeLayer.iconSpacing("bike")}</span
    >`;
  }
  /**
   * speed text
   * @param {VehicleProperty} properties
   */
  #getSpeedText(properties) {
    if (properties.speed_mph === undefined || properties.speed_mph === null) {
      return "unknown mph";
    }
    return `${Math.round(properties.speed_mph)} mph`;
  }
  /**
   *
   * @param {VehicleProperty} properties
   */
  #getFooterHTML(properties) {
    return /* HTML */ ` <div class="popup_footer">
      <div>
        ${properties.label || properties.vehicle_id} @
        ${properties?.route?.route_name || "unknown"}
        ${properties.next_stop?.platform_code
          ? `track ${properties.next_stop.platform_code}`
          : ""}
      </div>
      <div>
        ${formatTimestamp(properties.timestamp, "%I:%M %P")}
        <i data-update-timestamp=${properties.timestamp}></i>
      </div>
    </div>`;
  }

  /**
   * returns the vehicle popup html
   * @param {VehicleProperty} properties
   * @returns {HTMLDivElement} vehicle text
   */
  #getPopupHTML(properties) {
    const vehicleText = document.createElement("div");
    vehicleText.innerHTML = /* HTML */ `<div>
      ${this.#getHeaderHTML(properties)}
      <div style="margin-bottom: 3px;">
        ${this.#getBikeHTML(properties)}
        ${super.moreInfoButton(properties.vehicle_id)}
      </div>
      ${this.#getStatusHTML(properties)}
      <div>${this.#getDelayHTML(properties)}</div>
      ${this.#getOccupancyHTML(properties)}
      <div>${this.#getSpeedText(properties)}</div>
      ${this.#getFooterHTML(properties)}
    </div>`;

    return vehicleText;
  }

  /**
   * fills the vehicle-specific sidebar
   *
   * @param {VehicleProperty} properties
   */
  async #fillSidebar(properties) {
    const container = BaseRealtimeLayer.toggleSidebarDisplay(
      BaseRealtimeLayer.sideBarOtherId,
    );
    const sidebar = document.getElementById("sidebar");
    const timestamp = Math.round(new Date().valueOf() / 1000);
    if (!container || !sidebar) return;
    super.moreInfoButton(properties.vehicle_id, { loading: true });
    sidebar.style.display = "flex";
    container.innerHTML = /* HTML */ `<div class="centered-parent">
      <div class="loader-large"></div>
    </div>`;
    /** @type {PredictionProperty[]} */
    const predictions = await fetchCache(
      `/api/prediction?trip_id=${
        properties.trip_id
      }&include=stop_time&_=${Math.floor(timestamp / 5)}&cache=4`,
      { cache: "force-cache" },
      super.defaultFetchCacheOpt,
    );
    /** @type {AlertProperty[]} */
    const alerts = await fetchCache(
      `/api/alert?trip_id=${properties.trip_id}&_=${Math.floor(
        timestamp / 60,
      )}&cache=40`,
      { cache: "force-cache" },
      super.defaultFetchCacheOpt,
    );
    if (
      !properties.next_stop ||
      !Object.keys(properties.next_stop).length ||
      properties.next_stop?.delay === null
    ) {
      console.warn("no next stop found for vehicle", properties);
      properties.next_stop = predictions?.[0] || {};
    }
    super.moreInfoButton(properties.vehicle_id, {
      alert: Boolean(alerts.length),
    });
    /**@type {StopTimeAttrObj[]} */
    const specialStopTimes = [];

    sidebar.style.display = "initial";
    container.innerHTML = /*HTML*/ `<div>
        ${this.#getHeaderHTML(properties)}
        ${super.getAlertsHTML(alerts)}
        ${this.#getBikeHTML(properties)}
        ${this.#getStatusHTML(properties)}
        <div>${this.#getDelayHTML(properties)}</div>
        <div>${this.#getSpeedText(properties)}</div>
        ${this.#getOccupancyHTML(properties)}
        <div class="my-5">
          <table class='data-table'>
          <thead>
            ${super.tableHeaderHTML(properties.route, { onclick: false })}
            <tr><th>Stop</th><th>Estimate</th></tr>
          </thead>
          <tbody>
          ${predictions
            ?.sort(
              (a, b) =>
                (a.departure_time || a.arrival_time) -
                (b.departure_time || b.arrival_time),
            )
            ?.filter(
              (p) =>
                p.stop_sequence > properties?.next_stop?.stop_sequence ||
                Infinity,
            )
            ?.map((p) => {
              const realDeparture = p.departure_time || p.arrival_time;
              if (!realDeparture || realDeparture < Date().valueOf()) return "";
              const delayText = getDelayText(p.delay);

              const stAttrs = specialStopTimeAttrs(p.stop_time);
              /** @type {StopTimeAttrObj} we don't really *need* to do this, but it makes the implementation of the html key wicked easy */
              const trackIcon = {
                cssClass: "",
                htmlLogo: BaseRealtimeLayer.trackIconHTML(
                  {
                    stop_id: p.stop_id,
                    direction_id: p.direction_id,
                    route_type: properties?.route?.route_type,
                  },
                  { starOnly: true },
                ),
                tooltip: "",
              };

              //
              [stAttrs, trackIcon]
                .filter((attr) => Object.values(attr).filter(Boolean).length)
                .forEach((attr) => specialStopTimes.push(attr));

              const _onclick = !this.options.isMobile
                ? `LayerFinder.fromGlobals().clickStop('${p.stop_id}')`
                : "";

              return /* HTML */ `<tr>
                <td class="">
                  <a
                    class="${stAttrs.cssClass} ${(stAttrs.tooltip &&
                      "tooltip") ||
                    ""}"
                    onclick="${_onclick}"
                    data-tooltip="${stAttrs.tooltip}"
                    >${p.stop_name} ${stAttrs.htmlLogo}</a
                  >
                  ${trackIcon.htmlLogo}
                </td>
                <td>
                  ${formatTimestamp(realDeparture, "%I:%M %P")}
                  <i class="${getDelayClassName(p.delay)}">${delayText}</i>
                </td>
              </tr> `;
            })
            .join("")}
            </tbody>
          </table>
        </div>
      ${BaseRealtimeLayer.specialStopKeyHTML(specialStopTimes)}
      ${this.#getFooterHTML(properties)}
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
      container.innerHTML = /* HTML */ ` <p>No vehicles found</p> `;
      return;
    }

    const lastTMSP = properties.reduce((a, b) => {
      return a.timestamp > b.timestamp ? a : b;
    }).timestamp;

    /** @type {DelayObject}*/
    const delays = properties
      .map((a) => a.next_stop?.delay)
      .reduce((acc, curr) => {
        const dclass = getDelayClassName(curr);
        if (!acc[dclass]) acc[dclass] = 0;
        acc[dclass]++;
        return acc;
      }, {});

    const delayDesc = {
      "on-time": "On time / unscheduled",
      "slight-delay": "> 1 minute late",
      "moderate-delay": "> 5 minutes late",
      "severe-delay": "> 15 minutes late",
    };
    container.innerHTML = /* HTML */ `
      <div>
        <div class="train-status-bar">
          ${Object.entries(delayDesc)
            .map(([key, desc]) => {
              // const desc = delayDesc[key] || "Unknown";
              const value = delays[key] || 0;
              return `<div
                style="width: ${Math.round(
                  (value / properties.length) * 100,
                )}%;"
                class="item tooltip ${key}-bg"
                data-tooltip="(${value}) ${desc}"
              >

              </div>`;
            })
            .join("")}
        </div>
          <table class="sortable data-table">
            <thead>
              <tr>
                <th>Route</th>
                <th>Trip</th>
                <th>Next Stop</th>
              </tr>
            </thead>
            <tbody class="directional">
              ${properties
                .sort(
                  (a, b) =>
                    (a.route_id > b.route_id
                      ? 1
                      : b.route_id > a.route_id
                        ? -1
                        : 0) ||
                    (a.trip_short_name > b.trip_short_name
                      ? 1
                      : b.trip_short_name > a.trip_short_name
                        ? -1
                        : 0),
                )
                .map((prop) => {
                  const lStyle = `style="color:#${prop.route.route_color};font-weight:600;"`;
                  return /* HTML */ `<tr
                    data-direction-${parseInt(prop.direction_id)}=""
                  >
                    <td>
                      <a
                        ${lStyle}
                        onclick="LayerFinder.fromGlobals().clickRoute('${prop.route_id}')"
                        >${prop.route.route_name}</a
                      >
                    </td>
                    <td>
                      <a
                        ${lStyle}
                        onclick="LayerFinder.fromGlobals().clickVehicle('${prop.vehicle_id}')"
                        >${prop.trip_short_name}
                      </a>
                    </td>
                    <td>
                      <a
                        onclick="LayerFinder.fromGlobals().clickStop('${prop.stop_id}')"
                      >
                        ${prop.next_stop?.stop_name ||
                        prop.stop_time?.stop_name}</a
                      >
                      <i class="${getDelayClassName(prop.next_stop?.delay)}"
                        >${getDelayText(prop.next_stop?.delay, false)}</i
                      >
                    </td>
                  </tr>`;
                })
                .join("")}
            </tbody>
          </table>
          <div class="popup_footer mt-5">
            Last vehicle update @ ${formatTimestamp(lastTMSP, "%I:%M %P")}
            <i data-update-timestamp=${lastTMSP}></i>
          </div>
        </div>
      </div>
    `;

    for (const el of document.getElementsByClassName("sortable")) {
      sorttable.makeSortable(el);
    }

    return container;
  }

  /**
   * to be called `onclick`
   *
   * supercedes public super method
   *
   * @param {DomEvent.PropagableEvent} event
   * @param {RealtimeLayerOnClickOptions<VehicleProperty>} options
   */
  async #_onclick(event, options = {}) {
    super._onclick(event, options);
    /**@type {this} */
    const _this = options._this || this;
    await _this.#fillSidebar(options.properties);
    super._afterClick(event, options);
  }
}
