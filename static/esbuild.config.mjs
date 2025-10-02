import esbuild from "esbuild";
import fs from "fs";
import path from "path";

const bannerCode = esbuild.transformSync(
  [
    "./js/utils.js",
    "./js/utilities/theme.js",
    "./js/utilities/layerfinder.js",
    "./js/realtime/base.js",
    "./js/realtime/facilities.js",
    "./js/realtime/shapes.js",
    "./js/realtime/stops.js",
    "./js/realtime/vehicles.js",
  ]
    .map((fpath) =>
      fs.readFileSync(path.resolve(fpath), "utf8").replace(`"use strict";`, "")
    )
    .join("\n"),
  {
    loader: "js",
    keepNames: true,
    minifySyntax: false,
    minifyWhitespace: true,
  }
).code;

esbuild
  .build({
    entryPoints: ["bundle.js"], // only one true entry
    bundle: true,
    minify: true,
    // sourcemap: true,
    format: "iife", // run in global scope
    outfile: "bundle/bundle.js", // single output file
    assetNames: "images/[name]",

    loader: {
      ".css": "css",
      ".png": "file",
      ".svg": "file",
      ".gif": "file",
      ".ttf": "file",
      ".woff2": "file",
    },

    legalComments: "linked",
    footer: { js: `;"use strict";${bannerCode}` },
  })
  .then(() => {
    console.log("esbuild success — see ./bundle/");
  })
  .catch((err) => {
    console.error("esbuild failed", err);
    process.exit(1);
  });
