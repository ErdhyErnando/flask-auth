// Constants and Initialization
const DOMAIN = document.domain;
const PORT = location.port;

const WINDOW_DURATION = 5; // Duration of visible data in seconds

// DOM Elements
const elements = {
    fileExplorerModal: document.getElementById('fileExplorerModal'),
    fileExplorer: document.getElementById('fileExplorer'),
    chooseFileLabel: document.getElementById('chooseFileLabel'),
    selectedFileDisplay: document.getElementById('selectedFileDisplay'),
    logButton: document.getElementById('logButton'),
    paramContainer: document.getElementById('paramContainer'),
    addParamButton: document.getElementById('addParamButton'),
    startButton: document.getElementById("startButton"),
    stopButton: document.getElementById("stopButton"),
    modal: document.getElementById("commandModal"),
    confirmButton: document.getElementById("confirmButton"),
    commandText: document.getElementById("commandText"),
    output: document.getElementById("output"),
    labelFilters: document.getElementById('labelFilters'),
    trialCount: document.getElementById('trialCount'),
    buttonPressCount: document.getElementById('buttonPressCount'),
    errorCount: document.getElementById('errorCount'),
    flexExt: document.getElementById('flexExt')
};

// Global Variables
let myChart;
let socket;
let selectedFile = '';
let labelFilters = {};
let startTime = null;
let basePath;
let fullDataSets = {};
let trialCount = -1;
let buttonPressCount = 0;
let errorCount = 0;
let previousButtonState = 0;
let previousDisturbIntroState = 0;

// Chart Configuration
const chartConfig = {
    type: 'line',
    data: { datasets: [] },
    options: {
        animation: false,
        responsive: true,
        scales: {
            x: {
                type: 'linear',
                position: 'bottom',
                title: {
                    display: true,
                    text: 'Time (seconds)',
                    font: { size: 10 }
                },
                ticks: {
                    callback: value => value.toFixed(1) + 's',
                    font: { size: 8 }
                },
                min: 0,
                max: WINDOW_DURATION
            },
            y: {
                type: 'linear',
                position: 'left',
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Values',
                    font: { size: 10 }
                },
                ticks: { font: { size: 8 } }
            }
        },
        plugins: {
            legend: {
                labels: {
                    display: true,
                    font: { size: 10 },
                    filter: (legendItem, data) =>
                        labelFilters[legendItem.text] ? labelFilters[legendItem.text].checked : true
                }
            }
        }
    }
};

/**
 * Initializes the chart using Chart.js library.
 */
function initializeChart() {
    const ctx = document.getElementById('myChart').getContext('2d');
    myChart = new Chart(ctx, chartConfig);
}

/**
 * Initializes the WebSocket connection.
 */
function initializeSocket() {
    socket = io.connect(`http://${DOMAIN}:${PORT}`);
    setupSocketListeners();
}

/**
 * Sets up WebSocket event listeners.
 */
function setupSocketListeners() {
    socket.on("logging_complete", data => {
        console.log("logging complete", data.message);
        alert(data.message);
    });

    socket.on("script_stopped", () => {
        elements.output.textContent += "Script stopped by user\n";
    });

    socket.on("script_output", handleScriptOutput);

    socket.on('sudo_command_result', handleSudoCommandResult);
}

/**
 * Creates the file explorer structure in the DOM.
 * @param {Object[]} structure - The file/folder structure to display.
 * @param {HTMLElement} parentElement - The parent element to append the structure to.
 * @param {string} [path=basePath] - The current path in the file structure.
 */
function createFileExplorer(structure, parentElement, path = basePath) {
    structure.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.classList.add('file-explorer-item');

        if (item.type === 'folder') {
            itemElement.innerHTML = `<span class="folder-icon">📁</span> ${item.name}`;
            itemElement.classList.add('folder');
            const childrenContainer = document.createElement('div');
            childrenContainer.classList.add('folder-children');
            childrenContainer.style.display = 'none';
            createFileExplorer(item.children, childrenContainer, `${path}/${item.name}`);
            itemElement.appendChild(childrenContainer);

            itemElement.addEventListener('click', e => {
                e.stopPropagation();
                childrenContainer.style.display = childrenContainer.style.display === 'none' ? 'block' : 'none';
            });
        } else {
            const fileIcon = item.name.endsWith('.py') ? '🐍' : '📄';
            itemElement.innerHTML = `<span class="file-icon">${fileIcon}</span> ${item.name}`;
            itemElement.classList.add('file');
            itemElement.addEventListener('click', e => {
                e.stopPropagation();
                selectedFile = `${path}/${item.name}`;
                elements.selectedFileDisplay.textContent = item.name;
                elements.fileExplorerModal.style.display = 'none';
            });
        }

        parentElement.appendChild(itemElement);
    });
}

/**
 * Logs the selected data to the server.
 */
function logData() {
    const selectedLabels = Object.keys(labelFilters).filter(label => labelFilters[label].checked);
    const dataToLog = {};
    selectedLabels.forEach(label => {
        if (fullDataSets[label]) {
            dataToLog[label] = fullDataSets[label];
        }
    });

    const params = {};
    $('.param-input').each((index, element) => {
        const paramValue = element.value;
        if (paramValue !== "") {
            params[element.id] = paramValue;
        }
    });

    socket.emit("log_data", {
        data: dataToLog,
        filename: selectedFile,
        params: params
    });
}

/**
 * Resets all counters and updates the corresponding DOM elements.
 */
function resetCounters() {
    trialCount = -1;
    buttonPressCount = 0;
    errorCount = 0;
    elements.trialCount.textContent = '0';
    elements.buttonPressCount.textContent = '0';
    elements.errorCount.textContent = '0';
    elements.flexExt.textContent = '0.00';
}

/**
 * Increments the button press count and updates the DOM.
 */
function updateButtonPressCount() {
    buttonPressCount++;
    elements.buttonPressCount.textContent = buttonPressCount;
}

/**
 * Increments the error count and updates the DOM.
 */
function updateErrorCount() {
    errorCount++;
    elements.errorCount.textContent = errorCount;
}

/**
 * Handles the start button click event.
 * @param {Event} event - The click event object.
 */
function handleStartButtonClick(event) {
    event.preventDefault();
    if (!selectedFile) {
        alert('Please select a file');
        return;
    }

    const params = {};

    $('.param-input').each((index, element) => {
        params[element.id] = element.value;
        if (element.value.trim().startsWith('-n')) {
            const parts = element.value.trim().split(/\s+/);
            if (parts.length > 1) {
                const parsedValue = parseInt(parts[1]);
                if (!isNaN(parsedValue)) {
                    errorCount = parsedValue;
                    elements.errorCount.textContent = errorCount;
                } else {
                    console.warn(`Invalid value for -n flag: ${parts[1]}`);
                    // Optionally, show a warning to the user
                    alert(`Invalid value for -n flag: ${parts[1]}`);
                }
            } else {
                console.warn('-n flag used without a value');
                // Optionally, show a warning to the user
                alert('-n flag used without a value');
            }
        }
    });

    const paramStr = Object.values(params)
        .filter(value => value !== "")
        .join("  ");

    const filename = selectedFile.split('/').pop();
    const command = `python3 ${filename} ${paramStr}`;
    elements.commandText.textContent = command;
    elements.modal.style.display = "block";

    // Reset full data sets
    fullDataSets = {};
}

/**
 * Handles the confirm button click event in the command modal.
 */
function handleConfirmButtonClick() {
    const params = {};
    $('.param-input').each((index, element) => {
        params[element.id] = element.value;
    });

    resetCounters();

    elements.output.textContent = "";
    elements.labelFilters.innerHTML = '';
    labelFilters = {};

    startTime = null;
    myChart.data.datasets = [];
    myChart.update();

    socket.emit("start_script", { filename: selectedFile, params: params });
    elements.modal.style.display = "none";
}

/**
 * Handles the stop button click event.
 * @param {Event} event - The click event object.
 */
function handleStopButtonClick(event) {
    event.preventDefault();
    socket.emit("stop_script");
    elements.output.textContent = "";
    startTime = null;
    myChart.data.datasets = [];
    myChart.update();

    resetCounters();
}

/**
 * Updates the label filter checkboxes based on the received data labels.
 * @param {string[]} labels - The data labels to create filters for.
 */
function updateLabelFilter(labels) {
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
            elements.labelFilters.appendChild(filterDiv);

            labelFilters[label] = checkbox;

            checkbox.addEventListener('change', () => {
                const dataset = myChart.data.datasets.find(ds => ds.label === label);
                if (dataset) {
                    dataset.hidden = !checkbox.checked;
                    myChart.update();
                }
            });
        }
    });
}

/**
 * Updates the chart legend based on the current label filter states.
 */
function updateChartLegend() {
    myChart.options.plugins.legend.labels.filter = (legendItem, data) =>
        labelFilters[legendItem.text] ? labelFilters[legendItem.text].checked : true;
}

/**
 * Handles the script output received from the server.
 * @param {Object} data - The output data object.
 */
function handleScriptOutput(data) {
    // Format the output for display
    const formattedOutput = formatOutputForDisplay(data.output);
    elements.output.textContent += formattedOutput + '\n';
    elements.output.scrollTop = elements.output.scrollHeight;

    const parts = data.output.trim().split(":");
    const labels = [];
    const values = [];

    for (let i = 0; i < parts.length - 1; i += 2) {
        const label = parts[i].trim();
        const value = parts[i + 1].trim();

        if (label === 'new_trial' && value === '100') {
            trialCount++;
            elements.trialCount.textContent = trialCount;
        } else if (label === 'flex_ext') {
            elements.flexExt.textContent = value;
        } else if (label === 'is_pressed') {
            const newButtonState = value === '100' ? 1 : 0;
            if (newButtonState !== previousButtonState && newButtonState === 1) {
                updateButtonPressCount();
            }
            previousButtonState = newButtonState;
        } else if (label === 'err_count') {
            errorCount = parseInt(value);
            elements.errorCount.textContent = errorCount;
        }

        if (label !== 'err_count') {
            labels.push(label);
            values.push(value);
        }
    }

    if (startTime === null) {
        startTime = Date.now();
    }

    const currentTime = (Date.now() - startTime) / 1000;

    labels.forEach((label, index) => {
        let dataset = myChart.data.datasets.find(ds => ds.label === label);
        const newDataPoint = { x: currentTime, y: values[index] };

        if (dataset) {
            // Add to full data sets
            if (!fullDataSets[label]) {
                fullDataSets[label] = [];
            }
            fullDataSets[label].push(newDataPoint);

            // Add to visible data set
            dataset.data.push(newDataPoint);

            // remove data points outside the visible window
            dataset.data = dataset.data.filter(point => point.x >= currentTime - WINDOW_DURATION);
        } else {
            const color = `rgb(${Math.floor(Math.random() * 255)},${Math.floor(Math.random() * 255)},${Math.floor(Math.random() * 255)})`;
            myChart.data.datasets.push({
                label: label,
                data: [newDataPoint],
                backgroundColor: color,
                borderColor: color,
                borderWidth: 1,
                fill: false,
                hidden: labelFilters[label] ? !labelFilters[label].checked : false
            });

            fullDataSets[label] = [newDataPoint];
        }
    });

    // adjust x-axis scale to show the sliding window
    myChart.options.scales.x.min = Math.max(0, currentTime - WINDOW_DURATION);
    myChart.options.scales.x.max = currentTime;

    updateLabelFilter(labels);
    updateChartLegend();
    myChart.update();
}

/**
 * Formats the output for display by limiting decimal places for certain values and seperate values using ';'.
 * @param {string} output - The raw output string.
 * @returns {string} The formatted output string.
 */
function formatOutputForDisplay(output) {
    const parts = output.trim().split(":");
    const formattedParts = [];

    for (let i = 0; i < parts.length - 1; i += 2) {
        const label = parts[i].trim();
        const value = parts[i + 1].trim();

        if (label === 'orth_pos') {
            // Limit orth_pos to 2 decimal places
            formattedParts.push(`${label}:${parseFloat(value).toFixed(2)}`);
        } else {
            formattedParts.push(`${label}:${value}`);
        }
    }

    return formattedParts.join(';');
}

/**
 * Sets up all event listeners for the application.
 */
function setupEventListeners() {
    elements.chooseFileLabel.addEventListener('click', () => {
        elements.fileExplorerModal.style.display = 'block';
    });

    document.querySelectorAll('.close').forEach(button => {
        button.addEventListener('click', () => {
            elements.fileExplorerModal.style.display = 'none';
        });
    });

    elements.fileExplorer.addEventListener('click', e => {
        if (e.target.classList.contains('file')) {
            const fileName = e.target.textContent.trim();
            const filePath = e.target.closest('.folder-children') ?
                e.target.closest('.folder-children').previousSibling.textContent.trim() + '/' + fileName :
                fileName;
            selectedFile = filePath;
            elements.selectedFileDisplay.textContent = fileName;
            elements.fileExplorerModal.style.display = 'none';
        }
    });

    $(document).on('click', '.add-param-button', () => {
        const currentParams = $('.param-input').length;
        const newParamEnd = Math.min(currentParams + 1, 20);

        for (let i = currentParams + 1; i <= newParamEnd; i++) {
            const newParam = $('<div class="param-wrapper"></div>');
            newParam.append(`<input type="text" class="param-input" id="param${i}" name="param${i}" placeholder="Param ${i}">`);

            if (i > 5) {
                newParam.append(`<button class="delete-param-button" data-param="param${i}">×</button>`);
            }

            newParam.insertBefore('.add-param-button');
        }
    });

    $(document).on('click', '.delete-param-button', function () {
        if ($('.param-input').length > 5) {
            $(this).parent('.param-wrapper').remove();
            renumberParams();
        }
    });

    elements.logButton.addEventListener('click', logData);
    elements.startButton.addEventListener("click", handleStartButtonClick);
    elements.confirmButton.addEventListener("click", handleConfirmButtonClick);
    elements.stopButton.addEventListener("click", handleStopButtonClick);

    window.onclick = event => {
        if (event.target == elements.modal) {
            elements.modal.style.display = "none";
        }
    };

    const sudoButton = document.getElementById('sudoButton');
    sudoButton.addEventListener('click', handleSudoButtonClick);
}

/**
 * Renumbers the parameter input fields after deletion.
 */
function renumberParams() {
    $('.param-wrapper').each((index, wrapper) => {
        const paramNumber = index + 1;
        const input = $(wrapper).find('.param-input');
        input.attr('id', `param${paramNumber}`);
        input.attr('name', `param${paramNumber}`);
        input.attr('placeholder', `Param ${paramNumber}`);

        const deleteButton = $(wrapper).find('.delete-param-button');
        if (deleteButton.length) {
            deleteButton.attr('data-param', `param${paramNumber}`);
        }
    });
}

// Main Initialization
document.addEventListener("DOMContentLoaded", () => {
    initializeChart();
    initializeSocket();
    setupEventListeners();
    resetCounters();

    fetch('/get_file_structure')
        .then(response => response.json())
        .then(data => {
            basePath = data.base_path;
            createFileExplorer(data.structure, elements.fileExplorer, basePath);
        });
});

/**
 * Handles the Sudo button click event.
 * @param {Event} event - The click event object.
 */
function handleSudoButtonClick(event) {
    event.preventDefault();
    socket.emit('run_sudo_command');
}

/**
 * Handles the result of a sudo command execution.
 * @param {Object} data - The result data object.
 * @param {boolean} data.success - Indicates if the command was successful.
 * @param {string} data.message - The result message.
 */
function handleSudoCommandResult(data) {
    if (data.success) {
        alert('Success: ' + data.message);
    } else {
        alert('Error: ' + data.message);
    }
}