
// Initialize Chart.js
let ctx = document.getElementById('myChart').getContext('2d');
let myChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: []
    },
    options: {
        scales: {
            x: {
                type: 'linear',
                position: 'bottom',
                title: {
                    display: true,
                    text: 'Data Points'
                }
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Values'
                }
            }
        }
    }
});

// Initialize socket.io connection
document.addEventListener("DOMContentLoaded", function () {
    let socket = io.connect("http://" + document.domain + ":" + location.port);

    // Handle file selection click
    document.querySelector(".gui__file").addEventListener("click", function () {
        document.getElementById("scriptSelector").click();
    });

    // Update file name display
    let selectElement = document.getElementById("scriptSelector");
    let labelElement = document.getElementById("hiddenFileInput");
    selectElement.addEventListener("change", function () {
        let selectedText = selectElement.options[selectElement.selectedIndex].text;
        labelElement.textContent = selectedText.split('/').pop();
    });

    // add param (from the first script)
    $(document).on('click', '.add-param-button', function () {
        let currentParams = $('.param-input').length;
        let newParamEnd = Math.min(currentParams + 1, 20);

        for (let i = currentParams + 1; i <= newParamEnd; i++) {
            $('<input type="text" class="param-input" id="param' + (i) + '" name="param' + (i) + '" placeholder="Param ' + (i) + '">').insertBefore('.add-param-button');
        }
    });

    // Modal for confirmation
    let startButton = document.getElementById("startButton");
    let stopButton = document.getElementById("stopButton");
    let modal = document.getElementById("commandModal");
    let span = document.getElementsByClassName("close")[0];
    let confirmButton = document.getElementById("confirmButton");
    let commandText = document.getElementById("commandText");

    // Handle start button click
    startButton.addEventListener("click", function (event) {
        event.preventDefault();
        let selectedFile = document.getElementById("scriptSelector").value;

        // gather parameters
        let params = {};
        $('.param-input').each(function (index, element) {
            let paramId = element.id;
            params[paramId] = element.value;
        });

        let paramStr = Object.values(params)
            .filter(value => value !== "")
            .join("  ");

        // Extract the file name only in modal
        let filename = selectedFile.split('/').pop();
        let command = `python3 ${filename} ${paramStr}`;
        commandText.textContent = command;
        modal.style.display = "block";
    });

    // Handle confirmation button click
    confirmButton.addEventListener("click", function () {
        let selectedFile = document.getElementById("scriptSelector").value;

        // gather parameters
        let params = {};
        $('.param-input').each(function (index, element) {
            let paramId = element.id;
            params[paramId] = element.value;
        });

        document.getElementById("output").textContent = ""; // Clear output area
        // Reset chart data
        myChart.data.labels = [];
        myChart.data.datasets = [];
        myChart.update();

        socket.emit("start_script", { filename: selectedFile, params: params });
        modal.style.display = "none";
    });

    // Handle stop button
    stopButton.addEventListener("click", function (event) {
        event.preventDefault();
        socket.emit("stop_script");

        // Clear output
        document.getElementById("output").textContent = "";;

        // Reset the chart
        myChart.data.labels = [];
        myChart.data.datasets = [];
        myChart.update();
    });

    // Handle script stopped
    socket.on("script_stopped", function () {
        document.getElementById("output").textContent += "Script stopped by user\n";
    });

    // Handle script output (combining both scripts)
    socket.on("script_output", function (data) {
        let outputElement = document.getElementById("output");
        outputElement.textContent += data.output; // Append new output
        outputElement.scrollTop = outputElement.scrollHeight; // Auto scroll to the bottom

        // Split and parse data output
        let parts = data.output.trim().split(":");
        let labels = parts.filter((part, index) => index % 2 === 0).map(label => label.trim()); // Extract labels
        let values = parts.filter((part, index) => index % 2 !== 0).map(value => Number(value.trim()));

        // Add a new data point
        let newIndex = myChart.data.labels.length + 1;
        myChart.data.labels.push(newIndex);

        // Update or add datasets
        labels.forEach((label, index) => {
            let dataset = myChart.data.datasets.find(ds => ds.label === label);
            if (dataset) {
                dataset.data.push(values[index]);
            } else {
                let color = `rgb(${Math.floor(Math.random() * 255)},${Math.floor(Math.random() * 255)},${Math.floor(Math.random() * 255)})`;
                myChart.data.datasets.push({
                    label: label,
                    data: Array(newIndex - 1).fill(null).concat(values[index]),
                    backgroundColor: color,
                    borderColor: color,
                    borderWidth: 1,
                    fill: false
                });
            }
        });

        myChart.update();
    });

    // Close modal
    span.onclick = function () {
        modal.style.display = "none";
    };

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };
});
