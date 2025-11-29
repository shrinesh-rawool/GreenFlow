from typing import Dict, Any

class ControllerAgent:
    def __init__(self, simulator):
        self.sim = simulator
        self.context = {} # Stores context updates from Coordinator

    def decide(self, observation: Dict[str, Any]):
        """
        Receives a summary from the Observer.
        Rules:
            If the current green lane has < 5 cars and red lane has > 15 cars, SWITCH.
            If 'CRITICAL' flag is raised, prioritize that lane immediately.
        Output: Call the execute_signal_change tool with your decision.
        """
        intersection_id = observation['intersection_id']
        status = observation['status']
        critical = observation['critical']
        critical_lanes = observation['critical_lanes']
        
        current_green_lane = status['current_green_lane'] # e.g., 'NS_GREEN'
        
        # Determine Green and Red queues
        if current_green_lane == 'NS_GREEN':
            green_queue = status['north_queue'] + status['south_queue']
            red_queue = status['east_queue'] + status['west_queue']
            red_direction = 'EW'
        else:
            green_queue = status['east_queue'] + status['west_queue']
            red_queue = status['north_queue'] + status['south_queue']
            red_direction = 'NS'

        decision = "HOLD"
        reason = "Normal flow"

        # Check Context Update
        context_bias = self.context.get(intersection_id, {}).get('bias')
        
        # Rule: CRITICAL flag
        if critical:
            # If critical lane is in RED direction, SWITCH
            # If critical lane is in GREEN direction, HOLD (keep it green)
            # We need to know which specific lane is critical.
            # critical_lanes is list like ['north_queue', 'east_queue']
            
            critical_in_red = False
            for lane in critical_lanes:
                if current_green_lane == 'NS_GREEN':
                    if 'east' in lane or 'west' in lane:
                        critical_in_red = True
                else: # EW_GREEN
                    if 'north' in lane or 'south' in lane:
                        critical_in_red = True
            
            if critical_in_red:
                decision = "SWITCH"
                reason = "CRITICAL lane waiting"
            else:
                decision = "HOLD"
                reason = "CRITICAL lane clearing"
        
        # Rule: Green < 5 and Red > 15
        elif green_queue < 5 and red_queue > 15:
            decision = "SWITCH"
            reason = "Green empty, Red piling up"
            
        # Context Bias Rule (from Coordinator)
        elif context_bias:
            if context_bias == red_direction:
                 decision = "SWITCH"
                 reason = "Coordinator Bias"
        
        # Execute Decision
        if decision == "SWITCH":
            self.sim.execute_signal_change(intersection_id, "SWITCH")
        
        return {
            "intersection_id": intersection_id,
            "decision": decision,
            "reasoning": reason,
            "observation": f"Green: {green_queue}, Red: {red_queue}, Critical: {critical}"
        }

    def update_context(self, intersection_id: str, context: Dict[str, Any]):
        self.context[intersection_id] = context
