var oldURL = null;

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    //imageUpdater.poll();
    ws = new WebSocket("ws://pi.local:8888/imagesocket");
    ws.binaryType = "blob"
    ws.onopen = function() {
      ws.send("1");
    }
    ws.onmessage = function(message) {
      ws.send("1");

    //  var blob = new Blob([message.data], {type: "image/png"});
    //  console.log("msg size is", message.data.size, "blob size is", blob.size);
//      var URL = window.URL.createObjectURL(message.data);
//      $(imagenick).attr("src", URL);
      if (oldURL != null) {
  //      revokeObjectURL(oldURL);   // made no difference
      }
      oldURL = URL;

    }
});

var imageUpdater = {
    errorSleepTime: 500,

    poll: function() {

        fetch("/image")
          .then(function(response) {
            return response.blob();
          })
          .then(imageUpdater.onSuccess);
    },

    updateImage: function(imageBlob) {
        var URL = window.URL.createObjectURL(imageBlob);
        $(imagenick).attr("src", URL);
    },

    onSuccess: function(response) {
        try {
            imageUpdater.updateImage(response);
        } catch (e) {
            imageUpdater.onError();
            return;
        }
        imageUpdater.errorSleepTime = 500;
        window.setTimeout(imageUpdater.poll, 0);
    },

    onError: function(response) {
        imageUpdater.errorSleepTime *= 2;
        console.log("Poll error; sleeping for", imageUpdater.errorSleepTime, "ms");
        window.setTimeout(imageUpdater.poll, imageUpdater.errorSleepTime);
    },
};
