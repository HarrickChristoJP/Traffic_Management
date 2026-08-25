let map = L.map("map").setView([13.0827, 80.2707], 11);

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 19,
        attribution: "© OpenStreetMap contributors"
    }
).addTo(map);


let routeLayer = null;
let markerLayer = null;


// IMPORTANT: Connect button to function
document
    .getElementById("track-button")
    .addEventListener("click", trackVehicle);


async function trackVehicle() {

    const vehicleNumber = document
        .getElementById("vehicle-number")
        .value
        .trim()
        .toUpperCase();

    if (!vehicleNumber) {
        alert("Please enter a vehicle number");
        return;
    }

    try {

        const response = await fetch(`/track/${vehicleNumber}`);

        const data = await response.json();

        if (!data || data.length === 0) {
            alert("No vehicle records found");
            return;
        }


        // Remove previous route and markers
        if (routeLayer) {
            map.removeLayer(routeLayer);
        }

        if (markerLayer) {
            map.removeLayer(markerLayer);
        }


        markerLayer = L.layerGroup().addTo(map);

        const coordinates = [];


        // Add markers dynamically
        data.forEach((location, index) => {

    const lat = location.latitude;
    const lng = location.longitude;

    coordinates.push([lat, lng]);

    let label;
    let markerColor;

    // Dynamic labels and colors
    if (index === 0) {
        label = "START";
        markerColor = "green";
    }
    else if (index === data.length - 1) {
        label = "END";
        markerColor = "red";
    }
    else {
        label = `S${index}`;
        markerColor = "blue";
    }

    // Create marker
    const marker = L.circleMarker([lat, lng], {
        radius: 11,
        color: markerColor,
        fillColor: markerColor,
        fillOpacity: 1,
        weight: 3
    })
    .addTo(markerLayer)
    .bindPopup(`
        <div class="signal-popup">
            <h3>${label}</h3>
            <p><b>Signal:</b> ${location.signal_name}</p>
            <p><b>Time:</b> ${location.timestamp}</p>
        </div>
    `);

    // Permanent label
    marker.bindTooltip(
        `${label}: ${location.signal_name}`,
        {
            permanent: true,
            direction: "top",
            offset: [0, -15],
            className: `signal-label ${label.toLowerCase()}`
        }
    );

});


        // Draw route only when there are 2 or more locations
        if (coordinates.length >= 2) {

            routeLayer = L.polyline(coordinates, {
                color: "blue",
                weight: 5
            }).addTo(map);


            map.fitBounds(routeLayer.getBounds(), {
                padding: [50, 50]
            });

        }
        else {

            // Only one signal detected
            map.setView(coordinates[0], 15);

        }

    }
    catch (error) {

        console.error(error);

        alert("Error while tracking vehicle");

    }

}
