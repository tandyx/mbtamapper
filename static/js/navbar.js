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
  const menutoggle = document.getElementById("menu-toggle");
  const _custNav = document.getElementById("navbar");
  const _menu = _custNav.getElementsByClassName("menu")[0];
  for (const child of _menu.children) {
    if (child.id !== "modeToggle") continue;
    const anchor = child.getElementsByTagName("a")[0];
    anchor.text = Theme.unicodeIcon;
    child.addEventListener("click", () => {
      anchor.text = Theme.fromExisting().reverse().unicodeIcon;
    });
  }
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768 && menutoggle.checked) menutoggle.click();
  });
});
