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
    "step": 0,
    "intersections": {},
    "history": [],
    "last_action": "None"
}

sim_lock = threading.Lock()
sim_thread = None
msg_queue = queue.Queue()

# --- Simulation Setup ---
def init_simulation():
    global sim, observer, controller, coordinator
    sim = TrafficSimulator()
    
    # Create Intersections
    i1 = Intersection("I1", green_duration=10, clearance_rate=0.8, manual_control=True)
    i2 = Intersection("I2", green_duration=10, clearance_rate=0.8, manual_control=True)
    sim.add_intersection(i1)
    sim.add_intersection(i2)
    
    # Agents
    def thread_safe_callback(msg):
        msg_queue.put(msg)
        
    observer = ObserverAgent(sim, thread_safe_callback)
    
    def action_callback(action):
        simulation_state["last_action"] = f"{action['intersection_id']}: {action['action']}"
        intersection_id = action['intersection_id']
        for i in sim.intersections:
            if i.intersection_id == intersection_id:
                if action['action'] == 'SWITCH':
                    i.switch_phase()
                break

    controller = ControllerAgent(observer, action_callback)
    coordinator = CoordinatorAgent(
        observer, 
        {"I1": controller, "I2": controller}, 
        {"I1": "I2"}
    )
    
    observer.start()
    
    # Reset state
    simulation_state["step"] = 0
    simulation_state["intersections"] = {}
    simulation_state["history"] = []
    simulation_state["last_action"] = "None"

# Initialize once
init_simulation()

# --- Simulation Loop ---
def run_simulation_loop():
    while True:
        if simulation_state["running"]:
            with sim_lock:
                sim.step()
                simulation_state["step"] = sim.current_time
                
                # Inject traffic (Scenario)
                if sim.current_time % 10 == 0:
                    sim.intersections[1].add_vehicle('N', sim.current_time)
                    sim.intersections[1].add_vehicle('N', sim.current_time)

            # Process Messages
            while not msg_queue.empty():
                msg = msg_queue.get()
                data = json.loads(msg)
                
                # Update Global State
                i_id = data['intersection_id']
                simulation_state["intersections"][i_id] = data
                
                # Update History (only store I1 for simplicity in chart, or aggregate)
                # Let's store I1's wait time
                if i_id == "I1":
                    simulation_state["history"].append({
                        "step": data['timestamp'],
                        "avg_wait": data['avg_wait']
                    })
                    # Limit history size
                    if len(simulation_state["history"]) > 50:
                        simulation_state["history"].pop(0)
                
                # Run Agents
                controller.on_state_update(msg)
                coordinator.on_state_update(msg)
                
        time.sleep(0.1)

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
    action = request.json.get('action')
    if action == 'start':
        simulation_state["running"] = True
    elif action == 'stop':
        simulation_state["running"] = False
    elif action == 'reset':
        with sim_lock:
            # Stop old observer? Ideally yes, but for simplicity we just re-init
            if observer:
                observer.stop()
            init_simulation()
            simulation_state["running"] = False
            
    return jsonify({"status": "ok", "running": simulation_state["running"]})

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
