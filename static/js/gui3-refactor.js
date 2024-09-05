// Constants and Initialization
const DOMAIN = document.domain;
const PORT = location.port;

const WINDOW_DURATION = 2; // Duration of visible data in seconds

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
    labelFilters: document.getElementById('labelFilters')
};

// Global Variables
let myChart;
let socket;
let selectedFile = '';
let labelFilters = {};
let startTime = null;
let basePath;
let fullDataSets = {};

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

// Functions
function initializeChart() {
    const ctx = document.getElementById('myChart').getContext('2d');
    myChart = new Chart(ctx, chartConfig);
}

function initializeSocket() {
    socket = io.connect(`http://${DOMAIN}:${PORT}`);
    setupSocketListeners();
}

function setupSocketListeners() {
    socket.on("logging_complete", data => {
        console.log("logging complete", data.message);
        alert(data.message);
    });

    socket.on("script_stopped", () => {
        elements.output.textContent += "Script stopped by user\n";
    });

    socket.on("script_output", handleScriptOutput);
}

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

function handleStartButtonClick(event) {
    event.preventDefault();
    if (!selectedFile) {
        alert('Please select a file');
        return;
    }

    const params = {};
    $('.param-input').each((index, element) => {
        params[element.id] = element.value;
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

function handleConfirmButtonClick() {
    const params = {};
    $('.param-input').each((index, element) => {
        params[element.id] = element.value;
    });

    elements.output.textContent = "";
    elements.labelFilters.innerHTML = '';
    labelFilters = {};

    startTime = null;
    myChart.data.datasets = [];
    myChart.update();

    socket.emit("start_script", { filename: selectedFile, params: params });
    elements.modal.style.display = "none";
}

function handleStopButtonClick(event) {
    event.preventDefault();
    socket.emit("stop_script");
    elements.output.textContent = "";
    startTime = null;
    myChart.data.datasets = [];
    myChart.update();
}

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

function updateChartLegend() {
    myChart.options.plugins.legend.labels.filter = (legendItem, data) =>
        labelFilters[legendItem.text] ? labelFilters[legendItem.text].checked : true;
    myChart.update();
}

function handleScriptOutput(data) {
    elements.output.textContent += data.output;
    elements.output.scrollTop = elements.output.scrollHeight;

    const parts = data.output.trim().split(":");
    const labels = [];
    const values = [];

    for (let i = 0; i < parts.length - 1; i += 2) {
        labels.push(parts[i].trim());
        values.push(Number(parts[i + 1].trim()));
    }

    if (startTime === null) {
        startTime = Date.now();
    }

    const currentTime = (Date.now() - startTime) / 1000;

    labels.forEach((label, index) => {
        let dataset = myChart.data.datasets.find(ds => ds.label === label);
        const newDataPoint = { x: currentTime, y: values[index] };

        if (dataset) {
            // Add to full data set
            if (!fullDataSets[label]) {
                fullDataSets[label] = [];
            }
            fullDataSets[label].push(newDataPoint);

            // Add to visible data set
            dataset.data.push(newDataPoint);

            // Remove data points outside the visible window
            dataset.data = dataset.data.filter(point => point.x >= currentTime - WINDOW_DURATION);
        } else {
            const color = `rgb(${Math.floor(Math.random() * 255)},${Math.floor(Math.random() * 255)},${Math.floor(Math.random() * 255)})`;
            myChart.data.datasets.push({
                label: label,
                data: [{ x: currentTime, y: values[index] }],
                backgroundColor: color,
                borderColor: color,
                borderWidth: 1,
                fill: false,
                hidden: labelFilters[label] ? !labelFilters[label].checked : false
            });

            fullDataSets[label] = [{ x: currentTime, y: values[index] }];
        }
    });

    // adjust x-axis scale to show the sliding window
    myChart.options.scales.x.min = Math.max(0, currentTime - WINDOW_DURATION);
    myChart.options.scales.x.max = currentTime;

    updateLabelFilter(labels);
    updateChartLegend();
    myChart.update();
}

// Event Listeners
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
}

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

    fetch('/get_file_structure')
        .then(response => response.json())
        .then(data => {
            basePath = data.base_path;
            createFileExplorer(data.structure, elements.fileExplorer, basePath);
        });
});