import threading
import time
import json
from collections import deque
from typing import Callable, Dict, Any
from traffic_simulator import TrafficSimulator

class ObserverAgent:
    def __init__(self, simulator: TrafficSimulator, callback: Callable[[str], None]):
        self.sim = simulator
        self.callback = callback
        self.running = False
        self.thread = None
        self.last_processed_step = -1
        
        # Metrics state per intersection
        # Key: intersection_id, Value: { 'wait_times': deque(maxlen=30) }
        self.metrics_state = {}

    def start(self):
        """Starts the observer in a background thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops the observer thread."""
        self.running = False
        if self.thread:
            self.thread.join()

    def _poll_loop(self):
        """Main loop that polls the simulator state."""
        while self.running:
            try:
                current_step = self.sim.current_time
                
                # Only process if we moved to a new step
                if current_step > self.last_processed_step:
                    self._process_step(current_step)
                    self.last_processed_step = current_step
            except Exception as e:
                print(f"ObserverAgent Error: {e}")
                import traceback
                traceback.print_exc()
            
            # Sleep briefly to yield control and avoid 100% CPU usage
            # Adjust this based on simulation speed. 
            # If sim is real-time (1 sec/step), 0.01 is fine.
            time.sleep(0.01)

    def _process_step(self, step: int):
        """Extracts state and computes metrics for the current step."""
        # Accessing sim.intersections directly (assuming thread safety or atomic reads for this simple case)
        # In a strict environment, we might need locks, but for this Python sim it's likely fine 
        # as long as we don't modify the list while iterating.
        
        for intersection in self.sim.intersections:
            i_id = intersection.intersection_id
            
            # Initialize metrics state if needed
            if i_id not in self.metrics_state:
                self.metrics_state[i_id] = {
                    'wait_times': deque(maxlen=30)
                }
            
            # Get raw state
            # Note: get_state() returns a dict copy, so it's relatively safe
            state = intersection.get_state(step)
            
            # Compute Metrics
            queues = state['queues']
            queue_sum = sum(queues.values())
            max_queue = max(queues.values()) if queues else 0
            
            # Rolling Average Wait Time
            # We need the current average wait time from the intersection to track it over time?
            # Or does the requirement "Rolling average wait (window=30s)" mean:
            # Average of the "avg_wait" reported by intersection over last 30 steps?
            # OR Average wait of cars in the last 30s?
            # The intersection reports cumulative avg wait.
            # Let's assume "Rolling average of the reported avg_wait" for simplicity, 
            # or better, let's track the instantaneous wait or just smooth the reported value.
            # Given the input "avg_wait" in the JSON example is a single number, 
            # and the requirement says "Rolling average wait (window=30s)",
            # I will store the `avg_waiting_time` from the intersection state in the deque
            # and compute the average of that deque.
            
            current_avg_wait = state.get('avg_waiting_time', 0.0)
            self.metrics_state[i_id]['wait_times'].append(current_avg_wait)
            
            rolling_avg_wait = sum(self.metrics_state[i_id]['wait_times']) / len(self.metrics_state[i_id]['wait_times'])
            
            # Construct Message
            message = {
                "intersection_id": i_id,
                "timestamp": step, # Using step as timestamp
                "lane_counts": queues, # queues are lane counts
                "queue_lengths": queues, # Same as above
                "queue_sum": queue_sum,
                "max_queue": max_queue,
                "avg_wait": round(rolling_avg_wait, 2),
                "current_phase": state['phase'],
                "phase_elapsed": state['phase_timer']
            }
            
            # Publish
            json_msg = json.dumps(message)
            self.callback(json_msg)
