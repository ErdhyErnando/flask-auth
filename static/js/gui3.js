
document.addEventListener("DOMContentLoaded", function () {

    // Initialize Chart.js
    let ctx = document.getElementById('myChart').getContext('2d');
    let myChart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: []
        },
        options: {
            animation: false,
            responsive: true,
            scales: {
                x: {
                    type: 'linear',
                    position: 'bottom',
                    title: {
                        display: true,
                        text: 'Time (seconds)'
                    },
                    ticks: {
                        callback: function (value) {
                            return value.toFixed(1) + 's';
                        }
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
    let socket = io.connect("http://" + document.domain + ":" + location.port);

    // File selection
    let fileExplorerModal = document.getElementById('fileExplorerModal');
    let fileExplorer = document.getElementById('fileExplorer');
    let selectedFile = '';
    let chooseFileLabel = document.getElementById('chooseFileLabel');
    let selectedFileDisplay = document.getElementById('selectedFileDisplay');

    // Open file explorer modal when "Choose Files" is clicked
    chooseFileLabel.addEventListener('click', function () {
        fileExplorerModal.style.display = 'block';
    });

    // Close File explorer modal
    let closeButtons = document.getElementsByClassName('close');
    for (let i = 0; i < closeButtons.length; i++) {
        closeButtons[i].addEventListener('click', function () {
            fileExplorerModal.style.display = 'none';
        });
    }

    // Create file explorer modal
    function createFileExplorer(structure, parentElement, path = '/home/pi/flask-auth/orthosis-scripts/') {
        structure.forEach(item => {
            let itemElement = document.createElement('div');
            itemElement.classList.add('file-explorer-item');

            if (item.type === 'folder') {
                itemElement.innerHTML = `<span class="folder-icon">📁</span> ${item.name}`;
                itemElement.classList.add('folder');
                let childrenContainer = document.createElement('div');
                childrenContainer.classList.add('folder-children');
                childrenContainer.style.display = 'none';
                createFileExplorer(item.children, childrenContainer, path + item.name + '/');
                itemElement.appendChild(childrenContainer);

                itemElement.addEventListener('click', function (e) {
                    e.stopPropagation();
                    childrenContainer.style.display = childrenContainer.style.display === 'none' ? 'block' : 'none';
                    console.log(path + item.name);
                });
            } else {
                // check if it is a .py file
                let fileIcon = item.name.endsWith('.py') ? '<span class="file-icon">🐍</span>' : '<span class="file-icon">📄</span>';

                itemElement.innerHTML = `${fileIcon} ${item.name}`;
                itemElement.classList.add('file');
                itemElement.addEventListener('click', function (e) {
                    e.stopPropagation();
                    selectedFile = path + item.name;
                    selectedFileDisplay.textContent = item.name;
                    fileExplorerModal.style.display = 'none';
                    // document.getElementById('hiddenFileInput').textContent = selectedFile;
                });
            }

            parentElement.appendChild(itemElement);
        });
    }

    // Fetch file structure from server
    fetch('/get_file_structure')
        .then(response => response.json())
        .then(data => {
            createFileExplorer(data, fileExplorer);
        });


    // Handle file selection
    fileExplorer.addEventListener('click', function (e) {
        if (e.target.classList.contains('file')) {
            let fileName = e.target.textContent.trim();
            let filePath = e.target.closest('.folder-children') ?
                e.target.closest('.folder-children').previousSibling.textContent.trim() + '/' + fileName :
                fileName;
            selectedFile = filePath;
            selectedFileDisplay.textContent = fileName;
            fileExplorerModal.style.display = 'none';
        }
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
    let span = document.getElementsByClassName("closeModal")[0];
    let confirmButton = document.getElementById("confirmButton");
    let commandText = document.getElementById("commandText");


    // Handle start button click
    startButton.addEventListener("click", function (event) {
        event.preventDefault();
        if (!selectedFile) {
            alert('Please select a file');
            return;
        }

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

        // gather parameters
        let params = {};
        $('.param-input').each(function (index, element) {
            let paramId = element.id;
            params[paramId] = element.value;
        });

        document.getElementById("output").textContent = ""; // Clear output area

        // Clear label filters
        document.getElementById('labelFilters').innerHTML = '';
        labelFilters = {};

        startTime = null;
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

        startTime = null;
        myChart.data.datasets = [];
        myChart.update();
    });


    // Handle script stopped
    socket.on("script_stopped", function () {
        document.getElementById("output").textContent += "Script stopped by user\n";
    });

    let labelFilters = {};
    // Function to create or update Label filters
    function updateLabelFilter(labels) {
        const filterContainer = document.getElementById('labelFilters');

        labels.forEach(label => {
            if (!labelFilters.hasOwnProperty(label)) {
                const filterDiv = document.createElement('div');
                filterDiv.className = 'label-filter';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `filter-${label}`;
                checkbox.checked = true;

                const labelElement = document.createElement('label');
                labelElement.htmlFor = `filter-${label}`;
                labelElement.textContent = label;

                filterDiv.appendChild(checkbox);
                filterDiv.appendChild(labelElement);
                filterContainer.appendChild(filterDiv);

                labelFilters[label] = checkbox;

                checkbox.addEventListener('change', function () {
                    const dataset = myChart.data.datasets.find(ds => ds.label === label);
                    if (dataset) {
                        dataset.hidden = !checkbox.checked;
                        myChart.update();
                    }
                });
            }
        });
    }


    // Handle script output (combining both scripts)
    let startTime = null;
    socket.on("script_output", function (data) {
        let outputElement = document.getElementById("output");
        outputElement.textContent += data.output; // Append new output
        outputElement.scrollTop = outputElement.scrollHeight; // Auto scroll to the bottom

        // Split and parse data output
        let parts = data.output.trim().split(":");
        let labels = parts.filter((part, index) => index % 2 === 0).map(label => label.trim()); // Extract labels
        let values = parts.filter((part, index) => index % 2 !== 0).map(value => Number(value.trim()));

        if (startTime === null) {
            startTime = Date.now();
        }

        let currentTime = (Date.now() - startTime) / 1000;

        // Update or add datasets; change with datalabel filters
        labels.forEach((label, index) => {
            let dataset = myChart.data.datasets.find(ds => ds.label === label);
            if (dataset) {
                dataset.data.push({ x: currentTime, y: values[index] });
            } else {
                let color = `rgb(${Math.floor(Math.random() * 255)},${Math.floor(Math.random() * 255)},${Math.floor(Math.random() * 255)})`;
                myChart.data.datasets.push({
                    label: label,
                    data: [{ x: currentTime, y: values[index] }],
                    backgroundColor: color,
                    borderColor: color,
                    borderWidth: 1,
                    fill: false,
                    hidden: labelFilters[label] ? !labelFilterts[label].checked : false
                });
            }
        });

        updateLabelFilter(labels);
        myChart.update();
    });


    // Close confirmation modal
    span.onclick = function () {
        modal.style.display = "none";
    };

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    };
});
