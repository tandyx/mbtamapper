/**
 * @file shapes.js - Plot stops on map in realtime, updating every 15 seconds
 * @module shapes
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
  };

  static #worcester_map = {
    515: "hub to heart",
    520: "heart to hub",
  };
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
        <span class="vehicle_text" style="${delayStyle}"
          >${properties.display_name}</span
        >
      </div>
    `;

    return L.divIcon({ html: iconHtml, iconSize: [10, 10] });
  }
  /**
   *
   * @param {LayerApiRealtimeOptions?} options
   */
  constructor(options) {
    options.interval = options.interval || 15000;
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
      cache: false,
      removeMissing: true,
      interactive: options.interactive,
      getFeatureId: (f) => f.id,
      onEachFeature(f, l) {
        l.id = f.id;
        l.feature.properties.searchName = `${f.properties.trip_short_name} @ ${f.properties.route?.route_name}`;
        l.bindPopup(_this.#getPopupHTML(f.properties), options.textboxSize);
        if (!options.isMobile) l.bindTooltip(f.id);
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
        Object.values(_e.features).map((e) => e.properties)
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
              { animate: true }
            );
            layer.openPopup();
            setTimeout(onClick, 200);
          }
          VehicleLayer.onClickArry.forEach((fn) => layer.off("click", fn));
          VehicleLayer.onClickArry.push(onClick);
          layer.on("click", onClick);
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
        `${
          VehicleLayer.#direction_map[parseInt(properties.direction_id)] ||
          "null"
        } to ${properties.headsign}`}
      </div>
      <hr />
    </div>`;
  }

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
    return `<div>${_status} ${stopHTML}</div>`;
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
        ${properties.vehicle_id} @ ${properties?.route?.route_name || "unknown"}
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
      BaseRealtimeLayer.sideBarOtherId
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
      }&include=stop_time&_=${Math.floor(timestamp / 5)}`,
      { cache: "force-cache" },
      super.defaultFetchCacheOpt
    );
    /** @type {AlertProperty[]} */
    const alerts = await fetchCache(
      `/api/alert?trip_id=${properties.trip_id}&_=${Math.floor(
        timestamp / 60
      )}`,
      { cache: "force-cache" },
      super.defaultFetchCacheOpt
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
                (b.departure_time || b.arrival_time)
            )
            ?.filter(
              (p) =>
                p.stop_sequence > properties?.next_stop?.stop_sequence ||
                Infinity
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
                  { starOnly: true }
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
      container.innerHTML = /* HTML */ `
        <h2>${titleCase(this.options.routeType)}</h2>
        <p>No vehicles found</p>
      `;
      return;
    }

    const lastTMSP = properties.reduce((a, b) => {
      return a.timestamp > b.timestamp ? a : b;
    }).timestamp;

    container.innerHTML = /*HTML*/ `
    <h2>${titleCase(this.options.routeType)}</h2>
    <table class='mt-5 sortable data-table'>
      <thead>
        <tr><th>Route</th><th>Trip</th><th>Next</th></tr>
      </thead>
      <tbody class='directional'>
      ${properties
        .sort(
          (a, b) =>
            a.route_id - b.route_id || a.trip_short_name - b.trip_short_name
        )
        .map((prop) => {
          const lStyle = `style="color:#${prop.route.route_color};font-weight:600;"`;
          return /*HTML*/ `<tr data-direction-${parseInt(prop.direction_id)}="">
          <td><a ${lStyle} onclick="LayerFinder.fromGlobals().clickRoute('${
            prop.route_id
          }')">${prop.route.route_name}</a></td>
          <td><a ${lStyle} onclick="LayerFinder.fromGlobals().clickVehicle('${
            prop.vehicle_id
          }')">${prop.trip_short_name}
          </a></td>
          <td><a onclick="LayerFinder.fromGlobals().clickStop('${
            prop.stop_id
          }')"> ${
            prop.next_stop?.stop_name || prop.stop_time?.stop_name
          }</a> <i class='${getDelayClassName(
            prop.next_stop?.delay
          )}'>${getDelayText(prop.next_stop?.delay, false)}</i></td>
        </tr>`;
        })
        .join("")}
      </tbody>
      </table>
      <div class="popup_footer mt-5">
      Last vehicle update @ ${formatTimestamp(lastTMSP, "%I:%M %P")}
        <i data-update-timestamp=${lastTMSP}></i>
      </div>
     
    `;

    for (const el of document.getElementsByClassName("sortable")) {
      sorttable.makeSortable(el);
    }
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
