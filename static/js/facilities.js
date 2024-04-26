/** Plot facilities on map in realtime, updating every hour
 * @param {string} options.url - url to geojson
 * @param {L.layerGroup} options.layer - layer to plot facilities on
 * @param {object} options.textboxSize - size of textbox;
 * @param {boolean} options.isMobile - is the device mobile
 * @returns {L.realtime} - realtime layer
 */
function plotFacilities(options) {
  const { url, layer, textboxSize, isMobile } = options;
  const facilityIcon = L.icon({
    iconUrl: "static/img/parking.png",
    iconSize: [15, 15],
  });

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
      l.bindPopup(getFacilityText(f.properties), textboxSize);
      if (!isMobile) {
        l.bindTooltip(f.properties.facility_long_name);
      }
      l.setIcon(facilityIcon);
      l.setZIndexOffset(-150);
    },
  });
  realtime.on("update", handleUpdateEvent);
  return realtime;
}

/**
 * get facility text
 * @param {Object} properties - properties of the facility
 * @returns {HTMLElement} - HTML element with facility text
 */
function getFacilityText(properties) {
  const facilityHtml = document.createElement("div");
  const capac_acc = properties["capacity-accessible"];
  facilityHtml.innerHTML += `<p>
  <a href="${properties["contact-url"]}" rel="noopener" target="_blank" class="facility_header popup_header">${properties.facility_long_name}</a>
  </p>`;
  facilityHtml.innerHTML += `<p class="popup_subheader"><a href="${properties["contact-url"]}" rel="noopener" target="_blank">${properties.operator}</a></p>`;
  facilityHtml.innerHTML += "<hr /><p>";
  facilityHtml.innerHTML += `<span class='fa tooltip' data-tooltip='${properties.capacity} spots'>&#xf1b9;</span>&nbsp;&nbsp;&nbsp;`;
  if (capac_acc !== "0" && capac_acc) {
    facilityHtml.innerHTML += `<span class='fa tooltip' data-tooltip='${capac_acc} spots'>&#xf193;</span>`;
  }
  facilityHtml.innerHTML += "</p>";
  facilityHtml.innerHTML += `<p>${properties["fee-daily"]}</p>`;
  //   facilityHtml.innerHTML += `<p>${properties["fee-monthly"]}</p>`;
  facilityHtml.innerHTML += `<p><a href="${properties["payment-app-url"]}">${properties["payment-app"]} ${properties["payment-app-id"]}</a></p>`;
  facilityHtml.innerHTML += `<div class="popup_footer">
    <p>${properties.facility_id} @ ${properties.contact}</p>
    <p>${properties["contact-phone"]}</p>
    <p>${formatTimestamp(properties.timestamp)}</p>
  </div>`;
  return facilityHtml;
}
