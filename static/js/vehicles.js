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
 * @param {string} url - url to geojson
 * @param {L.layerGroup} layer - layer to plot vehicles on
 * @param {object} textboxSize - size of textbox; default: {
          minWidth: 200,
          maxWidth: 300,
        }
 * @returns {L.realtime} - realtime layer
 */
function plotVehicles(url, layer, textboxSize = null) {
  textboxSize = textboxSize || {
    minWidth: 200,
    maxWidth: 300,
  };

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
      l.bindTooltip(f.properties.trip_name || f.id);
      l.setIcon(
        getVehicleIcon(
          f.properties.bearing,
          f.properties.route_color,
          f.properties.display_name
        )
      );
      l.setZIndexOffset(100);
    },
  });

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
        if (wasOpen) layer.openPopup();
      }.bind(this)
    );
  });

  return realtime;
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
  vehicleText.innerHTML += `<hr><p>`;
  if (properties.bikes_allowed) {
    vehicleText.innerHTML += `<span class='fa tooltip' data-tooltip='bikes allowed'>&#xf206;</span>`;
  }
  if (properties.wheelchair_accessible) {
    if (properties.bikes_allowed) {
      vehicleText.innerHTML += `&nbsp;&nbsp;&nbsp;`;
    }
    vehicleText.innerHTML += `<span class='fa tooltip' data-tooltip='wheelchair accessible'>&#xf193;</span>`;
  }
  vehicleText.innerHTML += `</p>`;
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
      const delay_minutes = Math.floor(properties.next_stop.delay / 60);
      if (properties.next_stop.delay >= 900) {
        vehicleText.innerHTML += `<i class='severe-delay'>${delay_minutes} minutes late</i>`;
      } else if (properties.next_stop.delay >= 600) {
        vehicleText.innerHTML += `<i class='moderate-delay'>${delay_minutes} minutes late</i>`;
      } else if (properties.next_stop.delay >= 300) {
        vehicleText.innerHTML += `<i class='slight-delay'>${delay_minutes} minutes late</i>`;
      } else if (delay_minutes === 0) {
        vehicleText.innerHTML += `<i>on time</i>`;
      } else {
        vehicleText.innerHTML += `<i class='on-time'>${Math.abs(
          delay_minutes
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
