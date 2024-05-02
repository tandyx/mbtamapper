/**
 * @file stops.js - Plot stops on map in realtime, updating every hour
 */

const stopIcon = L.icon({
  iconUrl: "static/img/mbta.png",
  iconSize: [12, 12],
});

/** Plot stops on map in realtime, updating every hour
 * @param {Object} options - options for plotting stops
 * @param {string} options.url - url to geojson
 * @param {L.layerGroup} options.layer - layer to plot stops on
 * @param {object} options.textboxSize
 * @param {boolean} options.isMobile - is the device mobile
 * @returns {L.realtime} - realtime layer
 */
function plotStops(options) {
  const { url, layer, textboxSize, isMobile } = options;
  const realtime = L.realtime(url, {
    interval: 120000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.bindPopup(getStopText(f.properties), textboxSize);
      if (!isMobile) {
        l.bindTooltip(f.properties.stop_name);
      }
      l.setIcon(stopIcon);
      l.setZIndexOffset(-100);
      l.on("click", function () {
        fillAlertStopData(f.properties.stop_id);
        fillPredictionsStopData(f.properties.stop_id, f.properties.child_stops);
      });
    },
  });
  realtime.on("update", handleUpdateEvent);

  realtime.on("update", function (e) {
    Object.keys(e.update).forEach(
      function (id) {
        const layer = this.getLayer(id);
        const feature = e.update[id];
        const wasOpen = layer.getPopup() ? layer.getPopup().isOpen() : false;
        layer.unbindPopup();
        if (wasOpen) layer.closePopup();
        layer.bindPopup(getStopText(feature.properties), textboxSize);
        if (wasOpen) {
          layer.openPopup();
          fillAlertStopData(feature.properties.stop_id);
          fillPredictionsStopData(
            feature.properties.stop_id,
            feature.properties.child_stops
          );
        }
        layer.on("click", function () {
          fillAlertStopData(feature.properties.stop_id);
          fillPredictionsStopData(
            feature.properties.stop_id,
            feature.properties.child_stops
          );
        });
      }.bind(this)
    );
  });

  return realtime;
}

/**
 *  Get the stop text for the popup
 * @param {object} properties - properties of the stop
 * @returns {HTMLElement} - HTML element with stop text
 */
function getStopText(properties) {
  const stopHtml = document.createElement("div");
  const primaryRoute = properties.routes.sort(
    (a, b) => a.route_type - b.route_type
  )[0];
  stopHtml.innerHTML += `<p>
  <a href="${
    properties.stop_url
  }" rel="noopener" target="_blank" style="color:#${
    primaryRoute ? primaryRoute.route_color : "var(--text-color)"
  }"  class="popup_header">${properties.stop_name.replace("/", " / ")}</a>
  </p>`;
  stopHtml.innerHTML += `<p class="popup_subheader">${
    properties.zone_id || "zone-1A"
  }</p>`;
  stopHtml.innerHTML += "<hr />";
  if (properties.wheelchair_boarding == "0") {
    stopHtml.innerHTML += `<span class='fa tooltip slight-delay' data-tooltip='wheelchair accessible w/ caveats'>&#xf193;</span>&nbsp;&nbsp;&nbsp;`;
  } else if (properties.wheelchair_boarding == "1") {
    stopHtml.innerHTML += `<span class='fa tooltip' data-tooltip='wheelchair accessible'>&#xf193;</span>&nbsp;&nbsp;&nbsp;`;
  }
  stopHtml.innerHTML += `<span name="predictions-stop-${properties.stop_id}" class="fa hidden popup tooltip" data-tooltip="predictions">&#xf239;&nbsp;&nbsp;&nbsp;</span>`;
  stopHtml.innerHTML += `<span name="alert-stop-${properties.stop_id}" class="fa hidden popup tooltip slight-delay" data-tooltip="alerts">&#xf071;</span>`;

  stopHtml.innerHTML += `<p>${properties.routes
    .map(
      (r) =>
        `<a href="${r.route_url}" rel="noopener" target="_blank" style="color:#${r.route_color}">${r.route_name},</a>`
    )
    .join(" ")}</p>`;

  stopHtml.innerHTML += `<div class="popup_footer">
      <p>${properties.stop_id} @ ${properties.stop_address}</p>
      <p>${formatTimestamp(properties.timestamp)}</p>
    </div>`;

  return stopHtml;
}

/**
 * fill alert stop data
 * @param {string} stop_id
 * @returns {void}
 */
async function fillAlertStopData(stop_id) {
  for (const alertEl of document.getElementsByName(`alert-stop-${stop_id}`)) {
    const popupId = `popup-alert-${stop_id}`;
    // const oldTooltip = alertEl.getAttribute("data-tooltip");
    alertEl.onclick = function () {
      togglePopup(popupId);
    };
    const popupText = document.createElement("span");
    popupText.classList.add("popuptext");
    popupText.style.minWidth = "350px";
    popupText.id = popupId;
    // alertEl.setAttribute("data-tooltip", "loading...");
    const _data = await (
      await fetch(`/api/stop?stop_id=${stop_id}&include=alerts`)
    ).json();
    if (!_data || !_data.length || !_data[0].alerts.length) return;
    alertEl.classList.remove("hidden");
    // alertEl.setAttribute("data-tooltip", oldTooltip);
    popupText.innerHTML =
      "<table class='data-table'><tr><th>alert</th><th>timestamp</th></tr>" +
      _data[0].alerts
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
    }, 500);
  }
}

/**
 * fill stop predictions data
 * @param {string} stop_id - stop id
 * @param {Object[]} child_stops - child stops
 * @returns {void}
 */
async function fillPredictionsStopData(stop_id, child_stops) {
  for (const alertEl of document.getElementsByName(
    `predictions-stop-${stop_id}`
  )) {
    const popupId = `popup-predictions-${stop_id}`;
    const currTime = new Date().getTime() / 1000;
    alertEl.onclick = function () {
      togglePopup(popupId);
    };
    const popupText = document.createElement("span");
    popupText.classList.add("popuptext");
    popupText.id = popupId;
    popupText.innerHTML = "...";
    const _data = [];
    for (const child of child_stops.filter((s) => s.location_type == 0)) {
      _data.push(
        ...(await (
          await fetch(
            `/api/prediction?stop_id=${child.stop_id}&departure_time>${currTime}&include=route,stop_time,trip`
          )
        ).json())
      );
    }
    // const currTimeThres = new Date().getTime() / 10000 - 15 * 60;
    // const stopTimeData = [];
    // for (const child of child_stops.filter((s) => s.location_type == 0)) {
    //   stopTimeData.push(
    //     ...(await (
    //       await fetch(
    //         `/api/stoptime?stop_id=${child.stop_id}&departure_timestamp>${currTimeThres}&include=route`
    //       )
    //     ).json())
    //   );
    // }

    if (!_data.length) return;
    alertEl.classList.remove("hidden");
    popupText.innerHTML =
      "<table class='data-table' style='min-width:400px'><tr><th>route</th><th>trip</th><th>dest</th><th>est</th></tr>" +
      _data
        .sort(
          (a, b) =>
            (a.departure_time || a.arrival_time) -
            (b.departure_time || b.arrival_time)
        )
        .map(function (d) {
          const realDeparture = d.departure_time || d.arrival_time;
          let delayText = d.delay ? `${Math.floor(d.delay / 60)}` : "";
          if (delayText === "0") {
            delayText = "";
          } else if (d.delay > 0) {
            delayText = `+${delayText}`;
          }
          if (delayText) {
            delayText += " min";
          }
          // const realTime = d.departure_time || d.arrival_time;
          return `<tr>
          <td style='color:#${d.route.route_color}'>${d.route.route_name}</td>
          <td>${d.trip ? d.trip.trip_short_name || d.trip_id : d.trip_id}</td>
          <td>${d.headsign}</td>
          <td>
            ${formatTimestamp(realDeparture, "%I:%M %P")}
            <i class='${getDelayClassName(d.delay)}'>${delayText}</i>
          </td>
        </tr>
        `;
        })
        .join("") +
      // _data
      //   .map(function (d) {
      //     return `<tr>
      //     <td>${d.route_id}</td>
      //     <td>${d.direction_id}</td>
      //     <td>${formatTimestamp(d.timestamp)}</td>
      //   </tr>
      //   `;
      //   })
      //   .join("") +
      "</table>";
    alertEl.appendChild(popupText);
    setTimeout(() => {
      if (openPopups.includes(popupId)) togglePopup(popupId, true);
    }, 500);
  }
}
