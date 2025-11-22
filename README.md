# GreenFlow 🚦

**GreenFlow** is a modular, extensible traffic simulation platform designed to test and visualize multi-agent traffic control strategies. It features a custom-built discrete-time simulator, intelligent agents (Observer, Controller, Coordinator), and a real-time web dashboard.

![Traffic Simulator Dashboard](https://via.placeholder.com/800x400?text=GreenFlow+Dashboard+Preview)

## 🌟 Features

*   **Custom Traffic Simulator**: A lightweight, Python-based simulator supporting multiple intersections, lanes, and phases.
*   **Intelligent Agents**:
    *   **Observer Agent**: Polls simulation state and computes real-time metrics (queue lengths, wait times).
    *   **Controller Agent**: Implements rule-based logic (min/max green time, queue balancing) to optimize traffic flow.
    *   **Coordinator Agent**: Monitors network-level state to prevent spillback and gridlock.
*   **Real-Time Dashboard**: A modern web interface (Flask + HTML/JS) to visualize:
    *   Live traffic queues per lane.
    *   Active traffic light phases.
    *   Real-time average wait time charts.
    *   System status and agent actions.
*   **Extensible Design**: Easily add new intersection types, agent strategies (e.g., RL), or metrics.

## 🚀 Getting Started

### Prerequisites

*   Python 3.8+
*   `pip` (Python package manager)

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/shrinesh-rawool/GreenFlow.git
    cd GreenFlow
    ```

2.  Install dependencies:
    ```bash
    pip install flask
    ```

## 🖥️ Usage

### Running the Dashboard

1.  Start the Flask server:
    ```bash
    python3 server.py
    ```

2.  Open your browser and navigate to:
    ```
    http://127.0.0.1:5000
    ```

3.  Use the **Start**, **Stop**, and **Reset** buttons to control the simulation.

### Running Demos

The project includes several standalone demo scripts to test individual components:

*   **Basic Simulator**: `python3 demo.py`
*   **Observer Agent**: `python3 demo_observer.py`
*   **Controller Agent**: `python3 demo_controller.py`
*   **Coordinator Agent**: `python3 demo_coordinator.py`

## 📂 Project Structure

*   `traffic_simulator.py`: Core simulation logic (Lane, Intersection, Simulator).
*   `server.py`: Flask backend for the web dashboard.
*   `observer_agent.py`: Agent responsible for state monitoring.
*   `controller_agent.py`: Agent responsible for local intersection control.
*   `coordinator_agent.py`: Agent responsible for multi-intersection coordination.
*   `templates/` & `static/`: Frontend assets for the dashboard.
*   `project_documentation.md`: Detailed technical documentation.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open-source and available under the MIT License.
