function hoverImage(image_id, interval = 250) {
  var image = document.getElementById(image_id);
  // image.style.visibility = "hidden";
  image.animate({ transform: "scale(1.07)" }, interval).onfinish = function () {
    image.style.transform = "scale(1.07)";
  };
}

function unhoverImage(image_id, interval = 250) {
  var image = document.getElementById(image_id);
  // image.style.visibility = "hidden";
  image.animate({ transform: "scale(1)" }, interval).onfinish = function () {
    image.style.transform = "scale(1)";
  };
}
function openMiniPopup(popupId) {
  var miniPopup = document.getElementById(popupId);
  miniPopup.classList.toggle("show");
}
