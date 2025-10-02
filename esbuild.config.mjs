import esbuild from "esbuild";
import fs from "fs";
import path from "path";

const DIST_DIR = "static/dist";

const footerCode = esbuild.transformSync(
  [
    "./frontend/js/utils.js",
    "./frontend/js/utilities/theme.js",
    "./frontend/js/utilities/layerfinder.js",
    "./frontend/js/realtime/base.js",
    "./frontend/js/realtime/facilities.js",
    "./frontend/js/realtime/shapes.js",
    "./frontend/js/realtime/stops.js",
    "./frontend/js/realtime/vehicles.js",
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
    entryPoints: ["frontend/bundle.js"],
    bundle: true,
    minify: true,
    sourcemap: true,
    format: "iife", // run in global scope
    outfile: `${DIST_DIR}/bundle.js`,
    assetNames: "asset/[name]",
    loader: {
      ".css": "css",
      ".png": "file",
      ".svg": "file",
      ".gif": "file",
      ".ttf": "file",
      ".woff2": "file",
    },
    legalComments: "linked",
    footer: { js: `;"use strict";${footerCode}` },
  })
  .then(() => {
    ["./frontend/js/index.js", "./frontend/js/map.js"].forEach((fpath) => {
      const src = esbuild.transformSync(
        fs.readFileSync(path.resolve(fpath), "utf8"),
        { loader: "js", minify: true }
      );
      fs.writeFileSync(`${DIST_DIR}/${fpath.split("/").at(-1)}`, src.code);
    });
    console.log(`esbuild success — see ${DIST_DIR}`);
  })
  .catch((err) => {
    console.error("esbuild failed", err);
    process.exit(1);
  });
