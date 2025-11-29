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
            datasets: [
                {
                    label: 'Total Cars Waiting',
                    data: [],
                    borderColor: '#e74c3c',
                    tension: 0.1,
                    yAxisID: 'y'
                },
                {
                    label: 'Avg Wait Time (s)',
                    data: [],
                    borderColor: '#3498db',
                    tension: 0.1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: '#444' },
                    title: { display: true, text: 'Cars' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    title: { display: true, text: 'Seconds' }
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

async function setMode(mode) {
    await fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'set_mode', mode })
    });

    // Update UI buttons
    document.getElementById('modeAiBtn').classList.toggle('active', mode === 'AI');
    document.getElementById('modeBaseBtn').classList.toggle('active', mode === 'BASELINE');
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

    // Update Mode Buttons (sync with server state)
    document.getElementById('modeAiBtn').classList.toggle('active', data.mode === 'AI');
    document.getElementById('modeBaseBtn').classList.toggle('active', data.mode === 'BASELINE');

    // Render Intersections
    const container = document.getElementById('intersections');

    Object.values(data.intersections).forEach(intersection => {
        let card = document.getElementById(`int-${intersection.id}`);
        if (!card) {
            card = document.createElement('div');
            card.id = `int-${intersection.id}`;
            card.className = 'intersection-card';
            container.appendChild(card);
        }

        // Update Content
        const phaseClass = intersection.phase;
        const queues = intersection.queues; // Now it's a dict {N: ..., S: ...} or similar? 
        // Wait, get_state returns 'queues': {k: v.get_queue_length() ...} where k is 'N', 'S'...
        // Let's verify keys. Lane keys are 'N', 'S', 'E', 'W'.

        // Note: In server.py we updated get_state to return 'queues' dict.

        card.innerHTML = `
            <h3>${intersection.id}</h3>
            <div class="traffic-light ${phaseClass}">
                ${intersection.phase}<br>
                ${intersection.phase_timer}s
            </div>
            <div class="queues">
                <div class="queue-item">N: ${queues.N || 0}</div>
                <div class="queue-item">S: ${queues.S || 0}</div>
                <div class="queue-item">E: ${queues.E || 0}</div>
                <div class="queue-item">W: ${queues.W || 0}</div>
            </div>
            <p>Avg Wait: ${intersection.avg_waiting_time.toFixed(1)}s</p>
        `;
    });

    // Update Chart
    if (data.history.length > 0) {
        const labels = data.history.map(h => h.step);
        const waitValues = data.history.map(h => h.avg_wait);
        const queueValues = data.history.map(h => h.total_queue);

        waitChart.data.labels = labels;
        waitChart.data.datasets[0].data = queueValues;
        waitChart.data.datasets[1].data = waitValues;
        waitChart.update('none');
    }

    // Render Logs
    const logsContainer = document.getElementById('logsContainer');
    if (data.logs && logsContainer) {
        // Reverse logs to show newest first
        const logsHtml = data.logs.slice().reverse().map(log => `
            <div class="log-entry">
                <span class="log-step">[Step ${log.step}]</span>
                <span class="log-agent">${log.agent}</span>:
                <span class="log-decision ${log.decision}">${log.decision}</span>
                <div class="log-reason">${log.reasoning}</div>
            </div>
        `).join('');
        logsContainer.innerHTML = logsHtml;
    }
}
