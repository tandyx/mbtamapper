/** Plot vehicles on map in realtime, updating every 15 seconds
 * @param {string} url - url to geojson
 * @param {L.layerGroup} layer - layer to plot vehicles on
 * @returns {L.realtime} - realtime layer
 */
function plotVehicles(url, layer) {
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
      l.bindPopup(getVehicleText(f.properties), {
        minWidth: 200,
      });
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
        layer.bindPopup(getVehicleText(feature.properties), {
          minWidth: 200,
        });
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
  img.src = "/static/img/icon.png";
  img.alt = "vehicle";
  img.width = 65;
  img.height = 65;
  img.style.cssText = HEX_TO_CSS[color] || HEX_TO_CSS["ffffff"];
  img.style.transform = `rotate(${bearing}deg)`;

  const span = document.createElement("span");
  span.classList.add("vehicle_text");
  span.textContent = displayString;

  div.appendChild(img);
  div.appendChild(span);

  return L.divIcon({
    html: div,
    iconSize: [15, 15],
  });
}

const DIRECTION_MAPPER = {
  0: "Outbound",
  1: "Inbound",
  0.0: "Outbound",
  1.0: "Inbound",
};

/**
 * gets vehicle text
 * @param {object} properties
 * @returns {HTMLDivElement} - vehicle text
 */
function getVehicleText(properties) {
  const vehicleText = document.createElement("div");
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
    vehicleText.innerHTML += `<p>${almostTitleCase(
      properties.current_status
    )} ${properties.stop_time.stop_name} - ${formatTimestamp(
      properties.timestamp,
      "%I:%M %P"
    )}</p>`;
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
    vehicleText.innerHTML += `<p>${almostTitleCase(
      properties.current_status
    )} ${properties.next_stop.stop_name} - ${formatTimestamp(
      properties.timestamp,
      "%I:%M %P"
    )}</p>`;
  }
  if (properties.occupancy_status) {
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

  // const header = document.createElement("div");
  // const headerAnchor = document.createElement("a");
  // headerAnchor.href = properties.route.route_url;
  // headerAnchor.target = "_blank";
  // headerAnchor.classList.add("popup_header");
  // headerAnchor.style.color = `#${properties.route_color}`;
  // headerAnchor.textContent = properties.trip_short_name || properties.trip_id;
  // header.appendChild(headerAnchor);
  // vehicleText.appendChild(header);
  // const subHeader = document.createElement("");

  return vehicleText;

  // vehicleText.innerHTML = "";
  // const occu = properties.occupancy_status;

  // if (properties.bikes_allowed) {
  //   vehicleText.innerHTML += `<p class='tooltip' data-tooltip='bikes allowed'>
  //   <span class='fa'></span>

  //   </p>`;
  // }

  // if (occu != null) {
  //   vehicleText.innerHTML += `<p>Occupancy: <span style="color:${
  //     occu >= 80 ? "red" : occu >= 40 ? "orange" : "var(--text-color)"
  //   }">${properties.occupancy_percentage}%</span><p>`;
  // }
}

// """Returns vehicle as html for a popup."""

// predicted_html = "".join(p.as_html() for p in self.predictions if p.predicted)

// occupancy = (
//     f"""Occupancy: <span style="color:{self.__get_occupancy_color()}">{int(self.occupancy_percentage)}%</span></br>"""
//     if self.occupancy_status
//     else ""
// )

// bikes = (
//     """<div class = "tooltip-mini_image" onmouseover="hoverImage('bikeImg')" onmouseleave="unhoverImage('bikeImg')">"""
//     """<img src ="static/img/bike.png" alt="bike" class="mini_image" id="bikeImg" >"""
//     """<span class="tooltiptext-mini_image" >Bikes allowed.</span></div>"""
//     if self.trip and self.trip.bikes_allowed == 1
//     else ""
// )
// alert = (
//     """<div class = "popup" onclick="openMiniPopup('alertPopup')">"""
//     """<span class = 'tooltip-mini_image' onmouseover="hoverImage('alertImg')" onmouseleave="unhoverImage('alertImg')">"""
//     """<span class = 'tooltiptext-mini_image' >Show Alerts</span>"""
//     """<img src ="static/img/alert.png" alt="alert" class="mini_image" id="alertImg" >"""
//     "</span>"
//     """<span class="popuptext" id="alertPopup">"""
//     """<table class = "table">"""
//     f"""<tr style="background-color:#ff0000;font-weight:bold;">"""
//     """<td>Alert</td><td>Updated</td></tr>"""
//     f"""{"".join(set(a.as_html() for a in self.trip.alerts)) if self.trip else ""}</table>"""
//     """</span></div>"""
//     if self.trip and self.trip.alerts
//     else ""
// )

// prediction = (
//     """<div class = "popup" onclick="openMiniPopup('predictionPopup')">"""
//     """<span class = 'tooltip-mini_image' onmouseover="hoverImage('predictionImg')" onmouseleave="unhoverImage('predictionImg')">"""
//     """<span class = 'tooltiptext-mini_image' >Show Predictions</span>"""
//     """<img src ="static/img/train_icon.png" alt="prediction" class="mini_image" id="predictionImg">"""
//     "</span>"
//     """<span class="popuptext" id="predictionPopup" style="width:1850%;">"""
//     """<table class = "table">"""
//     f"""<tr style="background-color:#{self.route.route_color if self.route else "000000"};font-weight:bold;">"""
//     """<td>Stop</td><td>Platform</td><td>Predicted</td></tr>"""
//     f"""{predicted_html}</table>"""
//     """</span></div>"""
//     if predicted_html
//     else ""
// )

// prd_status = (
//     self.next_stop_prediction.status_as_html()
//     if self.next_stop_prediction
//     else ""
// )

// return (
//     f"""<a href = {self.route.route_url if self.route else ""} target="_blank"  class = 'popup_header' style="color:#{self.route.route_color if self.route else ""};">"""
//     f"""{(self.trip.trip_short_name if self.trip else None) or shorten(self.trip_id)}</a></br>"""
//     """<body style="color:#ffffff;text-align: left;">"""
//     f"""{Vehicle.DIRECTION_MAPPER.get(self.direction_id, "Unknown")} to {self.trip.trip_headsign if self.trip else max(self.predictions, key=lambda x: x.stop_sequence).stop.stop_name if self.predictions else "Unknown"}</body></br>"""
//     # """<hr/>"""
//     """—————————————————————————————————</br>"""
//     f"""{alert} {prediction} {bikes} {"</br>" if any([alert, prediction, bikes]) else ""}"""
//     f"{self.return_current_status()}"
//     f"""{("Delay: " if prd_status else "") + prd_status}{"</br>" if prd_status else ""}"""
//     f"""{occupancy}"""
//     f"""Speed: {int(self.speed or 0) if self.speed is not None or self.current_status == "1" or self.route.route_type in ["0", "2"] else "Unknown"} mph</br>"""
//     # f"""Bearing: {self.bearing}°</br>"""
//     f"""<span class = "popup_footer">"""
//     f"""Vehicle: {self.vehicle_id}</br>"""
//     f"""Route: {f'({self.route.route_short_name}) ' if self.route and self.route.route_type == "3" else ""}{self.route.route_long_name if self.route else self.route_id}</br>"""
//     f"""Timestamp: {self.updated_at_datetime.strftime("%m/%d/%Y %I:%M %p")}</br></span>"""
// )
