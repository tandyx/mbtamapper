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
  const toggle = [..._menu.children].filter((c) => c.id === "modeToggle")[0];
  if (!toggle) return;
  const anchor = toggle.getElementsByTagName("a")[0];
  anchor.text = Theme.unicodeIcon;
  toggle.addEventListener("click", () => {
    const theme = Theme.fromExisting().reverse(localStorage, onThemeChange);
    anchor.text = theme.unicodeIcon;
  });
  window.addEventListener("resize", () => {
    if (window.innerWidth > 768 && menutoggle.checked) menutoggle.click();
  });
});
