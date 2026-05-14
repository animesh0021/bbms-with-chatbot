// static/js/charts.js
// Final version – prevents infinite expansion and multiple initialisations

const chartInstances = {};

document.addEventListener('DOMContentLoaded', function() {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js library is not loaded.');
        return;
    }

    // Initialise each chart only once per canvas
    safeInit('inventoryChart', initInventoryChart);
    safeInit('donorTrendChart', initDonorTrendChart);
    safeInit('requestPieChart', initRequestPieChart);
    safeInit('donorDistributionChart', initDonorDistributionChart);
    safeInit('inventoryVsRequestChart', initInventoryVsRequestChart);
});

/**
 * Initialise a chart only once per canvas.
 * Uses a custom attribute 'data-chart-initialised' to track state.
 */
function safeInit(canvasId, initFn) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    if (canvas.getAttribute('data-chart-initialised') === 'true') {
        // console.log(`Chart ${canvasId} already initialised, skipping.`);
        return;
    }
    initFn().then(() => {
        canvas.setAttribute('data-chart-initialised', 'true');
    }).catch(err => {
        console.error(`Failed to initialise ${canvasId}:`, err);
    });
}

/**
 * Fetch JSON data from an endpoint.
 */
async function fetchChartData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Fetch failed: ${url}`, error);
        return null;
    }
}

/**
 * Create a new chart or replace an existing one.
 * Ensures only one Chart instance exists per canvas.
 */
function createOrUpdateChart(canvasId, type, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    // Destroy previous instance if any
    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    const ctx = canvas.getContext('2d');
    chartInstances[canvasId] = new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,           // Disable animations to prevent resize loops
            ...options
        }
    });
    return chartInstances[canvasId];
}

/**
 * Display an error message inside the canvas container.
 */
function showChartError(canvasId, message) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const parent = canvas.parentNode;
    const existing = parent.querySelector('.chart-error');
    if (existing) existing.remove();

    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-warning text-center chart-error';
    errorDiv.textContent = message;
    parent.insertBefore(errorDiv, canvas);
    canvas.style.display = 'none';
}

// ----------------------------------------------------------------------
// Individual chart initialisers (each returns a Promise)
// ----------------------------------------------------------------------

async function initInventoryChart() {
    const data = await fetchChartData('/api/charts/inventory');
    if (!data) {
        showChartError('inventoryChart', 'Unable to load inventory data.');
        return;
    }
    createOrUpdateChart('inventoryChart', 'bar', {
        labels: data.labels,
        datasets: [{
            label: 'Units Available',
            data: data.values,
            backgroundColor: 'rgba(220, 53, 69, 0.7)',
            borderColor: 'rgba(220, 53, 69, 1)',
            borderWidth: 1
        }]
    }, {
        scales: { y: { beginAtZero: true, title: { display: true, text: 'Units' } } },
        plugins: { legend: { display: false } }
    });
}

async function initDonorTrendChart() {
    const data = await fetchChartData('/api/charts/donor_trend');
    if (!data) {
        showChartError('donorTrendChart', 'Unable to load donor trend data.');
        return;
    }
    createOrUpdateChart('donorTrendChart', 'line', {
        labels: data.labels,
        datasets: [{
            label: 'New Donors',
            data: data.values,
            fill: false,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        }]
    }, {
        scales: { y: { beginAtZero: true, title: { display: true, text: 'Donors' } } }
    });
}

async function initRequestPieChart() {
    const data = await fetchChartData('/api/charts/requests');
    if (!data) {
        showChartError('requestPieChart', 'Unable to load request data.');
        return;
    }
    createOrUpdateChart('requestPieChart', 'pie', {
        labels: data.labels,
        datasets: [{
            data: data.values,
            backgroundColor: [
                'rgba(255, 206, 86, 0.7)',
                'rgba(75, 192, 192, 0.7)',
                'rgba(255, 99, 132, 0.7)'
            ],
            borderColor: [
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 1
        }]
    }, {
        plugins: { legend: { position: 'bottom' } }
    });
}

async function initDonorDistributionChart() {
    const data = await fetchChartData('/api/charts/donor_distribution');
    if (!data) {
        showChartError('donorDistributionChart', 'Unable to load donor distribution data.');
        return;
    }
    createOrUpdateChart('donorDistributionChart', 'bar', {
        labels: data.labels,
        datasets: [{
            label: 'Number of Donors',
            data: data.values,
            backgroundColor: 'rgba(54, 162, 235, 0.7)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    }, {
        scales: { y: { beginAtZero: true, title: { display: true, text: 'Donors' } } }
    });
}

async function initInventoryVsRequestChart() {
    const data = await fetchChartData('/api/charts/inventory_vs_request');
    if (!data) {
        showChartError('inventoryVsRequestChart', 'Unable to load comparison data.');
        return;
    }
    createOrUpdateChart('inventoryVsRequestChart', 'bar', {
        labels: data.labels,
        datasets: [
            {
                label: 'Available Units',
                data: data.inventory,
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            },
            {
                label: 'Requested Units',
                data: data.requests,
                backgroundColor: 'rgba(255, 99, 132, 0.7)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }
        ]
    }, {
        scales: { y: { beginAtZero: true, title: { display: true, text: 'Units' } } }
    });
}