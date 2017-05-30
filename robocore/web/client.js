
function processImage(rgb_array) {
  $(imagenick).attr("src", "data:image/png;base64," + rgb_array);

/*
  var array = new Uint8ClampedArray(4 * 160 * 128);

  for (var x = 0; x < 160; x++) {
    for (var y = 0; y < 128; y++) {
      var i = (y * 160 + x) * 4;
      var j = (x * 128 + y) * 3;
      console.log("sample", rgb_array[j]);
      r = rgb_array.charCodeAt(j);
      g = rgb_array.charCodeAt(j+1);
      b = rgb_array.charCodeAt(j+2);
      array[i+0 ] = r;  // R
      array[i+1 ] = g;  // G
      array[i+2 ] = b;  // B
      array[i+3 ] = 255;  // A
    }
  }
  var imageData = new ImageData(array, 160, 128);

  var ctx = document.getElementById("canvas").getContext("2d");

  ctx.putImageData(imageData, 0, 0);
  */
}

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    image_updater.poll();
});

var image_updater = {
    errorSleepTime: 500,

    poll: function() {
        //var args = {"_xsrf": getCookie("_xsrf")};
        $.ajax({url: "/image",
                processData: false,
                success: image_updater.onSuccess,
                error: image_updater.onError});
    },

    onSuccess: function(data) {
        try {
          //  console.log("response length", data.length);
            processImage(data);
        } catch (e) {
            image_updater.onError();
            return;
        }
        image_updater.errorSleepTime = 500;
        window.setTimeout(image_updater.poll, 0);
    },

    onError: function(response) {
        image_updater.errorSleepTime *= 2;
        console.log("Poll error; sleeping for", image_updater.errorSleepTime, "ms");
        window.setTimeout(image_updater.poll, image_updater.errorSleepTime);
    },
};
