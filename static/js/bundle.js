// bundle.js

import L from "leaflet";

import "leaflet-easybutton";
import "leaflet-fullscreen";
import "leaflet-providers";
import "leaflet-realtime";
import "leaflet-search";
import "leaflet-sidebar";
import { LocateControl } from "leaflet.locatecontrol";
import "leaflet.markercluster";
import "leaflet.markercluster.freezable";

import "sorttable";
import strftime from "strftime";

// CSS imports
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "leaflet.locatecontrol/dist/L.Control.Locate.min.css";
import "leaflet-fullscreen/dist/leaflet.fullscreen.css";
import "leaflet-easybutton/src/easy-button.css";
import "leaflet-search/dist/leaflet-search.mobile.min.css";
import "leaflet-search/dist/leaflet-search.min.css";
import "leaflet-sidebar/src/L.Control.Sidebar.css";

window.L = L;
window.sorttable = sorttable;
window.strftime = strftime;
window.LocateControl = LocateControl;
