from typing import Dict, Any, List

class CoordinatorAgent:
    def __init__(self, controller):
        self.controller = controller

    def coordinate(self, observations: Dict[str, Any]):
        """
        Manages two different intersections (e.g., Main St. & 1st Ave).
        Logic: If Main St. releases a huge wave of cars, the Coordinator tells 1st Ave to prepare.
        """
        # Example Logic:
        # If I1 (Main St) has high North Queue, tell I2 (1st Ave) to bias North?
        # Or if I1 is congested, tell I2 to hold back?
        
        # Let's implement the prompt's example:
        # "If Main St. releases a huge wave of cars, the Coordinator tells 1st Ave to prepare for incoming traffic."
        
        # Assuming I1 is Main St and I2 is 1st Ave.
        # If I1 switches to NS_GREEN (releasing North/South traffic), and I2 is downstream...
        
        # For this specific task, let's implement a simple rule:
        # If I1 North Queue > 15, tell I2 to bias 'NS' (prepare for flow).
        
        if 'I1' in observations:
            i1_obs = observations['I1']
            status = i1_obs['status']
            
            if status['north_queue'] > 15:
                # Inject context to I2
                self.controller.update_context('I2', {'bias': 'NS'})
            else:
                # Clear context
                self.controller.update_context('I2', {})
