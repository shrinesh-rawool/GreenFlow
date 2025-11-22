import json
from typing import Callable, Dict, Any

class ControllerAgent:
    def __init__(self, observer, action_callback: Callable[[Dict[str, Any]], None]):
        """
        Args:
            observer: The ObserverAgent instance to subscribe to.
            action_callback: Function to call with action dict.
        """
        self.observer = observer
        self.action_callback = action_callback
        self.advisories = {} # intersection_id -> advisory dict
        
        # Subscribe to observer
        # We assume observer has a way to add multiple callbacks or we wrap the existing one.
        # For this implementation, we'll just hook into the observer's callback mechanism.
        # If the observer only supports one callback, we might need to chain them.
        # But let's assume we can just set it or add it.
        # The current ObserverAgent takes a callback in __init__.
        # So in the demo, we will pass the Controller's on_state_update as the callback.
        
    def on_state_update(self, state_json: str):
        """Callback received from Observer."""
        state = json.loads(state_json)
        self.compute_action(state)

    def receive_advisory(self, intersection_id: str, advisory: Dict[str, Any]):
        """Receives advisory from Coordinator."""
        self.advisories[intersection_id] = advisory

    def compute_action(self, state: Dict[str, Any]):
        """Decides whether to SWITCH or EXTEND."""
        intersection_id = state['intersection_id']
        phase = state['current_phase']
        phase_elapsed = state['phase_elapsed']
        queues = state['queue_lengths']
        
        # Constraints
        MIN_GREEN = 5
        MAX_GREEN = 25
        
        if phase_elapsed < MIN_GREEN:
            return # Too early to switch
            
        if phase_elapsed >= MAX_GREEN:
            self.send_action(intersection_id, "SWITCH")
            return

        # Logic
        # Identify green and red lanes
        if phase == 'NS_GREEN':
            green_lanes = ['N', 'S']
            red_lanes = ['E', 'W']
        else: # EW_GREEN
            green_lanes = ['E', 'W']
            red_lanes = ['N', 'S']
            
        current_queue = sum(queues[lane] for lane in green_lanes)
        opposing_queue = sum(queues[lane] for lane in red_lanes)
        
        # Rule 1: If opposing queue is significantly larger, switch
        if opposing_queue > current_queue + 5:
            self.send_action(intersection_id, "SWITCH")
            return
            
        # Check for advisory
        avoid_extend = False
        if intersection_id in self.advisories:
            avoid_extend = self.advisories[intersection_id].get('avoid_extend', False)
            
        # Rule 2: If current queue is large, extend (implicit by NOT switching)
        # BUT if avoid_extend is True, we should probably switch if we can (or just not extend).
        # If we are here, it means opposing <= current + 5.
        # If avoid_extend is True, we want to clear the intersection or stop feeding downstream.
        # If avoid_extend is True, it means downstream is full. We should probably hold RED for the feeding lane?
        # Or if we are GREEN feeding downstream, we should SWITCH to stop feeding.
        # Let's assume avoid_extend means "Do not extend GREEN phase if you were planning to".
        # So if current_queue > 10, normally we extend. But if avoid_extend is True, we SWITCH.
        
        if current_queue > 10:
            if avoid_extend:
                # Coordinator says don't extend!
                self.send_action(intersection_id, "SWITCH")
            else:
                # "EXTEND" action is basically doing nothing
                pass

    def send_action(self, intersection_id: str, action: str):
        action_dict = {
            "intersection_id": intersection_id,
            "action": action
        }
        self.action_callback(action_dict)
