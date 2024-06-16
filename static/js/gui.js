document.querySelector(".gui__file").addEventListener("click", function () {
  document.getElementById("scriptSelector").click();
});

document.addEventListener("DOMContentLoaded", function () {
  var selectElement = document.getElementById("scriptSelector");
  var labelElement = document.getElementById("hiddenFileInput");
  selectElement.addEventListener("change", function () {
    var selectedText = selectElement.options[selectElement.selectedIndex].text;
    var filename = selectedText.split('/').pop();
    labelElement.textContent = filename;
  });
});

document.addEventListener("DOMContentLoaded", function () {
  var socket = io.connect("http://" + document.domain + ":" + location.port);

  document
    .getElementById("startButton")
    .addEventListener("click", function (event) {
      event.preventDefault();
      var selectedFile = document.getElementById("scriptSelector").value;
      document.getElementById("output").textContent = ""; // Clear output area
      socket.emit("start_script", { filename: selectedFile });
    });

  document
    .getElementById("stopButton")
    .addEventListener("click", function (event) {
      event.preventDefault();
      socket.emit("stop_script");
    });

  socket.on("script_output", function (data) {
    var outputElement = document.getElementById("output");
    outputElement.textContent += data.output; // Append new output
    outputElement.scrollTop = outputElement.scrollHeight; // Auto scroll to the bottom
  });
});
