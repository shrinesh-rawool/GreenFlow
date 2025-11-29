# Traffic Simulator Project Documentation

## Overview
This project is a modular, extensible traffic simulation platform designed to demonstrate the effectiveness of AI-driven traffic control compared to static timers. It follows a structured 5-Phase architecture to separate simulation, agent logic, orchestration, and observability.

## Project Goal
The primary goal is to create a "world" (simulation) where intelligent agents can observe traffic conditions and make real-time decisions to optimize flow, proving that dynamic control outperforms static timing.

## Architecture: The 5 Phases

### Phase 1: The Foundation (Simulation & Tools)
The core of the project is a robust Python-based discrete-time simulator.
- **`TrafficIntersection` (in `traffic_simulator.py`)**: Acts as the "Real World". It holds the state of queues (`north_queue`, etc.) and phases.
- **Tools**: The simulator exposes tool-like methods for agents:
    - `get_traffic_status(intersection_id)`: Returns current queue lengths.
    - `execute_signal_change(intersection_id, action)`: Switches or holds the light.

### Phase 2: Agent Architecture (The "Brain")
The system uses three distinct agent types to separate concerns:
1.  **Observer Agent (`observer_agent.py`)**: The "Eyes".
    -   Reads raw queue data.
    -   Flags intersections as **CRITICAL** if any queue exceeds 20 cars.
    -   Produces a structured summary for the Controller.
2.  **Controller Agent (`controller_agent.py`)**: The "Brain".
    -   Receives the Observer's summary.
    -   Applies logic:
        -   **Switch**: If Green < 5 cars AND Red > 15 cars.
        -   **Critical**: Prioritize CRITICAL lanes immediately.
    -   Calls `execute_signal_change`.
3.  **Coordinator Agent (`coordinator_agent.py`)**: The "Boss".
    -   Runs every 5 steps.
    -   Monitors multiple intersections.
    -   Injects "Context Updates" (e.g., bias downstream lights) to prevent gridlock.

### Phase 3: Orchestration & Workflow
The `server.py` script manages the main simulation loop, ensuring a strict sequence of events:
1.  **Start Step**: `sim.step()` adds random cars.
2.  **Observe Step**: Observer reads state.
3.  **Decide Step**: Controller makes decisions based on observations and Coordinator context.
4.  **Metric Step**: State is logged for the dashboard.

### Phase 4: Observability & Evaluation
The project includes a web-based dashboard for real-time monitoring and comparison.
-   **Modes**:
    -   **AI Mode**: Agents control the lights dynamically.
    -   **Baseline Mode**: Static timer switches lights every 30 seconds.
-   **Dashboard Features**:
    -   **Live Visualization**: Traffic lights and queue counts for each intersection.
    -   **Charts**: Real-time graph of "Total Cars Waiting" vs "Avg Wait Time".
    -   **Decision Logs**: A scrolling panel showing every decision made by the agents and their reasoning.

### Phase 5: Verification
A verification script (`verify_simulation.py`) ensures the system works as expected by running the loop programmatically and checking for log generation and correct state transitions.

## How to Run

### Prerequisites
- Python 3.x
- Flask (`pip install flask`)

### Running the Dashboard
1.  Navigate to the project directory:
    ```bash
    cd /home/shrinesh/antigravity_test/traffic_agent
    ```
2.  Start the server:
    ```bash
    python3 server.py
    ```
3.  Open your browser to `http://127.0.0.1:5000`.

### Using the Dashboard
1.  **Select Mode**: Choose "AI Mode" or "Baseline (Timer)".
2.  **Start**: Click the Start button to begin the simulation.
3.  **Observe**: Watch the queues, charts, and decision logs to see the difference in performance.

## Key Files
-   `traffic_simulator.py`: Core simulation logic.
-   `server.py`: Main loop and Flask server.
-   `observer_agent.py`, `controller_agent.py`, `coordinator_agent.py`: Agent logic.
-   `templates/index.html`: Dashboard frontend.
-   `static/script.js`: Dashboard logic.
