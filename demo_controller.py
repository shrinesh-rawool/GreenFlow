from traffic_simulator import TrafficSimulator, Intersection
from observer_agent import ObserverAgent
from controller_agent import ControllerAgent
import time
import json
import random

def action_callback(action: dict):
    """Callback to receive actions from Controller."""
    print(f"[Controller Action] {action}")
    # Execute action
    intersection_id = action['intersection_id']
    # Find intersection
    # In a real system, we'd have a map. Here we iterate or use global scope if simple.
    # We'll use a global reference for this demo or pass it.
    # Let's assume we have access to 'sim' or 'intersections' map.
    if intersection_id in intersection_map:
        intersection = intersection_map[intersection_id]
        if action['action'] == 'SWITCH':
            print(f" -> Switching Phase for {intersection_id}")
            intersection.switch_phase()

def observer_callback(message: str):
    """Callback to handle observer messages."""
    # We can print or just let the controller handle it.
    # For demo visibility, let's print a summary.
    data = json.loads(message)
    # print(f"[Observer] {data['intersection_id']} Phase={data['current_phase']} Elapsed={data['phase_elapsed']} Q={data['queue_lengths']}")
    
    # Pass to controller
    controller.on_state_update(message)

def main():
    global intersection_map, controller
    
    print("Initializing Traffic Simulator with Controller Agent...")
    
    # Setup Simulator
    sim = TrafficSimulator()
    
    # Create Intersection with Manual Control
    i1 = Intersection("INT_01", green_duration=10, clearance_rate=0.8, manual_control=True)
    sim.add_intersection(i1)
    
    intersection_map = {"INT_01": i1}
    
    # Setup Observer
    observer = ObserverAgent(sim, observer_callback)
    
    # Setup Controller
    controller = ControllerAgent(observer, action_callback)
    
    observer.start()
    
    print("Starting Simulation for 50 steps...")
    print("Logic: Switch if opposing queue > current + 5 OR max green (25s). Min green (5s).")
    
    try:
        for step in range(1, 51):
            # Manually inject traffic to trigger switches
            # Phase starts NS_GREEN.
            # To trigger switch to EW, we need EW queue > NS queue + 5
            # So let's flood EW (approaches E, W)
            if step == 10:
                print("\n[Scenario] Flooding East/West to trigger switch...")
                for _ in range(10):
                    i1.add_vehicle('E', sim.current_time)
                    i1.add_vehicle('W', sim.current_time)
            
            sim.step()
            time.sleep(0.1) 
            
    except KeyboardInterrupt:
        print("Simulation interrupted.")
    finally:
        observer.stop()
        print("Observer stopped.")
        print("Simulation Complete.")

if __name__ == "__main__":
    main()
