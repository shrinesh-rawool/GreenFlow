import csv
import json
import os
from typing import Dict, List, Any

class SimulationLogger:
    def __init__(self, log_dir: str = "logs", run_id: str = "sim_run"):
        self.log_dir = log_dir
        self.run_id = run_id
        self.csv_file_path = os.path.join(log_dir, f"{run_id}_metrics.csv")
        self.json_file_path = os.path.join(log_dir, f"{run_id}_metrics.json")
        self.logs: List[Dict[str, Any]] = []
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Initialize CSV with headers
        self.headers = ['step', 'intersection_id', 'phase', 'total_queue_length', 'avg_waiting_time']
        with open(self.csv_file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writeheader()

    def log_step(self, step: int, intersection_states: List[Dict[str, Any]]):
        """Logs the state of the simulation at a given step."""
        step_logs = []
        for state in intersection_states:
            # Calculate aggregate metrics for the intersection
            queues = state['queues']
            total_queue = sum(queues.values())
            
            # We need waiting time from the state, but currently get_state only returns queues.
            # We should update Intersection.get_state to return more info or pass objects.
            # For now, let's assume state has what we need or we calculate it.
            # Actually, let's update Intersection.get_state in traffic_simulator.py first.
            # But for now, I'll just log what I have and extend later.
            
            log_entry = {
                'step': step,
                'intersection_id': state['id'],
                'phase': state['phase'],
                'total_queue_length': total_queue,
                'avg_waiting_time': state.get('avg_waiting_time', 0.0)
            }
            step_logs.append(log_entry)
            self.logs.append(log_entry)

        # Write to CSV
        with open(self.csv_file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writerows(step_logs)

    def save_json(self):
        """Saves all logs to a JSON file."""
        with open(self.json_file_path, 'w') as f:
            json.dump(self.logs, f, indent=2)
