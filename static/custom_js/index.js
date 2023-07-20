


function showPredictionPopup() {
    var predictionPopup = document.getElementById("predictionPopup");
    predictionPopup.classList.toggle("show");
}
function showAlertPopup() {
    var alertPopup = document.getElementById("alertPopup");
    alertPopup.classList.toggle("show");
}
function getRouteType() {
    var tmp = null;
    $.ajax({
        'async': false,
        'type': "GET",
        'global': false,
        'dataType': 'html',
        'url': "/value",
        'data': { 'request': "", 'target': 'arrange_url', 'method': 'method_target' },
        'success': function (data) {
            tmp = data;
        }
    }
    );
    console.log(tmp)
    return tmp;
};