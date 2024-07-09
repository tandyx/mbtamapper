/**
 * @file shapes.js - Plot stops on map in realtime, updating every hour
 * @module shapes
 * @typedef {import("leaflet")}
 * @typedef {import("leaflet-realtime-types")}
 * @typedef {import("./utils.js")}
 * @import { Realtime } from "leaflet";
 * @exports plotShapes
 */

"use strict";

/** Plot shapes on map in realtime, updating every hour
 * @param {Object} options - options for plotting shapes
 * @param {string} options.url - url to geojson
 * @param {L.layerGroup} options.layer - layer to plot shapes on
 * @param {object} options.textboxSize - size of textbox
 * @param {boolean} options.isMobile - is the device mobile
 * @returns {Realtime} - realtime layer
 */
function plotShapes(options) {
  const { url, layer, textboxSize, isMobile } = options;
  const polyLineRender = L.canvas({ padding: 0.5, tolerance: 10 });
  const realtime = L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id; // geo
    },

    onEachFeature(f, l) {
      l.setStyle({
        color: `#${f.properties.route_color}`,
        weight: 1.3,
        renderer: polyLineRender,
      });
      l.feature.properties.searchName = f.properties.route_name;
      l.bindPopup(getShapeText(f.properties), textboxSize);
      if (!isMobile) l.bindTooltip(f.properties.route_name);
      l.on("click", function () {
        fillAlertShapeData(f.properties.route_id);
      });
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
  <a href="${
    properties.route_url
  }" rel="noopener" target="_blank" style="color:#${
    properties.route_color
  }" class="popup_header">${properties.route_name.replace("/", " / ")}</a>
  </p>`;
  shapeHtml.innerHTML += `<p class="popup_subheader">${properties.route_desc}</p>`;
  shapeHtml.innerHTML += "<hr />";
  // vehicleText.innerHTML += `<span name="pred-veh-${properties.trip_id}" class="fa hidden popup tooltip" data-tooltip="predictions">&#xf239;</span>&nbsp;&nbsp;&nbsp;`;
  shapeHtml.innerHTML += `<span name="alert-shape-${properties.route_id}" class="fa hidden popup tooltip slight-delay" data-tooltip="alerts">&#xf071;</span>`;
  shapeHtml.innerHTML += `<p>${properties.route_id} @ <a href="${properties.agency.agency_url}" rel="noopener" target="_blank">${properties.agency.agency_name}</a></p>`;
  shapeHtml.innerHTML += `<p>${properties.agency.agency_phone}</p>`;
  shapeHtml.innerHTML += `<div class="popup_footer"> 
        <p>${formatTimestamp(properties.timestamp)}</p>
    </div>`;
  return shapeHtml;
}

/**
 * fill alert shape data
 * @param {string} route_id
 * @returns
 */
async function fillAlertShapeData(route_id) {
  for (const alertEl of document.getElementsByName(`alert-shape-${route_id}`)) {
    const popupId = `popup-alert-${route_id}`;
    alertEl.onclick = function () {
      togglePopup(popupId);
    };
    const popupText = document.createElement("span");
    popupText.classList.add("popuptext");
    popupText.style.minWidth = "350px";
    popupText.id = popupId;
    popupText.innerHTML = "...";
    const _data = await (
      await fetch(`/api/alert?route_id=${route_id}&stop_id=null`)
    ).json();
    if (!_data.length) return;
    alertEl.classList.remove("hidden");
    popupText.innerHTML =
      "<table class='data-table'><tr><th>alert</th><th style='width:40%;'>period</th></tr>" +
      _data
        .map(function (d) {
          const strf = "%m-%d";
          const start = d.active_period_start
            ? formatTimestamp(d.active_period_start, strf)
            : null;
          const end = d.active_period_end
            ? formatTimestamp(d.active_period_end, strf)
            : null;

          return `<tr>
            <td>${d.header}</td>
            <td>${start} to ${end}</td>
          </tr>`;
        })
        .join("") +
      "</table>";
    alertEl.appendChild(popupText);
    setTimeout(() => {
      if (openPopups.includes(popupId)) togglePopup(popupId, true);
    }, 500);
  }
}
