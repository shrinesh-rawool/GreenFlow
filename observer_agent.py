import json
from typing import Dict, Any

class ObserverAgent:
    def __init__(self, simulator):
        self.sim = simulator

    def observe(self, step: int) -> Dict[str, Any]:
        """
        Reads queue lengths using get_traffic_status.
        If any queue is > 20 cars, flag it as 'CRITICAL'.
        Returns a structured summary.
        """
        observations = {}
        
        for intersection in self.sim.intersections:
            i_id = intersection.intersection_id
            status = self.sim.get_traffic_status(i_id)
            
            # Check for CRITICAL flag
            critical_lanes = []
            for lane, length in status.items():
                if lane.endswith('_queue') and length > 20:
                    critical_lanes.append(lane)
            
            summary = {
                "intersection_id": i_id,
                "step": step,
                "status": status,
                "critical": len(critical_lanes) > 0,
                "critical_lanes": critical_lanes
            }
            observations[i_id] = summary
            
        return observations
