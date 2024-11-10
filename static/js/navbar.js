/**
 * @typedef {import("./utils.js")}
 */

document.addEventListener("click", (event) => {
  if (!event.target?.closest(".nav")) {
    const menuToggle = document.getElementById("menu-toggle");
    if (menuToggle && menuToggle.checked) menuToggle.checked = false;
  }
});

window.addEventListener("load", () => {
  const _custNav = document.getElementById("navbar");
  const _menu = _custNav.getElementsByClassName("menu")[0];
  for (const child of _menu.children) {
    for (const anchor of child.getElementsByTagName("a")) {
      if (anchor.href === window.location.href) anchor.href = "#";
      if (
        window.location.pathname.startsWith(
          anchor.pathname.split(".")[0].replace("index", "") || "/"
        )
      ) {
        anchor.style.color = "var(--accent-color)";
      }
    }
  }
  const menutoggle = document.getElementById("menu-toggle");
  const styleSheet = getStylesheet("nav");
  if (!menutoggle) return;
  menutoggle.addEventListener("change", () => {
    const menu = document.getElementById("navmenu");
    if (!styleSheet || !menu) return;
    styleSheet.insertRule(
      `nav:has(#menu-toggle:checked)::before { position: absolute; height: calc(${getStyle(
        menu,
        "height"
      )} + ${getStyle(menu.children[0], "height")} - ${getStyle(
        menu.children[menu.children.length - 1],
        "border-bottom-width"
      )}) }`
    );
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 768 && menutoggle.checked) {
      menutoggle.click();
    }
  });
});
