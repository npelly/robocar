var session_id = -1;  // updated elsewhere

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
