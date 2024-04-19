/** Plot shapes on map in realtime, updating every hour
 * @param {Object} options - options for plotting shapes
 * @param {string} options.url - url to geojson
 * @param {L.layerGroup} options.layer - layer to plot shapes on
 * @param {object} options.textboxSize - size of textbox
 * @returns {L.realtime} - realtime layer
 */
function plotShapes(options) {
  const { url, layer, textboxSize } = options;
  const polyLineRender = L.canvas({ padding: 0.5, tolerance: 10 });
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
      l.setStyle({
        color: `#${f.properties.route_color}`,
        weight: 1.3,
        renderer: polyLineRender,
      });
      l.bindPopup(getShapeText(f.properties), textboxSize);
      l.bindTooltip(f.properties.name);
    },
  });

  realtime.on("update", handleUpdateEvent);
  return realtime;
}

/** get shape text
 * @param {Object} properties - properties of the shape
 * @returns {HTMLElement} - HTML element with shape text
 */
function getShapeText(properties) {
  const shapeHtml = document.createElement("div");
  shapeHtml.innerHTML += `<p>
  <a href="${properties.route_url}" rel="noopener" target="_blank" style="color:#${properties.route_color}" class="popup_header">${properties.route_name}</a>
  </p>`;
  shapeHtml.innerHTML += `<p class="popup_subheader">${properties.route_desc}</p>`;
  shapeHtml.innerHTML += "<hr />";
  shapeHtml.innerHTML += `<p>${properties.route_id} @ <a href="${properties.agency.agency_url}" rel="noopener" target="_blank">${properties.agency.agency_name}</a><p>`;
  shapeHtml.innerHTML += `<p>${properties.agency.agency_phone}</p>`;
  shapeHtml.innerHTML += `<div class="popup_footer"> 
        <p>${formatTimestamp(properties.timestamp)}</p>
    </div>`;
  return shapeHtml;
}
