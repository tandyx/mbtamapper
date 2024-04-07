const stopIcon = L.icon({
  iconUrl: "static/img/mbta.png",
  iconSize: [12, 12],
});

/** Plot stops on map in realtime, updating every hour
 * @param {string} url - url to geojson
 * @param {L.layerGroup} layer - layer to plot stops on
 * @returns {L.realtime} - realtime layer
 */
function plotStops(url, layer) {
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
      l.bindPopup(getStopText(f.properties), { maxWidth: "auto" });
      l.bindTooltip(f.id);
      l.setIcon(stopIcon);
      l.setZIndexOffset(-100);
    },
  });

  realtime.on("update", handleUpdateEvent);
  return realtime;
}

function getStopText(properties) {
  const stopHtml = document.createElement("div");
  stopHtml.innerHTML = `<h4>${properties.name}</h4>`;
  return stopHtml;
}
