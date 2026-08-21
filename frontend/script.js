// ============================================================
// DEMETER - HISTORY & ANALYTICS
// ============================================================

// Use the same server that served this page.
// This avoids unnecessary CORS problems.
const API_BASE = window.location.origin;

let historyData = [];

let trafficTrendChart = null;
let distributionChart = null;
let flowChart = null;


// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("DEMETER History & Analytics loaded");

    loadFilters();
    loadDashboard();

    const applyButton = document.getElementById("applyFilters");
    const clearButton = document.getElementById("clearFilters");
    const refreshButton = document.getElementById("refreshButton");
    const searchInput = document.getElementById("searchInput");
    const exportCsvButton = document.getElementById("exportCsv");
    const exportExcelButton = document.getElementById("exportExcel");

    if (applyButton) {
        applyButton.addEventListener("click", loadDashboard);
    }

    if (clearButton) {
        clearButton.addEventListener("click", clearFilters);
    }

    if (refreshButton) {
        refreshButton.addEventListener("click", loadDashboard);
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterTable);
    }

    if (exportCsvButton) {
        exportCsvButton.addEventListener("click", exportCSV);
    }

    if (exportExcelButton) {
        exportExcelButton.addEventListener("click", exportExcel);
    }

});


// ============================================================
// FILTERS
// ============================================================

async function loadFilters() {

    try {

        const response = await fetch(
            `${API_BASE}/api/analytics/filters`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        console.log("Filters:", result);

        if (!result.success) {
            console.error("Filter API failed:", result);
            return;
        }

        const locationSelect =
            document.getElementById("locationFilter");

        const modeSelect =
            document.getElementById("modeFilter");

        if (!locationSelect || !modeSelect) {
            return;
        }

        // Reset options
        locationSelect.innerHTML =
            `<option value="all">All Locations</option>`;

        modeSelect.innerHTML =
            `<option value="all">All Modes</option>`;

        // Locations
        (result.locations || []).forEach(location => {

            const option = document.createElement("option");

            option.value = location;
            option.textContent = location;

            locationSelect.appendChild(option);

        });

        // Modes
        (result.modes || []).forEach(mode => {

            const option = document.createElement("option");

            option.value = mode;
            option.textContent = mode;

            modeSelect.appendChild(option);

        });

    }

    catch (error) {

        console.error(
            "Failed to load filters:",
            error
        );

    }

}


// ============================================================
// GET FILTER PARAMETERS
// ============================================================

function getFilterParams() {

    const params = new URLSearchParams();

    const locationElement =
        document.getElementById("locationFilter");

    const modeElement =
        document.getElementById("modeFilter");

    const startDateElement =
        document.getElementById("startDate");

    const endDateElement =
        document.getElementById("endDate");

    const location =
        locationElement ? locationElement.value : "all";

    const mode =
        modeElement ? modeElement.value : "all";

    const startDate =
        startDateElement ? startDateElement.value : "";

    const endDate =
        endDateElement ? endDateElement.value : "";

    if (location && location !== "all") {

        params.append(
            "location",
            location
        );

    }

    if (mode && mode !== "all") {

        params.append(
            "mode",
            mode
        );

    }

    if (startDate) {

        params.append(
            "start_date",
            startDate
        );

    }

    if (endDate) {

        params.append(
            "end_date",
            endDate
        );

    }

    return params;

}


// ============================================================
// LOAD COMPLETE DASHBOARD
// ============================================================

async function loadDashboard() {

    console.log("Loading dashboard...");

    showLoading();

    const params = getFilterParams();

    try {

        await Promise.all([
            loadSummary(params),
            loadTrend(params),
            loadDistribution(params),
            loadFlow(params),
            loadHistory(params)
        ]);

        console.log("Dashboard loaded successfully");

    }

    catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );

    }

}


// ============================================================
// SUMMARY / KPI
// ============================================================

async function loadSummary(params) {

    try {

        const response = await fetch(
            `${API_BASE}/api/analytics/summary?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        console.log("Summary:", data);

        const totalVolume =
            document.getElementById("totalVolume");

        const peakHour =
            document.getElementById("peakHour");

        const emergencyCount =
            document.getElementById("emergencyCount");

        const systemMode =
            document.getElementById("systemMode");

        if (totalVolume) {

            totalVolume.textContent =
                Number(
                    data.total_volume || 0
                ).toLocaleString();

        }

        if (peakHour) {

            peakHour.textContent =
                data.peak_hour || "--";

        }

        if (emergencyCount) {

            emergencyCount.textContent =
                Number(
                    data.emergency_clearances || 0
                ).toLocaleString();

        }

        if (systemMode) {

            systemMode.textContent =
                data.current_mode || "--";

        }

    }

    catch (error) {

        console.error(
            "Summary loading error:",
            error
        );

    }

}


// ============================================================
// TRAFFIC TREND
// ============================================================

async function loadTrend(params) {

    try {

        const response = await fetch(
            `${API_BASE}/api/analytics/trend?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        console.log("Trend:", result);

        if (!result.success) {

            console.error(
                "Trend API failed:",
                result
            );

            return;

        }

        const data = result.data || [];

        const labels = data.map(
            item => item.hour
        );

        const values = data.map(
            item => Number(
                item.vehicle_count || 0
            )
        );

        const canvas =
            document.getElementById(
                "trafficTrendChart"
            );

        if (!canvas) {
            return;
        }

        const ctx =
            canvas.getContext("2d");

        if (trafficTrendChart) {

            trafficTrendChart.destroy();

        }

        trafficTrendChart =
            new Chart(ctx, {

                type: "line",

                data: {

                    labels: labels,

                    datasets: [
                        {
                            label: "Vehicle Volume",

                            data: values,

                            borderColor: "#2563eb",

                            backgroundColor:
                                "rgba(37, 99, 235, 0.10)",

                            borderWidth: 2,

                            fill: true,

                            tension: 0.35,

                            pointRadius: 3,

                            pointHoverRadius: 6
                        }
                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {
                        intersect: false,
                        mode: "index"
                    },

                    plugins: {

                        legend: {
                            display: false
                        }

                    },

                    scales: {

                        y: {

                            beginAtZero: true,

                            grid: {
                                color: "#e2e8f0"
                            }

                        },

                        x: {

                            grid: {
                                display: false
                            }

                        }

                    }

                }

            });

    }

    catch (error) {

        console.error(
            "Trend loading error:",
            error
        );

    }

}


// ============================================================
// TRAFFIC DISTRIBUTION
// ============================================================

async function loadDistribution(params) {

    try {

        const response = await fetch(
            `${API_BASE}/api/analytics/distribution?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        console.log("Distribution:", result);

        if (!result.success) {

            console.error(
                "Distribution API failed:",
                result
            );

            return;

        }

        const data = result.data || [];

        const labels = data.map(
            item => item.location
        );

        const values = data.map(
            item => Number(
                item.vehicle_count || 0
            )
        );

        const canvas =
            document.getElementById(
                "distributionChart"
            );

        if (!canvas) {
            return;
        }

        const ctx =
            canvas.getContext("2d");

        if (distributionChart) {

            distributionChart.destroy();

        }

        distributionChart =
            new Chart(ctx, {

                type: "doughnut",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            data: values,

                            backgroundColor: [
                                "#2563eb",
                                "#7c3aed",
                                "#16a34a",
                                "#ea580c",
                                "#0891b2",
                                "#64748b",
                                "#db2777",
                                "#ca8a04"
                            ],

                            borderWidth: 2,

                            borderColor: "#ffffff"

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    cutout: "68%",

                    plugins: {

                        legend: {
                            display: false
                        }

                    }

                }

            });

        createDistributionLegend(
            labels,
            values
        );

    }

    catch (error) {

        console.error(
            "Distribution loading error:",
            error
        );

    }

}


// ============================================================
// DISTRIBUTION LEGEND
// ============================================================

function createDistributionLegend(
    labels,
    values
) {

    const container =
        document.getElementById(
            "distributionLegend"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    const total =
        values.reduce(
            (sum, value) =>
                sum + Number(value || 0),
            0
        );

    labels.forEach(
        (label, index) => {

            const value =
                Number(
                    values[index] || 0
                );

            const percentage =
                total > 0
                    ? Math.round(
                        (value / total) * 100
                    )
                    : 0;

            const item =
                document.createElement(
                    "span"
                );

            item.className =
                "legend-item";

            item.textContent =
                `${label}: ${percentage}%`;

            container.appendChild(item);

        }
    );

}


// ============================================================
// FLOW ANALYSIS
// ============================================================

async function loadFlow(params) {

    try {

        const response = await fetch(
            `${API_BASE}/api/analytics/flow?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result = await response.json();

        console.log("Flow:", result);

        if (!result.success) {

            console.error(
                "Flow API failed:",
                result
            );

            return;

        }

        const data = result.data || [];

        const labels = data.map(
            item => item.hour
        );

        const inbound = data.map(
            item => Number(
                item.inbound || 0
            )
        );

        const outbound = data.map(
            item => Number(
                item.outbound || 0
            )
        );

        const canvas =
            document.getElementById(
                "flowChart"
            );

        if (!canvas) {
            return;
        }

        const ctx =
            canvas.getContext("2d");

        if (flowChart) {

            flowChart.destroy();

        }

        flowChart =
            new Chart(ctx, {

                type: "line",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            label: "Inbound",

                            data: inbound,

                            borderColor: "#2563eb",

                            backgroundColor:
                                "rgba(37, 99, 235, 0.05)",

                            borderWidth: 2,

                            fill: true,

                            tension: 0.3

                        },

                        {

                            label: "Outbound",

                            data: outbound,

                            borderColor: "#dc2626",

                            backgroundColor:
                                "rgba(220, 38, 38, 0.05)",

                            borderWidth: 2,

                            fill: true,

                            tension: 0.3

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {

                        intersect: false,

                        mode: "index"

                    },

                    plugins: {

                        legend: {
                            position: "bottom"
                        }

                    },

                    scales: {

                        y: {

                            beginAtZero: true

                        },

                        x: {

                            grid: {
                                display: false
                            }

                        }

                    }

                }

            });

    }

    catch (error) {

        console.error(
            "Flow loading error:",
            error
        );

    }

}


// ============================================================
// HISTORY TABLE
// ============================================================

async function loadHistory(params) {

    try {

        const response = await fetch(
            `${API_BASE}/api/history?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const result =
            await response.json();

        console.log("History:", result);

        historyData =
            result.data || [];

        renderTable(historyData);

    }

    catch (error) {

        console.error(
            "History loading error:",
            error
        );

        historyData = [];

        renderTable([]);

    }

}


// ============================================================
// RENDER HISTORY TABLE
// ============================================================

function renderTable(data) {

    const tbody =
        document.getElementById(
            "historyTableBody"
        );

    const emptyState =
        document.getElementById(
            "emptyState"
        );

    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";

    if (!data || data.length === 0) {

        if (emptyState) {
            emptyState.style.display = "block";
        }

        return;

    }

    if (emptyState) {
        emptyState.style.display = "none";
    }

    data.forEach(record => {

        const row =
            document.createElement("tr");

        const timestamp =
            formatDate(
                record.timestamp
            );

        let statusClass =
            "status-normal";

        const eventText =
            String(
                record.event || ""
            ).toLowerCase();

        if (

            record.ambulance === true ||

            String(record.ambulance)
                .toLowerCase() === "true" ||

            eventText.includes("ambulance") ||

            eventText.includes("emergency")

        ) {

            statusClass =
                "status-emergency";

        }

        else if (

            eventText.includes("high") ||

            eventText.includes("congestion") ||

            eventText.includes("warning")

        ) {

            statusClass =
                "status-warning";

        }

        row.innerHTML = `

            <td>
                ${escapeHTML(timestamp)}
            </td>

            <td>
                <strong>
                    ${escapeHTML(record.location)}
                </strong>
            </td>

            <td>
                <span class="status-badge ${statusClass}">
                    ${escapeHTML(record.event)}
                </span>
            </td>

            <td>
                <span class="mode-badge">
                    ${escapeHTML(record.mode)}
                </span>
            </td>

            <td>
                ${Math.round(
                    Number(
                        record.vehicle_count || 0
                    )
                )}
            </td>

            <td>
                ${escapeHTML(
                    record.details || "-"
                )}
            </td>

        `;

        tbody.appendChild(row);

    });

}


// ============================================================
// SEARCH HISTORY
// ============================================================

function filterTable() {

    const input =
        document.getElementById(
            "searchInput"
        );

    if (!input) {
        return;
    }

    const search =
        input.value
            .toLowerCase()
            .trim();

    if (!search) {

        renderTable(historyData);

        return;

    }

    const filtered =
        historyData.filter(
            record => {

                return (

                    String(
                        record.location || ""
                    )
                        .toLowerCase()
                        .includes(search)

                    ||

                    String(
                        record.event || ""
                    )
                        .toLowerCase()
                        .includes(search)

                    ||

                    String(
                        record.mode || ""
                    )
                        .toLowerCase()
                        .includes(search)

                    ||

                    String(
                        record.details || ""
                    )
                        .toLowerCase()
                        .includes(search)

                    ||

                    String(
                        record.timestamp || ""
                    )
                        .toLowerCase()
                        .includes(search)

                );

            }
        );

    renderTable(filtered);

}


// ============================================================
// CLEAR FILTERS
// ============================================================

function clearFilters() {

    const location =
        document.getElementById(
            "locationFilter"
        );

    const mode =
        document.getElementById(
            "modeFilter"
        );

    const startDate =
        document.getElementById(
            "startDate"
        );

    const endDate =
        document.getElementById(
            "endDate"
        );

    const search =
        document.getElementById(
            "searchInput"
        );

    if (location) {
        location.value = "all";
    }

    if (mode) {
        mode.value = "all";
    }

    if (startDate) {
        startDate.value = "";
    }

    if (endDate) {
        endDate.value = "";
    }

    if (search) {
        search.value = "";
    }

    loadDashboard();

}


// ============================================================
// CSV EXPORT
// ============================================================

function exportCSV() {

    if (!historyData.length) {

        alert(
            "No data available to export."
        );

        return;

    }

    const headers = [

        "Timestamp",
        "Location",
        "Event",
        "Mode",
        "Vehicle Count",
        "Car",
        "Bike",
        "Bus",
        "Truck",
        "Ambulance",
        "Traffic Level",
        "Inbound",
        "Outbound",
        "Details"

    ];

    const rows =
        historyData.map(
            record => [

                record.timestamp,
                record.location,
                record.event,
                record.mode,
                record.vehicle_count,
                record.car,
                record.bike,
                record.bus,
                record.truck,
                record.ambulance,
                record.traffic_level,
                record.inbound,
                record.outbound,
                record.details

            ]
        );

    const csv = [

        headers,

        ...rows

    ]

        .map(row =>

            row
                .map(value =>

                    `"${String(
                        value ?? ""
                    ).replace(
                        /"/g,
                        '""'
                    )}"`

                )
                .join(",")

        )

        .join("\n");

    const blob =
        new Blob(
            [csv],
            {
                type:
                    "text/csv;charset=utf-8;"
            }
        );

    const url =
        URL.createObjectURL(blob);

    const link =
        document.createElement("a");

    link.href = url;

    link.download =
        "demeter_traffic_history.csv";

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);

}


// ============================================================
// EXCEL EXPORT
// ============================================================

function exportExcel() {

    if (!historyData.length) {

        alert(
            "No data available to export."
        );

        return;

    }

    // Make sure XLSX library exists
    if (typeof XLSX === "undefined") {

        alert(
            "Excel export library is not loaded."
        );

        return;

    }

    const rows =
        historyData.map(
            record => ({

                Timestamp:
                    record.timestamp,

                Location:
                    record.location,

                Event:
                    record.event,

                Mode:
                    record.mode,

                "Vehicle Count":
                    record.vehicle_count,

                Car:
                    record.car,

                Bike:
                    record.bike,

                Bus:
                    record.bus,

                Truck:
                    record.truck,

                Ambulance:
                    record.ambulance,

                "Traffic Level":
                    record.traffic_level,

                Inbound:
                    record.inbound,

                Outbound:
                    record.outbound,

                Details:
                    record.details

            })
        );

    const worksheet =
        XLSX.utils.json_to_sheet(rows);

    const workbook =
        XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(
        workbook,
        worksheet,
        "Traffic History"
    );

    XLSX.writeFile(
        workbook,
        "demeter_traffic_history.xlsx"
    );

}


// ============================================================
// DATE FORMAT
// ============================================================

function formatDate(timestamp) {

    if (!timestamp) {
        return "--";
    }

    try {

        const date =
            new Date(timestamp);

        if (
            isNaN(
                date.getTime()
            )
        ) {

            return String(timestamp);

        }

        return date.toLocaleString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit"
            }
        );

    }

    catch (error) {

        return String(timestamp);

    }

}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHTML(value) {

    return String(
        value ?? ""
    )

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}


// ============================================================
// LOADING STATE
// ============================================================

function showLoading() {

    const totalVolume =
        document.getElementById(
            "totalVolume"
        );

    const peakHour =
        document.getElementById(
            "peakHour"
        );

    const emergencyCount =
        document.getElementById(
            "emergencyCount"
        );

    const systemMode =
        document.getElementById(
            "systemMode"
        );

    if (totalVolume) {
        totalVolume.textContent = "...";
    }

    if (peakHour) {
        peakHour.textContent = "...";
    }

    if (emergencyCount) {
        emergencyCount.textContent = "...";
    }

    if (systemMode) {
        systemMode.textContent = "...";
    }

}


// ============================================================
// END
// ============================================================

console.log(
    "DEMETER script.js ready | API:",
    API_BASE
);