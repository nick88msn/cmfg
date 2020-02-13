from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import Grid

from cmfg.node_manager import Node
from cmfg.order_dispatcher import OrderManager

import numpy as np

DEBUG = False
LAST_STEP = 100


# Hyperparameters
model_height = 20
model_width = 20
no_nodes = 30

# Start of datacollector functions
# Platform
def platform_capacity(model):
    """sum of all agents' initial capacity"""
    node_capacity = [a.capacity for a in model.schedule.agents]
    return np.sum(node_capacity)

def platform_utilization_rate(model):
    """platform overall capacity / platform current capacity"""
    overall_capacity = model.platform_overall_capacity
    current_capacity = platform_capacity(model)
    utilization_rate = round(round((overall_capacity - current_capacity)/overall_capacity,2)*100,2)
    return utilization_rate,overall_capacity

# Services Status
def service_request_analysis(model):
    """length of service queue"""
    service_requests = [s.order_register for s in model.order_schedule.agents]
    service_queue = [s.order_queue for s in model.order_schedule.agents]
    service_archived = [s.order_archive for s in model.order_schedule.agents]
    service_requests_len = len(service_requests[0])
    services_capacity_request = 0
    services_queued_request = []
    services_queued_capacity = 0
    services_capacity_rejected = 0
    services_capacity_completed = 0
    services_running_capacity = 0
    services_rejected = []
    services_running = []
    services_completed = []

    for service in service_requests[0]:
        key = list(service.keys())[0]
        services_capacity_request += service[key]['quantity']
    
    for service in service_queue[0]:
        key = list(service.keys())[0]
        if service[key]['status'] == 4:
            services_running.append(service)
            services_running_capacity += service[key]['quantity']
        elif  service[key]['status'] == 3:
            services_queued_request.append(service)
            services_queued_capacity += service[key]['quantity']        

    for service in service_archived[0]:
        key = list(service.keys())[0]
        if service[key]['status'] == 5:
            services_rejected.append(service)
            services_capacity_rejected += service[key]['quantity']
        elif service[key]['status'] == 6:
            services_completed.append(service)
            services_capacity_completed += service[key]['quantity']
    services_rejected_len = len(services_rejected)
    services_running_len = len(services_running)
    services_completed_len = len(services_completed)
    service_queued_requests_len = len(services_queued_request)
    if DEBUG:
        print(f":::::::::::SERVICE ARCHIVED:::::::::: | {service_archived}")
    return {
        "service_requests_len": service_requests_len,
        "service_queued_requests_len": service_queued_requests_len,
        "services_running_len": services_running_len,
        "services_rejected_len": services_rejected_len,
        "services_completed_len": services_completed_len,
        "services_capacity_request": services_capacity_request,
        "services_queued_request": services_queued_capacity,
        "services_running_capacity": services_running_capacity,
        "services_capacity_rejected": services_capacity_rejected,
        "services_capacity_completed": services_capacity_completed
    } 

'''
Create KPI for tasks created, service create, time to complete a task and a service
'''

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

        self.platform_overall_capacity = platform_capacity(self)
        print("::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        print(f"Created a platform with capacity: {self.platform_overall_capacity}")
        self.running = True
    
    def step(self):
        '''
        Have the scheduler advance each node by one step
        '''
        self.order_schedule.step()
        self.schedule.step()
        utilization_rate,overall_capacity = platform_utilization_rate(self)
        analytics = service_request_analysis(self) 
        print(f"[{self.clock}]: Platform Current Capacity: {platform_capacity(self)}|{overall_capacity} - ({utilization_rate}) % utilization rate")
        print(f"[{self.clock}]: Current Service Order: {analytics['service_requests_len']} | Current Service Capacity Request: {analytics['services_capacity_request']}")
        print(f"[{self.clock}]: Current Service Queue: {analytics['service_queued_requests_len']} | Current Service Queued Capacity Request: {analytics['services_queued_request']}")
        print(f"[{self.clock}]: Running Services: {analytics['services_running_len']} | Running Capacity: {analytics['services_running_capacity']}")
        print(f"[{self.clock}]: Completed Services: {analytics['services_completed_len']} | Completed Capacity: {analytics['services_capacity_completed']}")
        print(f"[{self.clock}]: Rejected Services: {analytics['services_rejected_len']} | Rejected Capacity: {analytics['services_capacity_rejected']}")
        self.clock += 1
        print("::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        '''
        Evolutionary model...randomly it should create new node near busiest area
        Make a revenue - cost balance for nodes. If things goes ok it should invest in new capacity if things go wrong reduce capacity till its dead
        '''