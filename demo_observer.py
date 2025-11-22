from traffic_simulator import TrafficSimulator, Intersection
from observer_agent import ObserverAgent
import time
import json

def observer_callback(message: str):
    """Callback function to handle observer messages."""
    data = json.loads(message)
    print(f"[Observer] Step {data['timestamp']} | ID: {data['intersection_id']} | Phase: {data['current_phase']} | AvgWait: {data['avg_wait']}s | QueueSum: {data['queue_sum']}")

def main():
    print("Initializing Traffic Simulator with Observer Agent...")
    
    # Setup Simulator
    sim = TrafficSimulator()
    
    # Create Intersections
    i1 = Intersection("INT_01", green_duration=5, clearance_rate=0.6)
    sim.add_intersection(i1)
    
    i2 = Intersection("INT_02", green_duration=8, clearance_rate=0.8)
    sim.add_intersection(i2)
    
    # Setup Observer
    observer = ObserverAgent(sim, observer_callback)
    observer.start()
    
    print("Starting Simulation for 20 steps...")
    
    try:
        for step in range(1, 21):
            sim.step()
            # Sleep to allow observer thread to catch the state change
            # Since observer polls every 0.01s, a sleep of 0.1s ensures it catches it.
            time.sleep(0.1) 
            
    except KeyboardInterrupt:
        print("Simulation interrupted.")
    finally:
        observer.stop()
        print("Observer stopped.")
        print("Simulation Complete.")

if __name__ == "__main__":
    main()
