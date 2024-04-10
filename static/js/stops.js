/**
 * @file stops.js - Plot stops on map in realtime, updating every hour
 */

const stopIcon = L.icon({
  iconUrl: "static/img/mbta.png",
  iconSize: [12, 12],
});

/** Plot stops on map in realtime, updating every hour
 * @param {string} url - url to geojson
 * @param {L.layerGroup} layer - layer to plot stops on
 * @param {object} textboxSize - size of textbox; default: {
         minWidth: 200,
         maxWidth: 300,
       }
 * @returns {L.realtime} - realtime layer
 */
function plotStops(url, layer, textboxSize = null) {
  textboxSize = textboxSize || {
    minWidth: 200,
    maxWidth: 300,
  };
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
      l.bindTooltip(f.id);
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
  stopHtml.innerHTML = `<h4>${properties.name}</h4>`;
  return stopHtml;
}
