/**
 * @file vehicles.js - Plot vehicles on map in realtime, updating every 15 seconds
 * @module vehicles
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime")}
 * @typedef {import("./utils.js")}
 * @typedef {import("./map.js")}
 * @typedef {import("leaflet.markercluster")}
 * @typedef {import("../node_modules/leaflet.markercluster.freezable/dist/leaflet.markercluster.freezable-src.js")}
 * @exports plotVehicles
 */

"use strict";

const DIRECTION_MAPPER = {
  0: "Outbound",
  1: "Inbound",
  0.0: "Outbound",
  1.0: "Inbound",
};

const HEX_TO_CSS = {
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
// const VEHICLES = {};

/**
 * wrapper for @function fillPredictionVehicleData @function fillAlertVehicleData
 * @param {string} trip_id  - stop id
 */
function fillVehicleDataWrapper(trip_id) {
  fillPredictionVehicleData(trip_id);
  fillAlertVehicleData(trip_id);
}

/** Plot vehicles on map in realtime, updating every 15 seconds
 * @param {options} options - options object with the following properties:
 * @param {string} options.url - url to geojson
 * @param {L.layerGroup} options.layer - layer to plot vehicles on
 * @param {object} options.textboxSize - size of textbox
 * @param {boolean} options.isMobile - is the device mobile
 */
// function plotVehicles(url, layer, textboxSize = null) {
function plotVehicles(options) {
  const { url, layer, textboxSize, isMobile } = options;
  const realtime = L.realtime(url, {
    // interval: !["bus", "all_routes"].includes(ROUTE_TYPE) ? 15000 : 45000,
    interval: 15000,
    type: "FeatureCollection",
    container: layer,
    cache: false,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },

    /**
     * @param {*} f
     * @param {L.Layer} l
     */
    onEachFeature(f, l) {
      l.id = f.id;
      l.feature.properties.searchName = `${f.properties.trip_short_name} @ ${f.properties.route?.route_name}`;
      l.bindPopup(getVehicleText(f.properties), textboxSize);
      if (!isMobile) {
        l.bindTooltip(f.id);
      }
      l.setIcon(
        getVehicleIcon(
          f.properties.bearing,
          f.properties.route_color,
          f.properties.display_name
        )
      );
      l.setZIndexOffset(100);
      l.on("click", function () {
        fillVehicleDataWrapper(f.properties.trip_id);
      });
    },
  });

  // realtime.on("enter", function (e) {
  //   setVehicleSideBarSummary(sidebar, e.features);
  // });

  realtime.on("update", function (e) {
    if (!window.mobileCheck() || !inIframe())
      setDefaultVehicleSideBarSummary(e.features);
    Object.keys(e.update).forEach(
      function (id) {
        const layer = this.getLayer(id);

        const feature = e.update[id];
        const wasOpen = layer.getPopup()?.isOpen() || false;

        layer.id = feature.id;
        layer.feature.properties.searchName = `${feature.properties.trip_short_name} @ ${feature.properties.route?.route_name}`;

        // VEHICLES[`${id}`] = layer;
        layer.unbindPopup();
        if (wasOpen) layer.closePopup();
        layer.bindPopup(getVehicleText(feature.properties), textboxSize);
        layer.setIcon(
          getVehicleIcon(
            feature.properties.bearing,
            feature.properties.route_color,
            feature.properties.display_name
          )
        );
        if (wasOpen) {
          layer.openPopup();
          setTimeout(fillVehicleDataWrapper, 200, feature.properties.trip_id);
        }
        layer.on("click", function () {
          setTimeout(fillVehicleDataWrapper, 200, feature.properties.trip_id);
        });
      }.bind(this)
    );
  });

  // setVehicleSideBarSummary(sidebar, e.features);

  return realtime;
}

/**
 * fill prediction data in for `pred-veh-{trip_id}` element
 * this appears as a popup on the map
 * @param {string} trip_id - vehicle id
 * @param {boolean} popup - whether to show the popup
 * @returns {void}
 */
async function fillPredictionVehicleData(trip_id) {
  for (const predEl of document.getElementsByName(`pred-veh-${trip_id}`)) {
    const popupId = `popup-pred-${trip_id}`;
    predEl.onclick = function () {
      togglePopup(popupId);
    };

    const popupText = document.createElement("span");

    popupText.classList.add("popuptext");
    popupText.id = popupId;
    popupText.innerHTML = "...";
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
 *
 */

/**
 *  fill alert prediction data
 * @param {string} trip_id - vehicle id
 */

async function fillAlertVehicleData(trip_id) {
  for (const alertEl of document.getElementsByName(`alert-veh-${trip_id}`)) {
    const popupId = `popup-alert-${trip_id}`;
    alertEl.onclick = function () {
      togglePopup(popupId);
    };

    const popupText = document.createElement("span");

    popupText.classList.add("popuptext");
    popupText.id = popupId;
    popupText.innerHTML = "...";
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
 * return icon div
 * @param {string} bearing - icon to display
 * @param {string} color - color of icon
 * @param {string} displayString - text to display
 * @returns {L.divIcon} - div icon
 */

function getVehicleIcon(bearing, color, displayString = null) {
  const div = document.createElement("div");

  div.classList.add("vehicle_wrapper");

  const img = document.createElement("img");

  img.src = "static/img/icon.png";
  img.loading = "lazy";
  img.alt = "vehicle";
  img.width = 60;
  img.height = 60;
  img.style.cssText = HEX_TO_CSS[color] || "";
  img.style.transform = `rotate(${bearing}deg)`;

  const span = document.createElement("span");
  span.classList.add("vehicle_text");
  span.textContent = displayString;

  div.appendChild(img);
  div.appendChild(span);

  return L.divIcon({
    html: div,
    iconSize: [10, 10],
  });
}

/**
 * gets vehicle text
 * @param {object} properties
 * @returns {HTMLDivElement} - vehicle text
 */
function getVehicleText(properties) {
  const vehicleText = document.createElement("div");
  const formattedTimestamp = formatTimestamp(properties.timestamp, "%I:%M %P");
  const platformName =
    properties.route &&
    properties.route.route_type == "2" &&
    properties.next_stop &&
    properties.next_stop.platform_name
      ? properties.next_stop.platform_name
          .toLowerCase()
          .replace(/ *\([^)]*\) */g, "")
          .replace("commuter rail", "")
          .replace("-", "")
          .trim()
      : "";
  vehicleText.innerHTML = `
  <p>
  <a href="${
    properties.route
      ? properties.route.route_url
      : "https://mbta.com/schedules/" + self.properties.route_id
  }" target="_blank" style="color:#${
    properties.route_color
  }" class="popup_header">${properties.trip_short_name}</a></p>`;
  if (properties.trip_short_name === "552") {
    vehicleText.innerHTML += `<p>heart to hub</p>`;
  } else if (properties.trip_short_name === "549") {
    vehicleText.innerHTML += `<p>hub to heart</p>`;
  } else {
    vehicleText.innerHTML += `<p>${
      DIRECTION_MAPPER[properties.direction_id] || "null"
    } to ${properties.headsign}</p>
    `;
  }
  vehicleText.innerHTML += `<hr>`;
  if (properties.bikes_allowed) {
    vehicleText.innerHTML += `<span class='fa tooltip' data-tooltip='bikes allowed'>&#xf206;</span>&nbsp;&nbsp;&nbsp;`;
  }
  vehicleText.innerHTML += `<span name="pred-veh-${properties.trip_id}" class="fa hidden popup tooltip" data-tooltip="predictions">&#xf239;&nbsp;&nbsp;&nbsp;</span>`;
  vehicleText.innerHTML += `<span name="alert-veh-${properties.trip_id}" class="fa hidden popup tooltip slight-delay" data-tooltip="alerts">&#xf071;&nbsp;&nbsp;&nbsp;</span>`;
  // vehicleText.innerHTML += `</p>`;
  // if (properties.trip_properties.length) {
  //   console.log();
  // }
  // var trip_properties = properties.trip_properties;
  if (properties.stop_time) {
    if (properties.current_status != "STOPPED_AT") {
      const tmsp =
        properties.next_stop?.arrival_time ||
        properties.next_stop?.departure_time;
      const fmttmsp = tmsp ? formatTimestamp(tmsp, "%I:%M %P") : "";
      vehicleText.innerHTML += `<p>${almostTitleCase(
        properties.current_status
      )} ${properties.stop_time.stop_name} - ${fmttmsp}</p>`;
    } else {
      vehicleText.innerHTML += `<p>${almostTitleCase(
        properties.current_status
      )} ${properties.stop_time.stop_name}`;
    }

    if (properties.next_stop && properties.next_stop.delay !== null) {
      const delayMinutes = Math.floor(properties.next_stop.delay / 60);
      const delayClass = getDelayClassName(properties.next_stop.delay);
      if (delayClass !== "on-time") {
        vehicleText.innerHTML += `<i class='${delayClass}'>${delayMinutes} minutes late</i>`;
      } else if (delayMinutes === 0) {
        vehicleText.innerHTML += `<i>on time</i>`;
      } else {
        vehicleText.innerHTML += `<i class='on-time'>${Math.abs(
          delayMinutes
        )} minutes early</i>`;
      }

      // vehicleText.innerHTML += `<p>delay: ${properties.next_stop.delay} minutes</p>`;
    }
  } else if (properties.next_stop) {
    if (properties.current_status != "STOPPED_AT") {
      vehicleText.innerHTML += `<p>${almostTitleCase(
        properties.current_status
      )} ${properties.next_stop.stop_name} - ${formattedTimestamp}</p>`;
    } else {
      vehicleText.innerHTML += `<p>${almostTitleCase(
        properties.current_status
      )} ${properties.next_stop.stop_name}</p>`;
    }
    // if (properties.next_stop.delay === null) {
    //   vehicleText.innerHTML += `<i>not scheduled</i>`;
    // }
  }

  if (properties.occupancy_status != null) {
    vehicleText.innerHTML += `<p><span class="${
      properties.occupancy_percentage >= 80
        ? "severe-delay"
        : properties.occupancy_percentage >= 60
        ? "moderate-delay"
        : properties.occupancy_percentage >= 40
        ? "slight-delay"
        : ""
    }">${properties.occupancy_percentage}% occupancy</span></p>`;
  }

  vehicleText.innerHTML += `<p>${
    properties.speed_mph != null
      ? Math.round(properties.speed_mph)
      : properties.speed_mph
  } mph</p>`;

  vehicleText.innerHTML += `<div class = "popup_footer">
    <p>${properties.vehicle_id} @ ${
    properties.route ? properties.route.route_name : "unknown"
  } ${platformName}</p>
    <p>${formatTimestamp(properties.timestamp)}</p>
    </div>
  `;
  return vehicleText;
}

/**
 *  Set the vehicle sidebar summary
 * @param {L.sidebar} sidebar - sidebar object
 * @param {Object} data - vehicle data
 */

async function setDefaultVehicleSideBarSummary(data) {
  // const key = await (await fetch("key")).json();
  // let content = `<h2 class='color-${key}'>${titleCase(key).toLowerCase()}</h2>`;
  const key = await (await fetch("key")).json();
  const findBox = "<div id='findBox'></div>";
  if (key === "ferry") {
    return setSideBarContent(
      `${findBox}<h2>no vehicle data for ${key}</h2><p style='text-align:center;'>but alerts are still realtime!</p>`,
      "sidebar-default-content"
    );
  }

  let content = findBox;

  // content += "<hr />";
  content += "<table class='sidebar-table sortable'>";
  content +=
    "<thead><th>train</th><th>next stop</th><th>headsign</th><th>delay</th></thead><tbody>";
  Object.values(data)
    // .map((e) => e.properties)
    .forEach(function (d) {
      const headsign =
        d.properties.headsign != "unknown"
          ? d.properties.headsign?.replace("/", " / ") || ""
          : "";
      const trip = d.properties.trip_short_name;
      const delay = d.properties.next_stop?.delay || 0;
      const nextStop =
        d.properties.next_stop?.stop_name?.replace("/", " / ") ||
        d.properties.stop_time?.stop_name?.replace("/", " / ") ||
        "";
      const delayText = getDelayText(delay);
      content += `<tr>
    <td><a style='color:#${
      d.properties.route.route_color
    };cursor:pointer;' onclick="mapsPlaceholder[0].findLayer('${
        d.id
      }', true, 14)">${trip}</a></td>
    <td>${nextStop}</td>
    <td>${headsign}</td>
    <td><i class='${getDelayClassName(delay)}'>${delayText}</i></td>
    </tr>`;
    });
  content += "</tbody></table>";
  setSideBarContent(content, "sidebar-default-content");
}
