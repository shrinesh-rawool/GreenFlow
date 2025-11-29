import random
from collections import deque
from typing import List, Dict, Optional

class Lane:
    def __init__(self, lane_id: str):
        self.lane_id = lane_id
        self.queue = deque()  # Stores arrival times of vehicles
        self.total_waiting_time = 0
        self.vehicles_cleared = 0

    def add_vehicle(self, current_time: int):
        """Adds a vehicle to the queue with the current timestamp."""
        self.queue.append(current_time)

    def remove_vehicle(self, current_time: int) -> int:
        """Removes a vehicle and returns its waiting time. Returns -1 if empty."""
        if not self.queue:
            return -1
        arrival_time = self.queue.popleft()
        waiting_time = current_time - arrival_time
        self.total_waiting_time += waiting_time
        self.vehicles_cleared += 1
        return waiting_time

    def get_queue_length(self) -> int:
        return len(self.queue)

    def get_average_waiting_time(self) -> float:
        if self.vehicles_cleared == 0:
            return 0.0
        return self.total_waiting_time / self.vehicles_cleared

    def get_current_wait_time(self, current_time: int) -> float:
        """Returns the average wait time of vehicles currently in the queue."""
        if not self.queue:
            return 0.0
        total_wait = sum(current_time - arrival_time for arrival_time in self.queue)
        return total_wait / len(self.queue)

class Intersection:
    def __init__(self, intersection_id: str, green_duration: int = 10, clearance_rate: float = 0.5, manual_control: bool = False):
        self.intersection_id = intersection_id
        # Approaches: North, East, South, West
        self.approaches: Dict[str, Lane] = {
            'N': Lane(f"{intersection_id}_N"),
            'E': Lane(f"{intersection_id}_E"),
            'S': Lane(f"{intersection_id}_S"),
            'W': Lane(f"{intersection_id}_W")
        }
        self.phases = ['NS_GREEN', 'EW_GREEN']
        self.current_phase_index = 0
        self.phase_timer = 0
        self.green_duration = green_duration
        self.clearance_rate = clearance_rate # Vehicles per second per lane
        self.manual_control = manual_control

    @property
    def north_queue(self): return self.approaches['N'].get_queue_length()
    @property
    def south_queue(self): return self.approaches['S'].get_queue_length()
    @property
    def east_queue(self): return self.approaches['E'].get_queue_length()
    @property
    def west_queue(self): return self.approaches['W'].get_queue_length()
    
    @property
    def current_green_lane(self):
        return self.phases[self.current_phase_index]

    def step(self, current_time: int):
        """Executes one time step of the intersection logic."""
        self.phase_timer += 1
        
        # Switch phase if duration exceeded AND NOT manual control
        if not self.manual_control and self.phase_timer >= self.green_duration:
            self.switch_phase()
        
        current_phase = self.phases[self.current_phase_index]
        
        # Determine which lanes have green light
        green_lanes = []
        if current_phase == 'NS_GREEN':
            green_lanes = ['N', 'S']
        elif current_phase == 'EW_GREEN':
            green_lanes = ['E', 'W']
            
        # Process departures for green lanes
        for lane_key in green_lanes:
            lane = self.approaches[lane_key]
            if random.random() < self.clearance_rate:
                lane.remove_vehicle(current_time)

    def switch_phase(self):
        """Manually switches to the next phase."""
        self.current_phase_index = (self.current_phase_index + 1) % len(self.phases)
        self.phase_timer = 0
        
    def switch_light(self, direction: str = None):
        """
        Changes the green light. 
        If direction is provided (e.g., 'NS' or 'EW'), it switches to that phase.
        Otherwise it just toggles.
        """
        if direction:
            if direction == 'NS' and self.phases[self.current_phase_index] != 'NS_GREEN':
                self.current_phase_index = self.phases.index('NS_GREEN')
                self.phase_timer = 0
            elif direction == 'EW' and self.phases[self.current_phase_index] != 'EW_GREEN':
                self.current_phase_index = self.phases.index('EW_GREEN')
                self.phase_timer = 0
        else:
            self.switch_phase()

    def add_vehicle(self, approach: str, current_time: int):
        if approach in self.approaches:
            self.approaches[approach].add_vehicle(current_time)

    def get_state(self, current_time: int = 0) -> Dict:
        # Calculate average wait time of CURRENTLY waiting vehicles
        total_current_wait = sum(lane.get_current_wait_time(current_time) * lane.get_queue_length() for lane in self.approaches.values())
        total_queue = sum(lane.get_queue_length() for lane in self.approaches.values())
        
        # Weighted average
        avg_wait = total_current_wait / total_queue if total_queue > 0 else 0.0
        
        return {
            'id': self.intersection_id,
            'phase': self.phases[self.current_phase_index],
            'phase_timer': self.phase_timer,
            'queues': {k: v.get_queue_length() for k, v in self.approaches.items()},
            'avg_waiting_time': avg_wait,
            # Add specific queue keys for easier access if needed
            'north_queue': self.north_queue,
            'south_queue': self.south_queue,
            'east_queue': self.east_queue,
            'west_queue': self.west_queue
        }

    def get_status(self) -> Dict:
        """Returns current queue lengths as requested."""
        return {
            'north_queue': self.north_queue,
            'south_queue': self.south_queue,
            'east_queue': self.east_queue,
            'west_queue': self.west_queue,
            'current_green_lane': self.current_green_lane
        }

class TrafficSimulator:
    def __init__(self, logger=None):
        self.intersections: List[Intersection] = []
        self.current_time = 0
        self.arrival_rate = 0.1 # Vehicles per second per lane (Poisson lambda)
        self.logger = logger

    def add_intersection(self, intersection: Intersection):
        self.intersections.append(intersection)

    def step(self):
        self.current_time += 1
        intersection_states = []
        for intersection in self.intersections:
            # Simulate Arrivals (Poisson)
            for approach in intersection.approaches:
                if random.random() < self.arrival_rate:
                    intersection.add_vehicle(approach, self.current_time)
            
            # Simulate Intersection Logic
            intersection.step(self.current_time)
            intersection_states.append(intersection.get_state(self.current_time))
            
        if self.logger:
            self.logger.log_step(self.current_time, intersection_states)

    def run(self, steps: int):
        for _ in range(steps):
            self.step()
        if self.logger:
            self.logger.save_json()

    # --- Tool Wrappers for Agents ---
    def get_traffic_status(self, intersection_id: str) -> Dict:
        """Returns current queue lengths for all lanes."""
        for intersection in self.intersections:
            if intersection.intersection_id == intersection_id:
                return intersection.get_status()
        return {"error": "Intersection not found"}

    def execute_signal_change(self, intersection_id: str, action: str) -> str:
        """Executes a signal change. Action can be 'HOLD' or 'SWITCH'."""
        for intersection in self.intersections:
            if intersection.intersection_id == intersection_id:
                if action == "SWITCH":
                    intersection.switch_light()
                    return f"Signal SWITCHED for {intersection_id}"
                elif action == "HOLD":
                    return f"Signal HELD for {intersection_id}"
                # Support directional switch if needed, e.g. "SWITCH_NS"
                elif action.startswith("SWITCH_"):
                    direction = action.split("_")[1]
                    intersection.switch_light(direction)
                    return f"Signal SWITCHED to {direction} for {intersection_id}"
        return "Intersection not found or Invalid Action"
