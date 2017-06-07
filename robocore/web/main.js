var session_id = -1;  // updated elsewhere
var atom_id = -1;     // updated elsewhere

function pollLive() {
	$.ajax({
		url: "live/more?session_id=" + session_id + "&atom_id=" + atom_id,
		success: function(html) {
			$("body").append(html);
			window.scrollTo(0,document.body.scrollHeight);
			window.setTimeout(pollLive, 0);
		},
    error: function() {
      window.setTimeout(pollLive, 1000);
    },
  });
}

function pollSessionList() {
	$.ajax({
		url: "more?session_id=" + session_id,
		success: function(html) {
			$("body").append(html);
			window.scrollTo(0,document.body.scrollHeight);
			window.setTimeout(pollSessionList, 0);
		},
    error: function() {
      window.setTimeout(pollSessionList, 1000);
    },
  });
}

function imageClick(image) {
	var scale = 1;
	if (image.hasAttribute("scale")) {
		scale = parseInt(image.getAttribute("scale"));
	}

	var original_width = image.width / scale;

	// height seems to automatically adjust
	if (scale <= 3) {
		image.width += original_width;
		image.setAttribute("scale", scale + 1);
	} else {
		image.width = original_width;
		image.removeAttribute("scale");
	}
}
