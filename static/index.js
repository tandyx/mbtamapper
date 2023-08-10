const ARRAY = [ 'SUBWAY', 'RAPID_TRANSIT', 'COMMUTER_RAIL', 'BUS', 'FERRY', 'ALL_ROUTES' ]
window.addEventListener('load', function () {

    L.Map.include({
        _initControlPos: function () {
          var corners = this._controlCorners = {},
            l = 'leaflet-',
            container = this._controlContainer =
              L.DomUtil.create('div', l + 'control-container', this._container);
      
          function createCorner(vSide, hSide) {
            var className = l + vSide + ' ' + l + hSide;
      
            corners[vSide + hSide] = L.DomUtil.create('div', className, container);
          }
      
          createCorner('top', 'left');
          createCorner('top', 'right');
          createCorner('bottom', 'left');
          createCorner('bottom', 'right');
      
          createCorner('top', 'center');
          createCorner('middle', 'center');
          createCorner('middle', 'left');
          createCorner('middle', 'right');
          createCorner('bottom', 'center');
        }
      });


    var route_type = ARRAY[Math.floor(Math.random() * ARRAY.length)];
    var zoom = route_type == "COMMUTER_RAIL" ? 11 : 13;
    var map = L.map('map', {
        zoomControl: false,
        maxZoom: zoom,
        minZoom: zoom,
    }).setView([42.3519, -71.0552], zoom);

    map.dragging.disable();
    map.touchZoom.disable();
    map.doubleClickZoom.disable();
    map.scrollWheelZoom.disable();
    map.boxZoom.disable();
    map.keyboard.disable();
    if (map.tap) map.tap.disable();
    document.getElementById('map').style.cursor='default';


    var CartoDB_Positron = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20,
    }).addTo(map);
    var CartoDB_DarkMatter = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20,
    });

    var shape_layer = L.layerGroup().addTo(map);
    realtime = plotShapes(route_type, shape_layer).addTo(map);

    map.on("click", function () {
        if (map.hasLayer(CartoDB_Positron)) {
            map.removeLayer(CartoDB_Positron);
            map.addLayer(CartoDB_DarkMatter);
        } else {
            map.removeLayer(CartoDB_DarkMatter);
            map.addLayer(CartoDB_Positron);
        }
    });
    
    L.Control.textbox = L.Control.extend({
		onAdd: function(map) {
			
		var text = L.DomUtil.create('div');
		text.id = "info_text";
		text.innerHTML = `
        <div style="font-size:10pt;font-family: 'montserrat','sans-serif';color: #ffffff;background: rgba(0, 0, 0, 0.9);width: auto;overflow: hidden;padding: 14px 16px;border: 1px solid black;border-radius: 4px;text-align: center;justify-content: center;">
            <h1>MBTA Mapper</h1>
            <table style="margin-left: auto;margin-right: auto;width:auto;">
                <tr>
                    <td style="padding: 15px">
                        <a href="/subway/" style="font-weight:bold;text-decoration:none;color:#7C878E;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Icon-mode-subway-default.svg/512px-Icon-mode-subway-default.svg.png" width="125"><br><br>
                            Subway
                        </a>
                    </td>
                    <td style="padding: 15px">
                        <a href="/rapid_transit/" style="font-weight:bold;text-decoration:none;color:#ED8B00;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Icon-mode-subway-default.svg/512px-Icon-mode-subway-default.svg.png" width="125" style="filter: invert(60%) sepia(38%) saturate(1600%) hue-rotate(8deg) brightness(102%) contrast(101%);"><br><br>
                            Rapid Transit
                        </a>
                    </td>
                    <td style="padding: 15px">
                        <a href="/commuter_rail/" style="font-weight:bold;text-decoration:none;color:#80276C;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Icon-mode-commuter-rail-default.svg/512px-Icon-mode-commuter-rail-default.svg.png" width="125"><br><br>
                            Commuter Rail
                        </a>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 15px">
                        <a href="/bus/" style="font-weight:bold;text-decoration:none;color:#FFC72C;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Icon-mode-bus-default.svg/512px-Icon-mode-bus-default.svg.png" width="125"><br><br>
                            Bus <a style="color:red">(30s updates)</a>
                        </a>
                    </td>
                    <td style="padding: 15px">
                        <a href="/ferry/" style="font-weight:bold;text-decoration:none;color:#006595;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Icon-mode-ferry-default.svg/512px-Icon-mode-ferry-default.svg.png" width="125"><br><br>
                            Ferry <a style="color:red">(no vehicle data)</a>
                        </a>
                    </td>
                    <td style="padding: 15px">
                        <a href="/all_routes/" style="font-weight:bold;text-decoration:none;color:#ffffff;">
                            <img src="/static/mbta.png" width="125"><br><br>
                            All Routes <a style="color:red">(30s updates)</a>
                        </a>
                    </td>
                </tr>
            </table>
            <div style="margin-top:25px">
                This was my personal project. While I used to work for Keolis, I have no further affiliation with the MBTA.<br><br>
                <a href="https://github.com/tandy-c/mbta_mapper" style="font-weight:bold;text-decoration:none;color:#ffffff;padding:15px;">
                    <img src="https://icon-library.com/images/github-icon-white/github-icon-white-5.jpg" width="45">
                </a>
                <a href="https://www.linkedin.com/in/chojohan/" style="font-weight:bold;text-decoration:none;color:#ffffff;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/LinkedIn_logo_initials.png/600px-LinkedIn_logo_initials.png" width="45">
                </a>
            </div>
        </div>
        `
		return text;
		},

		onRemove: function(map) {
			// Nothing to do here
		}
	});
    
	L.control.textbox = function(opts) { return new L.Control.textbox(opts);}
	L.control.textbox({ position: 'topcenter' }).addTo(map);
    
});

// var zoom = route_type == "commuter_rail" ? 9 : 13;

function plotShapes(key, layer) {
    let polyLineRender = L.canvas({ padding: 0, tolerance: 0 });
    return L.realtime(
        `/static/geojsons/${key}/shapes.json`,
        {
            interval: 360000000000000,
            type: 'FeatureCollection',
            container: layer,
            cache: true,
            removeMissing: true,
            getFeatureId(f) {
                return f.id;
            },
            onEachFeature(f, l) {
                l.setStyle({
                    interactive: false,
                    color: f.properties.color,
                    opacity: f.properties.opacity,
                    weight: 1.3,
                    renderer: polyLineRender,
                });
            },
        }
    )
}