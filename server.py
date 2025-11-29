from flask import Flask, render_template, jsonify, request
import threading
import time
import json
import queue
from traffic_simulator import TrafficSimulator, Intersection
from observer_agent import ObserverAgent
from controller_agent import ControllerAgent
from coordinator_agent import CoordinatorAgent

app = Flask(__name__)

# Global State
simulation_state = {
    "running": False,
    "mode": "AI", # "AI" or "BASELINE"
    "step": 0,
    "intersections": {},
    "history": [],
    "logs": []
}

sim_lock = threading.Lock()
sim_thread = None

# Agents & Sim
sim = None
observer = None
controller = None
coordinator = None

# --- Simulation Setup ---
def init_simulation():
    global sim, observer, controller, coordinator
    sim = TrafficSimulator()
    
    # Create Intersections
    # Manual control is True so agents can switch lights. 
    # In Baseline mode, we might want auto-switch or manual switch by timer.
    i1 = Intersection("I1", green_duration=30, manual_control=True)
    i2 = Intersection("I2", green_duration=30, manual_control=True)
    sim.add_intersection(i1)
    sim.add_intersection(i2)
    
    # Initialize Agents
    observer = ObserverAgent(sim)
    controller = ControllerAgent(sim)
    coordinator = CoordinatorAgent(controller)
    
    # Reset state
    simulation_state["step"] = 0
    simulation_state["intersections"] = {}
    simulation_state["history"] = []
    simulation_state["logs"] = []

# Initialize once
init_simulation()

# --- Simulation Loop ---
def run_simulation_loop():
    while True:
        if simulation_state["running"]:
            with sim_lock:
                # 1. Start Step (Add random cars)
                sim.step()
                simulation_state["step"] = sim.current_time
                
                # Inject traffic (Scenario)
                if sim.current_time % 10 == 0:
                    sim.intersections[0].add_vehicle('N', sim.current_time)
                    sim.intersections[0].add_vehicle('N', sim.current_time)

                # 2. Observe Step & 3. Decide Step
                if simulation_state["mode"] == "AI":
                    # Observer
                    observations = observer.observe(sim.current_time)
                    
                    # Coordinator (Every 5 steps)
                    if sim.current_time % 5 == 0:
                        coordinator.coordinate(observations)
                    
                    # Controller (Decide for each intersection)
                    for i_id, obs in observations.items():
                        decision_data = controller.decide(obs)
                        
                        # Log Decision
                        log_entry = {
                            "step": sim.current_time,
                            "agent": f"Controller_{i_id}",
                            "observation": decision_data['observation'],
                            "decision": decision_data['decision'],
                            "reasoning": decision_data['reasoning']
                        }
                        simulation_state["logs"].append(log_entry)
                        if len(simulation_state["logs"]) > 100:
                            simulation_state["logs"].pop(0)

                elif simulation_state["mode"] == "BASELINE":
                    # Static Timer Logic
                    # Switch every 30 seconds
                    for intersection in sim.intersections:
                        # We used manual_control=True, so we must switch manually
                        if intersection.phase_timer >= 30:
                            intersection.switch_light()
                            
                # 4. Metric Step (Update State for UI)
                for intersection in sim.intersections:
                    state = intersection.get_state(sim.current_time)
                    simulation_state["intersections"][intersection.intersection_id] = state
                    
                    # History for Chart (I1 only for simplicity)
                    if intersection.intersection_id == "I1":
                        simulation_state["history"].append({
                            "step": sim.current_time,
                            "avg_wait": state['avg_waiting_time'],
                            "total_queue": sum(state['queues'].values())
                        })
                        if len(simulation_state["history"]) > 100:
                            simulation_state["history"].pop(0)
                            
        time.sleep(0.1) # 10 steps per second max

# Start Background Thread
sim_thread = threading.Thread(target=run_simulation_loop, daemon=True)
sim_thread.start()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    return jsonify(simulation_state)

@app.route('/api/control', methods=['POST'])
def control():
    data = request.json
    action = data.get('action')
    
    if action == 'start':
        simulation_state["running"] = True
    elif action == 'stop':
        simulation_state["running"] = False
    elif action == 'reset':
        with sim_lock:
            init_simulation()
            simulation_state["running"] = False
    elif action == 'set_mode':
        mode = data.get('mode')
        if mode in ['AI', 'BASELINE']:
            simulation_state["mode"] = mode
            # Reset on mode change? Maybe better to let user reset.
            
    return jsonify({"status": "ok", "running": simulation_state["running"], "mode": simulation_state["mode"]})

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
