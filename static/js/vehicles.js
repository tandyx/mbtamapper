/**
 * @file vehicles.js - Plot vehicles on map in realtime, updating every 15 seconds
 */

// import * as L from "leaflet";
// import * as Plotly from "plotly.js";

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
  "005595":
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
    // interval: !["BUS", "ALL_ROUTES"].includes(ROUTE_TYPE) ? 15000 : 45000,
    interval: 15000,
    type: "FeatureCollection",
    container: layer,
    cache: false,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.bindPopup(getVehicleText(f.properties), textboxSize);
      if (!isMobile) {
        l.bindTooltip(f.properties.trip_short_name || f.id);
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
        fillPredictionVehicleData(f.properties.trip_id);
        fillAlertVehicleData(f.properties.trip_id);
      });
    },
  });

  // realtime.on("enter", function (e) {
  //   setVehicleSideBarSummary(sidebar, e.features);
  // });

  realtime.on("update", function (e) {
    Object.keys(e.update).forEach(
      function (id) {
        const layer = this.getLayer(id);
        const feature = e.update[id];
        const wasOpen = layer.getPopup() ? layer.getPopup().isOpen() : false;
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
          fillPredictionVehicleData(feature.properties.trip_id);
          fillAlertVehicleData(feature.properties.trip_id);
        }
        layer.on("click", function () {
          fillPredictionVehicleData(feature.properties.trip_id);
          fillAlertVehicleData(feature.properties.trip_id);
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
      await fetch(`/api/prediction?trip_id=${trip_id}`)
    ).json();
    if (!_data.length) return;
    predEl.classList.remove("hidden");
    popupText.innerHTML =
      "<table class='data-table'><tr><th>stop</th><th>estimate</th></tr>" +
      _data
        .map(function (d) {
          const realDeparture = d.departure_time || d.arrival_time;
          if (!realDeparture || realDeparture < Date().valueOf()) return "";
          let delayText = d.delay ? `${Math.floor(d.delay / 60)}` : "";
          if (delayText === "0") {
            delayText = "";
          } else if (d.delay > 0) {
            delayText = `+${delayText}`;
          }
          if (delayText) {
            delayText += " min";
          }
          return `<tr>
            <td>${d.stop_name}</td>
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
    }, 500);
  }
}

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
    }, 500);
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
  img.alt = "vehicle";
  img.width = 60;
  img.height = 60;
  img.style.cssText = HEX_TO_CSS[color] || HEX_TO_CSS["ffffff"];
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
  vehicleText.innerHTML = `
  <p>
  <a href="${
    properties.route
      ? properties.route.route_url
      : "https://mbta.com/schedules/" + self.properties.route_id
  }" target="_blank" style="color:#${
    properties.route_color
  }" class="popup_header">${properties.trip_short_name}</a></p><p>${
    DIRECTION_MAPPER[properties.direction_id]
  } to ${properties.headsign}</p>
  `;
  vehicleText.innerHTML += `<hr>`;
  if (properties.bikes_allowed) {
    vehicleText.innerHTML += `<span class='fa tooltip' data-tooltip='bikes allowed'>&#xf206;</span>&nbsp;&nbsp;&nbsp;`;
  }
  vehicleText.innerHTML += `<span name="pred-veh-${properties.trip_id}" class="fa hidden popup tooltip" data-tooltip="predictions">&#xf239;</span>&nbsp;&nbsp;&nbsp;`;
  vehicleText.innerHTML += `<span name="alert-veh-${properties.trip_id}" class="fa hidden popup tooltip slight-delay" data-tooltip="alerts">&#xf071;</span>&nbsp;&nbsp;&nbsp;`;
  // vehicleText.innerHTML += `</p>`;
  if (properties.stop_time) {
    if (properties.current_status != "STOPPED_AT") {
      vehicleText.innerHTML += `<p>${almostTitleCase(
        properties.current_status
      )} ${properties.stop_time.stop_name} - ${formattedTimestamp}</p>`;
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
      )} ${properties.next_stop.stop_name}`;
    }
  }
  if (properties.occupancy_status != null) {
    vehicleText.innerHTML += `<p><span class="${
      properties.occupancy_percentage >= 80
        ? "severe-delay"
        : properties.occupancy_percentage >= 40
        ? "moderate-delay"
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
  }</p>
    <p>${formatTimestamp(properties.timestamp)}</p>
    </div>
  `;
  return vehicleText;
}

/**
 *  Set the vehicle sidebar summary
 * @param {L.sidebar} sidebar - sidebar object
 * @param {object} data - vehicle data
 */

function setVehicleSideBarSummary(sidebar, data) {
  // const sidebar = addSidebar();
  // const sidebar = addSidebar();
  // sidebar.innerHTML = "";
  const summary = document.createElement("div");
  summary.classList.add("inner-sidebar-content");
  summary.id = "summary";
  summary.innerHTML = `
  <h1>Summary</h1>
  <p>There are ${
    Object.keys(data).length
  } vehicles currently on the mapdasdasdasdasudhasjhdkjashdjkashdjkashdksah dkjahsgdsagdsahdgsgakdjksa.</p>
  <div id="piechart"></div>
  `;
  // createDelayPiechart("piechart",
  const delayCounts = Object.values(data)
    .map((properties) => properties.properties.next_stop?.delay)
    .filter((delay) => delay !== null)
    .reduce((counts, delay) => {
      counts[getDelayClassName(delay)] =
        (counts[getDelayClassName(delay)] || 0) + 1;
      return counts;
    }, {});
  if (!document.getElementById("summary_")) {
    setTimeout(() => {
      sidebar.addPanel({
        id: "summary_",
        tab: "<i class='fa>&#xf05a;</i>",
        pane: summary,
      });
    }, 2000);
  }

  // sidebar.addPanel({
  //   id: "ghlink",
  //   tab: '<i class="fa fa-github"></i>',
  //   button: "https://github.com/noerw/leaflet-sidebar-v2",
  // });

  createDelayPiechart("piechart", delayCounts);
}

/**
 * gets the delay class name
 * @param {int} delay - delay in seconds
 * @returns {string} - delay class name
 */

function getDelayClassName(delay) {
  if (delay >= 900) {
    return "severe-delay";
  }
  if (delay >= 600) {
    return "moderate-delay";
  }
  if (delay > 60) {
    return "slight-delay";
  }
  return "on-time";
}

/**
 * creates a pie chart for the delay
 * @param {string} id - The id of the div to put the pie chart in
 * @param {Object} properties - The delay properties
 * @returns {void}
 */
function createDelayPiechart(id, properties) {
  const font = getComputedStyle(document.body).getPropertyValue(
    "--font-family"
  );
  const styleSheet = getStylesheet("index");
  const data = [
    {
      values: Object.values(properties),
      labels: Object.keys(properties).map((label) => titleCase(label, "-")),
      textinfo: "label",
      marker: {
        colors: Object.keys(properties).map((label) => {
          const color = getStyleRuleValue("color", `.${label}`, styleSheet);
          if (color.startsWith("var")) {
            return getComputedStyle(document.body).getPropertyValue(
              color.replace("var(", "").replace(")", "") || "#f2f2f2"
            );
          }
          return color;
        }),
      },
      type: "pie",
      hoverlabel: {
        borderRadius: 10,
        font: { family: font, size: 15 },
      },
      hovertemplate: "%{label}: %{percent} <extra></extra>",
      outsidetextfont: { color: "transparent" },
      responsive: true,
    },
  ];

  const layout = {
    autosize: true,
    showlegend: false,
    font: {
      family: font,
      size: 15,
      color: "#f2f2f2",
    },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: {
      l: 0,
      r: 0,
      b: 0,
      t: 0,
      pad: -30,
    },
    height: 300,
  };

  Plotly.newPlot(id, data, layout, { responsive: true });
}
