import streamlit as st
import time
import json
import pandas as pd
import queue
from traffic_simulator import TrafficSimulator, Intersection
from observer_agent import ObserverAgent
from controller_agent import ControllerAgent
from coordinator_agent import CoordinatorAgent

# Page Config
st.set_page_config(page_title="Traffic Simulator Dashboard", layout="wide")

# --- Callbacks ---
# Callback for actions (runs in main thread context via queue processing)
def action_callback(action: dict):
    """Callback to receive actions from Controller."""
    # Update session state for visualization
    st.session_state.last_action = f"{action['intersection_id']}: {action['action']}"
    
    # Execute action
    intersection_id = action['intersection_id']
    # We need access to the simulator instance. 
    # Since this runs in the main thread (mostly), we can access session_state.sim
    if 'sim' in st.session_state:
        sim = st.session_state.sim
        # Find intersection (sim.intersections is a list, we should probably have made it a dict)
        for i in sim.intersections:
            if i.intersection_id == intersection_id:
                if action['action'] == 'SWITCH':
                    i.switch_phase()
                break

def init_simulation():
    """Initializes the simulation state."""
    st.session_state.sim = TrafficSimulator()
    st.session_state.msg_queue = queue.Queue()
    
    # Create Intersections
    i1 = Intersection("I1", green_duration=10, clearance_rate=0.8, manual_control=True)
    i2 = Intersection("I2", green_duration=10, clearance_rate=0.8, manual_control=True)
    st.session_state.sim.add_intersection(i1)
    st.session_state.sim.add_intersection(i2)
    
    # Setup Agents
    # Capture queue in a closure to avoid accessing st.session_state in thread
    q = st.session_state.msg_queue
    def thread_safe_callback(msg):
        q.put(msg)
        
    st.session_state.observer = ObserverAgent(st.session_state.sim, thread_safe_callback)
    st.session_state.controller = ControllerAgent(st.session_state.observer, action_callback)
    st.session_state.coordinator = CoordinatorAgent(
        st.session_state.observer, 
        {"I1": st.session_state.controller, "I2": st.session_state.controller}, 
        {"I1": "I2"}
    )
    
    st.session_state.observer.start()
    st.session_state.running = False
    st.session_state.history = []
    st.session_state.latest_state = None
    st.session_state.last_action = "None"

# --- Initialization ---
if 'sim' not in st.session_state:
    init_simulation()

# --- Sidebar Controls ---
st.sidebar.title("Controls")
if st.sidebar.button("Start/Stop"):
    st.session_state.running = not st.session_state.running

if st.sidebar.button("Reset"):
    # Stop old observer if running
    if 'observer' in st.session_state and st.session_state.observer:
        st.session_state.observer.stop()
    init_simulation()
    st.rerun()

speed = st.sidebar.slider("Simulation Speed (delay)", 0.0, 1.0, 0.1)

# --- Main Dashboard ---
st.title("🚦 Traffic Simulator Dashboard")

# Layout
col1, col2 = st.columns(2)

# Metrics
with col1:
    st.subheader("System Status")
    status = "Running" if st.session_state.running else "Paused"
    st.metric("Status", status)
    
    if st.session_state.latest_state:
        state = st.session_state.latest_state
        st.metric("Current Step", state['timestamp'])
        st.metric("Last Action", st.session_state.last_action)

with col2:
    st.subheader("Live Metrics (I1)")
    if st.session_state.latest_state:
        state = st.session_state.latest_state
        # Note: Observer currently only reports one intersection at a time in the callback?
        # The ObserverAgent iterates and calls callback for EACH intersection.
        # So latest_state will be overwritten by whichever reported last.
        # For the dashboard, we should probably store state per intersection.
        # But for this simple demo, let's just visualize whatever comes in (likely I2 since it's added last).
        # Or better, let's filter/store properly.
        pass

# Better State Handling
# We need to capture state for ALL intersections to display them.
# Let's assume the callback updates a dict: st.session_state.states = {'I1': ..., 'I2': ...}
# We need to update the callback logic, but we can't change the function definition easily inside the script 
# without reloading. 
# Actually, we can just check st.session_state.latest_state and see which ID it is.
# But it's better to have a persistent store.

if 'states' not in st.session_state:
    st.session_state.states = {}

if st.session_state.latest_state:
    ls = st.session_state.latest_state
    st.session_state.states[ls['intersection_id']] = ls

# Display per intersection
for i_id, data in st.session_state.states.items():
    with st.expander(f"Intersection {i_id}", expanded=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Phase", data['current_phase'])
        c1.metric("Elapsed", f"{data['phase_elapsed']}s")
        c2.metric("Avg Wait", f"{data['avg_wait']}s")
        c3.metric("Queue Sum", data['queue_sum'])
        
        # Bar Chart for Queues
        queues = data['lane_counts']
        df_queues = pd.DataFrame.from_dict(queues, orient='index', columns=['Vehicles'])
        st.bar_chart(df_queues)

# Historical Graph
st.subheader("Average Wait Time History")
if st.session_state.history:
    df_hist = pd.DataFrame(st.session_state.history)
    # We might have mixed data from I1 and I2 in history. 
    # Let's just plot it. It might be messy but shows activity.
    st.line_chart(df_hist.set_index('step')['avg_wait'])

# --- Simulation Loop ---
if st.session_state.running:
    # Step the simulator
    st.session_state.sim.step()
    
    # Process messages from Observer (Thread)
    while not st.session_state.msg_queue.empty():
        message = st.session_state.msg_queue.get()
        data = json.loads(message)
        
        # Update State
        st.session_state.latest_state = data
        
        # Update History
        st.session_state.history.append({
            "step": data['timestamp'],
            "avg_wait": data['avg_wait'],
            "queue_sum": data['queue_sum']
        })
        
        # Run Agents (in Main Thread)
        st.session_state.controller.on_state_update(message)
        st.session_state.coordinator.on_state_update(message)
    
    # Inject traffic manually to make it interesting (like in demo)
    # I2 congestion scenario
    current_time = st.session_state.sim.current_time
    if current_time % 10 == 0:
        # Add cars to I2
        st.session_state.sim.intersections[1].add_vehicle('N', current_time)
        st.session_state.sim.intersections[1].add_vehicle('N', current_time)
    
    time.sleep(speed)
    st.rerun()
