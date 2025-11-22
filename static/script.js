let waitChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    setInterval(pollState, 100); // Poll every 100ms
});

function initChart() {
    const ctx = document.getElementById('waitChart').getContext('2d');
    waitChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Avg Wait Time (I1)',
                data: [],
                borderColor: '#3498db',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#444' }
                },
                x: {
                    grid: { color: '#444' }
                }
            }
        }
    });
}

async function controlSim(action) {
    await fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
    });
}

async function pollState() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();
        updateUI(data);
    } catch (e) {
        console.error("Polling error:", e);
    }
}

function updateUI(data) {
    // Update Status
    document.getElementById('status').textContent = `Status: ${data.running ? 'Running' : 'Stopped'}`;
    document.getElementById('step').textContent = `Step: ${data.step}`;
    document.getElementById('lastAction').textContent = data.last_action;

    // Render Intersections
    const container = document.getElementById('intersections');
    // Simple diffing: if empty, create. Else update.
    // For simplicity, we just clear and rebuild if IDs change, or update in place.
    // Let's just rebuild for this demo or find existing elements.
    
    Object.values(data.intersections).forEach(intersection => {
        let card = document.getElementById(`int-${intersection.intersection_id}`);
        if (!card) {
            card = document.createElement('div');
            card.id = `int-${intersection.intersection_id}`;
            card.className = 'intersection-card';
            container.appendChild(card);
        }
        
        // Update Content
        const phaseClass = intersection.current_phase;
        const queues = intersection.queue_lengths;
        
        card.innerHTML = `
            <h3>${intersection.intersection_id}</h3>
            <div class="traffic-light ${phaseClass}">
                ${intersection.current_phase}<br>
                ${intersection.phase_elapsed}s
            </div>
            <div class="queues">
                <div class="queue-item">N: ${queues.N}</div>
                <div class="queue-item">S: ${queues.S}</div>
                <div class="queue-item">E: ${queues.E}</div>
                <div class="queue-item">W: ${queues.W}</div>
            </div>
            <p>Avg Wait: ${intersection.avg_wait}s</p>
        `;
    });

    // Update Chart
    if (data.history.length > 0) {
        const labels = data.history.map(h => h.step);
        const values = data.history.map(h => h.avg_wait);
        
        waitChart.data.labels = labels;
        waitChart.data.datasets[0].data = values;
        waitChart.update('none'); // 'none' mode for performance
    }
}
