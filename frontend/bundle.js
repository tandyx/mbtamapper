// bundle.js

import L from "leaflet";

//node js
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

// external css imports
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "leaflet.locatecontrol/dist/L.Control.Locate.min.css";
import "leaflet-fullscreen/dist/leaflet.fullscreen.css";
import "leaflet-easybutton/src/easy-button.css";
import "leaflet-search/dist/leaflet-search.mobile.min.css";
import "leaflet-search/dist/leaflet-search.min.css";
import "leaflet-sidebar/src/L.Control.Sidebar.css";

// css imports
import "./css/index.css";
import "./css/leaflet_custom.css";
import "./css/navbar.css";

globalThis.L = L;
globalThis.sorttable = sorttable;
globalThis.strftime = strftime;
globalThis.LocateControl = LocateControl;
// globalThis.BaseRealtimeLayer = BaseRealtimeLayer;
// Object.assign(globalThis, _utils);
