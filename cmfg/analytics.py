import numpy as np

DEBUG = False

# Start of datacollector functions
# Platform
def platform_capacity(model):
    """sum of all agents' initial capacity"""
    node_capacity = [a.capacity for a in model.schedule.agents]
    return np.sum(node_capacity)

#STATISTICS FOR DATACOLLECTOR

#PLATFORM STATISTICS
def getPlatformOverallCapacity(self):
    return self.platform_overall_capacity

def getPlatformUtilizationRate(model):
    overall_capacity = model.platform_overall_capacity
    current_capacity = platform_capacity(model)
    utilization_rate = round(round((overall_capacity - current_capacity)/overall_capacity,2)*100,2)
    return utilization_rate

def getCurrentServiceOrder(model):
    return service_request_analysis(model)['service_requests_len']

def getCurrentServiceRequests(model):
    return service_request_analysis(model)['services_capacity_request']

def getCurrentServiceQueued(model):
    return service_request_analysis(model)['service_queued_requests_len']

def getCurrentCapacityQueued(model):
    return service_request_analysis(model)['services_queued_request']

def getCurrentServiceRunning(model):
    return service_request_analysis(model)['services_running_len']

def getCurrentRunningCapacity(model):
    return service_request_analysis(model)['services_running_capacity']

def getCurrentCompletedServices(model):
    return service_request_analysis(model)['services_completed_len']

def getCurrentCompletedCapacity(model):
    return service_request_analysis(model)['services_capacity_completed']

def getCurrentRejectedServices(model):
    return service_request_analysis(model)['services_rejected_len']

def getCurrentRejectedCapacity(model):
    return service_request_analysis(model)['services_capacity_rejected']

#NODE STATISTICS
def getNodeCurrentServiceRequests(agent):
    service_queue = len(agent.service_requests_queue)
    return service_queue

def getNodeCurrentBalance(agent):
    current_balance = round(agent.balance['revenue'] - agent.balance['costs']['fixed_costs'] - agent.balance['costs']['manufacturing_costs'] - agent.balance['costs']['overhead_costs'],2)
    return current_balance

def getNodeCurrentRevenue(agent):
    current_revenues = round(agent.balance['revenue'],2)
    return current_revenues

def getNodeCurrentFixedCosts(agent):
    current_fixed_costs = round(agent.balance['costs']['fixed_costs'],2)
    return current_fixed_costs

def getNodeCurrentVariableCosts(agent):
    current_variable_costs = round(agent.balance['costs']['manufacturing_costs'] - agent.balance['costs']['overhead_costs'],2)
    return current_variable_costs

def getNodeCapitalInvestment(agent):
    capital_investment = round(agent.balance['costs']['capital_investment'],2)
    return capital_investment

def getNodeCapitalProcessedQuantitites(agent):
    quantities = agent.balance['processed_quantities']
    return quantities

def getNodeCurrentServiceWaiting(agent):
    service_pending_queue = len(agent.service_pending_queue)
    return service_pending_queue

def getNodeTasksQueue(agent):
    tasks_queue = len(agent.tasks_queue)
    return tasks_queue

def getNodeRunningTasks(agent):
    tasks_running = len(agent.running_tasks)
    return tasks_running

def getNodeCompletedTasks(agent):
    completed_tasks = len(agent.tasks_archive)
    return completed_tasks

#Statistics for log
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