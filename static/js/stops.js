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
 * @returns {L.realtime} - realtime layer
 */
function plotStops(options) {
  const { url, layer, textboxSize } = options;
  const realtime = L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.bindPopup(getStopText(f.properties), textboxSize);
      l.bindTooltip(f.properties.stop_name);
      l.setIcon(stopIcon);
      l.setZIndexOffset(-100);
    },
  });

  realtime.on("update", handleUpdateEvent);
  return realtime;
}

/**
 *  Get the stop text for the popup
 * @param {object} properties - properties of the stop
 * @returns {HTMLElement} - HTML element with stop text
 */
function getStopText(properties) {
  const stopHtml = document.createElement("div");
  stopHtml.innerHTML += `<p>
  <a href="${
    properties.stop_url
  }" rel="noopener" target="_blank" style="color:#${
    properties.routes.sort((a, b) => a.route_type - b.route_type)[0].route_color
  }"  class="popup_header">${properties.stop_name}</a>
  </p>`;
  stopHtml.innerHTML += `<p class="popup_subheader">${
    properties.zone_id || "zone-1A"
  }</p>`;
  stopHtml.innerHTML += "<hr /><p>";
  if (properties.wheelchair_boarding === "0") {
    stopHtml.innerHTML += `<p><span class='fa tooltip slight-delay' data-tooltip='wheelchair accessible w/ caveats'>&#xf193;</span>`;
  } else if (properties.wheelchair_boarding === "1") {
    stopHtml.innerHTML += `<p><span class='fa tooltip' data-tooltip='wheelchair accessible'>&#xf193;</span>`;
  }
  stopHtml.innerHTML += "</p>";
  stopHtml.innerHTML += `<p>${properties.routes
    .map(
      (r) =>
        `<a href="${r.route_url}" rel="noopener" target="_blank" style="color:#${r.route_color}">${r.route_name}</a>`
    )
    .join(", ")}</p>`;

  stopHtml.innerHTML += `<div class="popup_footer">
      <p>${properties.stop_address}</p>
      <p>${formatTimestamp(properties.timestamp)}</p>
    </div>`;

  return stopHtml;
}
