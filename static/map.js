const ROUTE_TYPE = window.location.href.split("/").slice(-2)[0].toUpperCase();
document.title = "MBTA " + titleCase(ROUTE_TYPE) + " Realtime Map";
onLoad(ROUTE_TYPE.toLowerCase());

window.addEventListener("load", function () {
  var map = L.map("map", {
    minZoom: 9,
    maxZoom: 20,
    maxBounds: L.latLngBounds(L.latLng(40, -74), L.latLng(44, -69)),
    fullscreenControl: true,
    fullscreenControlOptions: {
      position: "topleft",
    },
  }).setView([42.3519, -71.0552], ROUTE_TYPE == "COMMUTER_RAIL" ? 10 : 13);

  var CartoDB_Positron = L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 20,
    }
  ).addTo(map);
  var CartoDB_DarkMatter = L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 20,
    }
  );
  map.attributionControl.removeAttribution(
    "| © OpenStreetMap contributors © CARTO"
  );

  var stop_layer = L.layerGroup().addTo(map);
  var shape_layer = L.layerGroup().addTo(map);
  var vehicle_layer = L.markerClusterGroup({
    disableClusteringAtZoom: ROUTE_TYPE == "COMMUTER_RAIL" ? 10 : 12,
  }).addTo(map);
  var parking_lots = L.layerGroup();

  var stopsRealtime = plotStops(
    `/static/geojsons/${ROUTE_TYPE}/stops.json`,
    stop_layer
  ).addTo(map);
  var shapesRealtime = plotShapes(
    `/static/geojsons/${ROUTE_TYPE}/shapes.json`,
    shape_layer
  ).addTo(map);
  var vehiclesRealtime = plotVehicles(
    `/${ROUTE_TYPE.toLowerCase()}/vehicles`,
    vehicle_layer
  ).addTo(map);
  var facilitiesRealtime = plotFacilities(
    `/static/geojsons/${ROUTE_TYPE}/park.json`,
    parking_lots
  );
  controlSearch = L.control
    .search({
      layer: L.layerGroup([
        stop_layer,
        shape_layer,
        vehicle_layer,
        parking_lots,
      ]),
      initial: false,
      propertyName: "name",
      zoom: 16,
      marker: false,
      textPlaceholder: "",
    })
    .addTo(map);

  L.control
    .layers(
      {
        Dark: CartoDB_DarkMatter,
        Light: CartoDB_Positron,
      },
      {
        Vehicles: vehicle_layer,
        Stops: stop_layer,
        Shapes: shape_layer,
        "Parking Lots": parking_lots,
      }
    )
    .addTo(map);

  if (map.hasLayer(parking_lots) == true) {
    map.removeLayer(parking_lots);
  }

  controlSearch.on("search:locationfound", function (event) {
    event.layer.openPopup();
  });

  for (realtime of [stopsRealtime, shapesRealtime, facilitiesRealtime]) {
    realtime.on("update", function (e) {
      Object.keys(e.update).forEach(
        function (id) {
          var feature = e.update[id];
          var wasOpen = this.getLayer(id).getPopup().isOpen();
          if (wasOpen === true) {
            this.getLayer(id).closePopup();
          }

          this.getLayer(id).bindPopup(feature.properties.popupContent, {
            maxWidth: "auto",
          });

          if (wasOpen === true) {
            this.getLayer(id).openPopup();
          }
        }.bind(this)
      );
    });
  }

  vehiclesRealtime.on("update", function (e) {
    Object.keys(e.update).forEach(
      function (id) {
        var layer = this.getLayer(id);
        var feature = e.update[id];
        var wasOpen = layer.getPopup().isOpen();
        layer.unbindPopup();
        if (wasOpen === true) {
          layer.closePopup();
        }
        layer.bindPopup(feature.properties.popupContent, { maxWidth: "auto" });
        layer.setIcon(
          L.divIcon({
            html: feature.properties.icon,
            iconSize: [15, 15],
          })
        );
        if (wasOpen === true) {
          layer.openPopup();
        }
      }.bind(this)
    );
  });
  // showPredictionPopup();

  map.on("zoomend", function () {
    if (map.getZoom() < 16) {
      map.removeLayer(parking_lots);
    }
    if (map.getZoom() >= 16) {
      map.addLayer(parking_lots);
    }
    console.log(map.getZoom());
  });
});

function onLoad(route_type, array = null) {
  if (array == null) {
    array = [
      { href: "/static/mbta.favicon", rel: "icon" },
      {
        href: "/static/custom_js/leaflet-realtime/leaflet-realtime.js",
        rel: "script",
      },
      {
        href: "/static/custom_js/leaflet-realtime/leaflet-realtime.min.js",
        rel: "script",
      },
      {
        href: "/static/custom_js/leaflet-fullscreen/Control.FullScreen.css",
        rel: "stylesheet",
      },
      {
        href: "/static/custom_js/leaflet-fullscreen/Control.FullScreen.js",
        rel: "script",
      },
      {
        href: "/static/custom_js/leaflet-search/leaflet-search.js",
        rel: "script",
      },
      {
        href: "/static/custom_js/leaflet-search/leaflet-search.mobile.css",
        rel: "stylesheet",
      },
      {
        href: "/static/custom_js/leaflet-search/leaflet-search.css",
        rel: "stylesheet",
      },
      { href: "/static/custom_css/popup.css", rel: "stylesheet" },
      { href: "/static/custom_css/tooltip.css", rel: "stylesheet" },
      { href: "/static/custom_css/table.css", rel: "stylesheet" },
      { href: "/static/custom_css/scrollbar.css", rel: "stylesheet" },
      { href: "/static/custom_css/leaflet_custom.css", rel: "stylesheet" },
    ];
  }
  for (linkdict of array) {
    if (linkdict.rel != "script") {
      var link = document.createElement("link");
      link.rel = linkdict.rel;
      link.href = `/${route_type}` + linkdict.href;
    } else {
      var link = document.createElement("script");
      link.src = `/${route_type}` + linkdict.href;
    }
    document.head.appendChild(link);
  }
}

function plotVehicles(url, layer) {
  return L.realtime(url, {
    interval: !["BUS", "ALL_ROUTES"].includes(ROUTE_TYPE) ? 15000 : 45000,
    type: "FeatureCollection",
    container: layer,
    cache: false,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      var icon = L.divIcon({
        html: f.properties.icon,
        iconSize: [15, 15],
      });
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
      l.setIcon(icon);
      l.setZIndexOffset(100);
    },
  });
}

function plotStops(url, layer) {
  const stopIcon = L.icon({
    iconUrl: "/static/mbta.png",
    iconSize: [15, 15],
  });

  return L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      // l.setStyle({ renderer: L.canvas({ padding: 0.5, tolerance: 10 }) });
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
      l.setIcon(stopIcon);
      l.setZIndexOffset(-100);
    },
  });
}

function plotShapes(url, layer) {
  let polyLineRender = L.canvas({ padding: 0.5, tolerance: 10 });

  return L.realtime(url, {
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
        color: f.properties.color,
        opacity: f.properties.opacity,
        weight: 1.3,
        renderer: polyLineRender,
      });

      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
    },
  });
}

function plotFacilities(url, layer) {
  const facilityIcon = L.icon({
    iconUrl: "/static/parking.png",
    iconSize: [15, 15],
  });

  return L.realtime(url, {
    interval: 3600000,
    type: "FeatureCollection",
    container: layer,
    cache: true,
    removeMissing: true,
    getFeatureId(f) {
      return f.id;
    },
    onEachFeature(f, l) {
      l.bindPopup(f.properties.popupContent, { maxWidth: "auto" });
      l.bindTooltip(f.properties.name);
      l.setIcon(facilityIcon);
      l.setZIndexOffset(-150);
    },
  });
}

function openMiniPopup(popupId) {
  var miniPopup = document.getElementById(popupId);
  miniPopup.classList.toggle("show");
}

function titleCase(str, split = "_") {
  return str
    .toLowerCase()
    .split(split)
    .map(function (word) {
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}
