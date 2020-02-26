from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import Grid

from cmfg.node_manager import Node
from cmfg.order_dispatcher import OrderManager
import cmfg.analytics as a

from mesa.datacollection import DataCollector

DEBUG = False
LAST_STEP = 30

# Hyperparameters
model_height = 20
model_width = 20
no_nodes = 50

# Start of platform model
class SMfgModel(Model):

    def __init__(self, height=model_height, width=model_width, no_nodes=no_nodes):
        # Set up the grid and schedule.

        # Use SimultaneousActivation which simulates all the nodes
        # computing their next state and actions simultaneously.  
        # This needs to be done because each node's next state 
        # depends on the current state of all its neighbors 
        # -- before they've changed.\
        self.clock = 0
        self.last_step = LAST_STEP
        self.schedule = SimultaneousActivation(self)
        self.order_schedule = SimultaneousActivation(self)

        # Use a simple grid, where edges wrap around.
        self.grid = Grid(height, width, torus=True)

        # Create an order manager
        order_manager = OrderManager(1,self)
        self.order_schedule.add(order_manager)

        for _ in range(no_nodes):
            pos = self.grid.find_empty()
            node = Node(pos,self)
            self.grid.place_agent(node,pos)
            self.schedule.add(node)

        self.platform_overall_capacity = a.platform_capacity(self)
        self.datacollector = DataCollector(
            model_reporters={
                "Platform Overall Capacity": a.getPlatformOverallCapacity,
                "Platform Current Capacity": a.platform_capacity,
                "Utilization Rate": a.getPlatformUtilizationRate,
                "Service Orders": a.getCurrentServiceOrder,
                "Service Capacity Request": a.getCurrentServiceRequests,
                "Service Queued": a.getCurrentServiceQueued,
                "Capacity Queued": a.getCurrentCapacityQueued,
                "Running Services": a.getCurrentServiceRunning,
                "Running Capacity": a.getCurrentRunningCapacity,
                "Completed Services": a.getCurrentCompletedServices,
                "Completed Capacity": a.getCurrentCompletedCapacity,
                "Rejected Services": a.getCurrentRejectedServices,
                "Rejected Capacity": a.getCurrentRejectedCapacity
                },  
            agent_reporters={
                'ID': 'id',
                'Location': 'pos',
                'Full Capacity': 'initial_capacity',
                'Current Capacity': 'capacity',
                'Balance': a.getNodeCurrentBalance,
                'Revenue': a.getNodeCurrentRevenue,
                'Fixed Costs': a.getNodeCurrentFixedCosts,
                'Variable Costs': a.getNodeCurrentVariableCosts,
                'Capital Investment': a.getNodeCapitalInvestment,
                'Processed Quantities': a.getNodeCapitalProcessedQuantitites,
                'Current Service Requests': a.getNodeCurrentServiceRequests,
                'Current Service Waiting': a.getNodeCurrentServiceWaiting,
                'Tasks queue': a.getNodeTasksQueue,
                'Running Tasks': a.getNodeRunningTasks,
                'Completed Tasks': a.getNodeCompletedTasks
                })

        print("::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        print(f"Created a platform with capacity: {self.platform_overall_capacity}")
        self.running = True
    
    def step(self):
        '''
        Have the scheduler advance each node by one step
        '''
        self.order_schedule.step()
        self.schedule.step()
        self.datacollector.collect(self)
        utilization_rate,overall_capacity = a.platform_utilization_rate(self)
        analytics = a.service_request_analysis(self) 
        print(f"[{self.clock}]: Platform Current Capacity: {a.platform_capacity(self)}|{overall_capacity} - ({utilization_rate}) % utilization rate")
        print(f"[{self.clock}]: Current Service Order: {analytics['service_requests_len']} | Current Service Capacity Request: {analytics['services_capacity_request']}")
        print(f"[{self.clock}]: Current Service Queue: {analytics['service_queued_requests_len']} | Current Service Queued Capacity Request: {analytics['services_queued_request']}")
        print(f"[{self.clock}]: Running Services: {analytics['services_running_len']} | Running Capacity: {analytics['services_running_capacity']}")
        print(f"[{self.clock}]: Completed Services: {analytics['services_completed_len']} | Completed Capacity: {analytics['services_capacity_completed']}")
        print(f"[{self.clock}]: Rejected Services: {analytics['services_rejected_len']} | Rejected Capacity: {analytics['services_capacity_rejected']}")
        print("::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        self.clock += 1
        '''
        Evolutionary model...randomly it should create new node near busiest area
        Make a revenue - cost balance for nodes. If things goes ok it should invest in new capacity if things go wrong reduce capacity till its dead
        '''