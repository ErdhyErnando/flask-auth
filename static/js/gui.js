document.addEventListener("DOMContentLoaded", function () {
  var socket = io.connect("http://" + document.domain + ":" + location.port);

  document.querySelector(".gui__file").addEventListener("click", function () {
      document.getElementById("scriptSelector").click();
  });

  var selectElement = document.getElementById("scriptSelector");
  var labelElement = document.getElementById("hiddenFileInput");
  selectElement.addEventListener("change", function () {
      var selectedText = selectElement.options[selectElement.selectedIndex].text;
      var filename = selectedText.split('/').pop();
      labelElement.textContent = filename;
  });

  var startButton = document.getElementById("startButton");
  var stopButton = document.getElementById("stopButton");
  var modal = document.getElementById("commandModal");
  var span = document.getElementsByClassName("close")[0];
  var confirmButton = document.getElementById("confirmButton");
  var commandText = document.getElementById("commandText");

  startButton.addEventListener("click", function (event) {
      event.preventDefault();
      var selectedFile = document.getElementById("scriptSelector").value;
      var params = {
          param1: document.getElementById("param1").value,
          param2: document.getElementById("param2").value,
          param3: document.getElementById("param3").value,
          param4: document.getElementById("param4").value,
          param5: document.getElementById("param5").value
      };

      var paramStr = Object.keys(params)
          .filter(key => params[key] !== "")
          .map(key => `--${key} ${params[key]}`)
          .join(" ");

      var command = `python3 ${selectedFile} ${paramStr}`;
      commandText.textContent = command;
      modal.style.display = "block";
  });

  confirmButton.addEventListener("click", function () {
      var selectedFile = document.getElementById("scriptSelector").value;
      var params = {
          param1: document.getElementById("param1").value,
          param2: document.getElementById("param2").value,
          param3: document.getElementById("param3").value,
          param4: document.getElementById("param4").value,
          param5: document.getElementById("param5").value
      };
      document.getElementById("output").textContent = ""; // Clear output area
      socket.emit("start_script", { filename: selectedFile, params: params });
      modal.style.display = "none";
  });

  stopButton.addEventListener("click", function (event) {
      event.preventDefault();
      socket.emit("stop_script");
  });

  socket.on("script_output", function (data) {
      var outputElement = document.getElementById("output");
      outputElement.textContent += data.output; // Append new output with a newline
      outputElement.scrollTop = outputElement.scrollHeight; // Auto scroll to the bottom
  });

  span.onclick = function () {
      modal.style.display = "none";
  };

  window.onclick = function (event) {
      if (event.target == modal) {
          modal.style.display = "none";
      }
  };
});