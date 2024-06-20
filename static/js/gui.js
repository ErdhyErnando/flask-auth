// Create a new Chart.js instance
var ctx = document.getElementById('myChart').getContext('2d');
var myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], // You will fill this array with your labels
        datasets: [{
            label: 'My Dataset',
            data: [], // You will fill this array with your data
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

// socketio connnection
document.addEventListener("DOMContentLoaded", function () {
    var socket = io.connect("http://" + document.domain + ":" + location.port);

    document.querySelector(".gui__file").addEventListener("click", function () {
        document.getElementById("scriptSelector").click();
    });

    // choose file and display the file name
    var selectElement = document.getElementById("scriptSelector");
    var labelElement = document.getElementById("hiddenFileInput");
    selectElement.addEventListener("change", function () {
        var selectedText = selectElement.options[selectElement.selectedIndex].text;
        var filename = selectedText.split('/').pop();  // Get the file name only
        labelElement.textContent = filename;
    });

    // Modal for confirmation
    var startButton = document.getElementById("startButton");
    var stopButton = document.getElementById("stopButton");
    var modal = document.getElementById("commandModal");
    var span = document.getElementsByClassName("close")[0];
    var confirmButton = document.getElementById("confirmButton");
    var commandText = document.getElementById("commandText");

    // Event listeners for parameters 
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


        // Extract the file name only in modal
        var filename = selectedFile.split('/').pop();
        var command = `python3 ${paramStr} ${filename} `;
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


    // stop button
    stopButton.addEventListener("click", function (event) {
        event.preventDefault();
        socket.emit("stop_script");
    });

    // script output
    socket.on("script_output", function (data) {
        var outputElement = document.getElementById("output");
        outputElement.textContent += data.output; // Append new output with a newline
        outputElement.scrollTop = outputElement.scrollHeight; // Auto scroll to the bottom
        
        var parsedData = JSON.parse(data.output);
    
        myChart.data.labels = parsedData.labels;
        myChart.data.datasets[0].data = parsedData.data;
        myChart.update();
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



