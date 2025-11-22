from traffic_simulator import TrafficSimulator, Intersection
from logger import SimulationLogger
import time

def main():
    print("Initializing Traffic Simulator...")
    
    # Setup Logger
    logger = SimulationLogger(log_dir="logs", run_id="demo_run")
    
    # Setup Simulator
    sim = TrafficSimulator(logger=logger)
    
    # Create Intersections
    # Intersection 1: Standard
    i1 = Intersection("INT_01", green_duration=15, clearance_rate=0.6)
    sim.add_intersection(i1)
    
    # Intersection 2: Faster switching
    i2 = Intersection("INT_02", green_duration=10, clearance_rate=0.8)
    sim.add_intersection(i2)
    
    print("Starting Simulation for 200 steps...")
    
    # Run Simulation
    # We can run step by step to print progress
    for step in range(1, 201):
        sim.step()
        
        # Print status every 20 steps
        if step % 20 == 0:
            state1 = i1.get_state()
            print(f"Step {step}: INT_01 Phase={state1['phase']} Queues={state1['queues']} AvgWait={state1['avg_waiting_time']:.2f}s")

    sim.logger.save_json()
    print("Simulation Complete.")
    print(f"Logs saved to {logger.log_dir}")

if __name__ == "__main__":
    main()
