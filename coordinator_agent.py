import json
from typing import Dict, Any, List
from controller_agent import ControllerAgent

class CoordinatorAgent:
    def __init__(self, observer, controllers: Dict[str, ControllerAgent], graph: Dict[str, str]):
        """
        Args:
            observer: ObserverAgent to subscribe to.
            controllers: Dict of intersection_id -> ControllerAgent.
            graph: Dict of upstream_id -> downstream_id (Simple 1-to-1 for now).
                   Example: {'I1': 'I2'} means I1 feeds into I2.
        """
        self.observer = observer
        self.controllers = controllers
        self.graph = graph
        self.state_cache = {} # Stores latest state for each intersection
        
        # Subscribe to observer (we assume we can hook into it, similar to Controller)
        # In demo, we'll manually pass messages or assume observer supports multiple callbacks.
        # For now, we'll expose an on_state_update method.

    def on_state_update(self, state_json: str):
        """Callback received from Observer."""
        state = json.loads(state_json)
        self.state_cache[state['intersection_id']] = state
        self.check_spillback()

    def check_spillback(self):
        """Checks for spillback and sends advisories."""
        SPILLBACK_THRESHOLD = 20
        
        for upstream, downstream in self.graph.items():
            if downstream in self.state_cache:
                downstream_state = self.state_cache[downstream]
                # Check total queue or specific approach queue?
                # For simplicity, check total queue sum of downstream.
                downstream_queue = downstream_state['queue_sum']
                
                if downstream_queue > SPILLBACK_THRESHOLD:
                    # Spillback detected! Tell upstream to avoid extending green.
                    self.send_advisory(upstream, {'avoid_extend': True})
                else:
                    # Clear advisory
                    self.send_advisory(upstream, {'avoid_extend': False})

    def send_advisory(self, intersection_id: str, advisory: Dict[str, Any]):
        if intersection_id in self.controllers:
            self.controllers[intersection_id].receive_advisory(intersection_id, advisory)
