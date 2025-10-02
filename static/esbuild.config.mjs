import esbuild from "esbuild";
import fs from "fs";
import path from "path";

// import { transformSync } from "@swc/core";

/**
 * loads file as javascript
 * @param {string} filePath
 * @param {boolean} [plain=false]
 * @returns
 */
function loadFile(filePath, plain = false) {
  const abs = path.resolve(filePath);
  if (!fs.existsSync(abs)) {
    console.warn(`file not found: ${filePath} — skipping`);
    return `// missing: ${filePath}\n`;
  }
  const src = fs.readFileSync(path.resolve(filePath), "utf8");
  if (plain) return src;
  return /* JS */ `// --- begin content: ${filePath}\n${src}\n// --- end content: ${filePath}\n`;
}

const bannerCode = [
  "./js/utils.js",
  "./js/utilities/theme.js",
  "./js/utilities/layerfinder.js",
  "./js/realtime/base.js",
  "./js/realtime/facilities.js",
  "./js/realtime/shapes.js",
  "./js/realtime/stops.js",
  "./js/realtime/vehicles.js",
]

  .map(
    (f) =>
      esbuild.transformSync(
        fs
          .readFileSync(path.resolve(filePath), "utf8")
          .replace(`"use strict";`, ""),
        {
          loader: "js",
          keepNames: true,
          minifySyntax: false,
          minifyWhitespace: true,
        }
      ).code
  )
  .join("\n");

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
    // banner: { js: `"use strict";` },
    footer: { js: `;"use strict";${bannerCode}` },
  })
  .then(() => {
    console.log("esbuild success — see ./bundle/");
  })
  .catch((err) => {
    console.error("esbuild failed", err);
    process.exit(1);
  });
