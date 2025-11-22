from traffic_simulator import TrafficSimulator, Intersection
from observer_agent import ObserverAgent
from controller_agent import ControllerAgent
from coordinator_agent import CoordinatorAgent
import time
import json

def action_callback(action: dict):
    """Callback to receive actions from Controller."""
    # print(f"[Controller Action] {action}")
    intersection_id = action['intersection_id']
    if intersection_id in intersection_map:
        intersection = intersection_map[intersection_id]
        if action['action'] == 'SWITCH':
            print(f" -> Switching Phase for {intersection_id}")
            intersection.switch_phase()

def observer_callback(message: str):
    """Callback to handle observer messages."""
    # Pass to controller and coordinator
    controller.on_state_update(message)
    coordinator.on_state_update(message)

def main():
    global intersection_map, controller, coordinator
    
    print("Initializing Traffic Simulator with Coordinator Agent...")
    
    # Setup Simulator
    sim = TrafficSimulator()
    
    # Create Intersections
    # I1 feeds into I2
    i1 = Intersection("I1", green_duration=10, clearance_rate=0.8, manual_control=True)
    i2 = Intersection("I2", green_duration=10, clearance_rate=0.8, manual_control=True)
    sim.add_intersection(i1)
    sim.add_intersection(i2)
    
    intersection_map = {"I1": i1, "I2": i2}
    
    # Setup Observer
    observer = ObserverAgent(sim, observer_callback)
    
    # Setup Controller
    # We use one controller instance managing both for simplicity, or we could have one per intersection.
    # The ControllerAgent class design handles any intersection ID passed in state.
    # So one instance is fine.
    controller = ControllerAgent(observer, action_callback)
    
    # Setup Coordinator
    # Graph: I1 -> I2
    coordinator = CoordinatorAgent(observer, {"I1": controller, "I2": controller}, {"I1": "I2"})
    
    observer.start()
    
    print("Starting Simulation for 50 steps...")
    print("Scenario: I2 gets congested. Coordinator should tell I1 to avoid extending green.")
    
    try:
        for step in range(1, 51):
            # Congest I2 manually
            if step > 10:
                for _ in range(3):
                    i2.add_vehicle('N', sim.current_time) # Add to I2
            
            # Keep I1 busy so it WANTS to extend
            if step > 10:
                i1.add_vehicle('N', sim.current_time) # Add to I1 (Green lane)
            
            sim.step()
            
            # Check advisory status occasionally
            if step % 10 == 0:
                adv = controller.advisories.get('I1', {})
                print(f"Step {step}: I1 Advisory: {adv}")
                
            time.sleep(0.1) 
            
    except KeyboardInterrupt:
        print("Simulation interrupted.")
    finally:
        observer.stop()
        print("Observer stopped.")
        print("Simulation Complete.")

if __name__ == "__main__":
    main()
