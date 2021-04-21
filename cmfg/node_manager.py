from mesa import Agent
import uuid,random,math

#HYPERPARAMETERS
DEBUG = False

NODE_MIN_CAPACITY = 1
NODE_MAX_CAPACITY = 10  #no. of processing unit per step

MFG_COSTS_MIN = round(random.uniform(1,3),2)
MFG_COSTS_MAX = round(random.uniform(4,7),2)

FIXED_COSTS_MIN = 1
FIXED_COSTS_MAX = 5
OVERHEAD_COSTS_MIN = .5
OVERHEAD_COSTS_MAX = 3

MARGIN_MIN = 0.05

# COSTS PARAMETERS
MACHINE_UNIT_PRICE = round(random.uniform(80,200),2)

''' Functions'''
#Task initialization
def generate_task(self,node,service,quantity):
    task_id = "task_" + str(uuid.uuid4())
    task = {
        task_id :{
                "node": node,
                "service": service,
                "quantity": quantity,
                "start_time": 0,
                "end_time": 0,
                "completed": False
                }
        }
    return task

# Time related functions

# Service Analizer
def getDictID(dictionary):
    return list(dictionary.keys())[0]

def get_distance(pos1,pos2):
    (x1,y1) = pos1
    (x2,y2) = pos2
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return round(distance,4)

def analyze_service(self,service):
    service_id = getDictID(service)
    if DEBUG:
        print(f"::::::::::SERVICE ANALYZER:::::::::")
        print(f"[SERV. MANAGER] => {self.id} has received {service_id} request to analyze")
    distance = get_distance(self.pos,service[service_id]['delivery'])
    logistics_cost = distance * service[service_id]['unit_price'] * service[service_id]['logistics_cost']
    #manufacturing_price = service[service_id]['unit_price'] - logistics_cost
    manufacturing_cost = self.mfg_costs * service[service_id]['quantity']['machine_time']
    margin = service[service_id]['unit_price'] - manufacturing_cost - logistics_cost
    if  margin/service[service_id]['unit_price'] >= self.min_margin:
        if DEBUG:
            print(f"[SERV. MANAGER] => {service_id} for {self.id} is economically sustainable")
        if self.capacity > service[service_id]['quantity']:
            if DEBUG:
                print(f"[SERV. MANAGER] => {self.id} is able to process the entire service as follows: mfg price {manufacturing_price}/{self.mfg_costs} and logistics_cost {logistics_cost} ")
                print(f"[SERV. MANAGER] => Distance between node {self.pos} and delivery in {service[service_id]['delivery']} is: {round(distance,2)}")
            return service_id, service[service_id]['quantity'], distance
        elif self.capacity < service[service_id]['quantity']:
            if DEBUG:
                print(f"[SERV. MANAGER] => {self.id} may process only {self.capacity} out of {service[service_id]['quantity']} as follows: mfg price {manufacturing_price}/{self.mfg_costs} and logistics_cost {logistics_cost}")
                print(f"[SERV. MANAGER] => Distance between node {self.pos} and delivery in {service[service_id]['delivery']} is: {round(distance,2)}")
            return service_id, self.capacity, distance
        elif self.capacity == 0:
            if DEBUG:
                print(f"[SERV. MANAGER] => {self.id} is busy, cannot take the request")
            return False
    else:
        if DEBUG:
            print(f"[SERV. MANAGER] => {service_id} for {self.id} is not sustainable")

# Create Task(s)
def launchProduction(self):
    if DEBUG:
        print(f"::::::::::PRODUCTION MANAGER:::::::::")
    #find pending services
    pending_services = self.service_pending_queue.copy()
    for service_id in pending_services:
        #print(f"{self.id}:{service_id}")
        #find services details
        for service in self.model.order_schedule.agents[0].order_queue:
            #find service details that regards only the current node
            if service_id == getDictID(service):
                service_schedule = service[service_id]["schedule"]
                #extract only scheduling info for the node
                for node in service_schedule:
                    if node == self.id and service_schedule[self.id]["scheduled_quantity"] > 0:
                        #if service has planned to allocate resources from current node
                        #and if there is enough capacity, generate the task, reduce node current capacity for machine_time * quantity time
                        if DEBUG:
                            print(f'[PROD. MANAGER] => {service_schedule[self.id]["scheduled_quantity"]}/{self.capacity}')
                        scheduled_quantity = service_schedule[self.id]["scheduled_quantity"]
                        if self.capacity >= scheduled_quantity:
                            if DEBUG:
                                print(f"[PROD. MANAGER] => Everything is ok generate a task on {self.id}")
                            task = generate_task(self,node,service_id,scheduled_quantity)
                            self.service_pending_queue.pop(service_id)
                            self.tasks_queue.append(task)
                            if DEBUG:
                                print(task)
                        else:
                            if DEBUG:
                                print(f'[PROD. MANAGER] => Node {self.id} has reach capacity cannot accept service')
                            ###vedere se far rimbalzare o metterlo dopo in produzione

# Task Management
def taskManager(self):
    if DEBUG:
        print(f"::::::::::TASK MANAGER:::::::::")
    #start and close opening tasks if completed, update node capacity
    for task in self.tasks_queue:
        task_id = getDictID(task)
        service_id = task[task_id]["service"]
        #if task not started and there is enough capacity
        if self.capacity >= task[task_id]['quantity']:
            if DEBUG:
                print(f'[TASK MANAGER] => Task {task_id} has started on {self.id} @t={self.model.clock}')
            self.tasks_queue.remove(task)
            task[task_id]['start_time'] = self.model.clock     #set start time to now
            self.running_tasks.append(task)
            self.capacity -= task[task_id]['quantity']          #decrease node capacity
        
    for task in self.running_tasks:
        task_id = getDictID(task)
        for service in self.model.order_schedule.agents[0].order_queue:
            if service_id == getDictID(service):
                service_lead_time = service[service_id]["machine_time"]
                start_time = task[task_id]['start_time']
                current_time = self.model.clock
                end_time = start_time + service_lead_time
                if current_time > end_time:
                    if DEBUG:
                        print(f'[TASK MANAGER] => Task {task_id} has finished on {self.id} @{current_time} after {service_lead_time}')
                    self.running_tasks.remove(task)
                    task[task_id]['end_time'] = self.model.clock
                    task[task_id]['completed'] = True
                    self.tasks_archive.append(task)
                    self.capacity += task[task_id]['quantity']
                else:
                    if DEBUG:
                        print(f'[TASK MANAGER] => Task {task_id} is working on {self.id} @t={current_time}')

            ### if there is no machine capacity at the moment the task is gonna wait in task queue and process later

#Accounting -> Economic analysis
def updateNodeRevenues(self):
    #initialize revenue count
    self.balance['revenue'] = 0
    self.balance['processed_quantities'] = 0
    #update revenue only if service is completed and iterate for all task completed by the node
    for task in self.tasks_archive:
        task_id = getDictID(task)
        service_id = task[task_id]['service']
        for service in self.model.order_schedule.agents[0].order_archive:
            service_key = getDictID(service)
            if service_id == service_key:
                self.balance['revenue'] += round(service[service_id]['unit_price'] * task[task_id]['quantity'],2)
                self.balance['processed_quantities'] += task[task_id]['quantity']

def updateNodeCosts(self):
    #update fixed cost by multipling current step and fixed costs per unit
    self.balance['costs']['fixed_costs'] = round(self.model.clock * self.fixed_costs,2)
    self.balance['costs']['manufacturing_costs'] = self.balance['costs']['logistics_costs'] = self.balance['costs']['overhead_costs'] = 0
    #update variable costs for both completed services and running services
    for task in self.tasks_archive:
        task_id = getDictID(task)
        service_id = task[task_id]['service']
        for service in self.model.order_schedule.agents[0].order_archive:
            service_key = getDictID(service)
            if service_id == service_key:
                distance = get_distance(self.pos,service[service_id]['delivery'])
                logistics_cost = distance * service[service_id]['unit_price'] * service[service_id]['logistics_cost']
                self.balance['costs']['manufacturing_costs'] += round(self.mfg_costs * task[task_id]['quantity'],2)
                self.balance['costs']['logistics_costs'] += round(logistics_cost * task[task_id]['quantity'],2)
                self.balance['costs']['overhead_costs'] += round(self.overhead_costs * task[task_id]['quantity'],2)

def bookKeeping(self):
    updateNodeRevenues(self)
    updateNodeCosts(self)
    if DEBUG:
        print(f'{self.id} -----> {self.balance}')
    current_balance = round(self.balance['revenue'] - self.balance['costs']['fixed_costs'] - self.balance['costs']['manufacturing_costs'] - self.balance['costs']['overhead_costs'],2)
    if DEBUG:
        print(f'{self.id} -----> Current Balance = {current_balance}')
    #Estimating Break Even Point
    if self.balance['processed_quantities'] > 0:
        fixed_costs = (self.balance['costs']['capital_investment'] + self.balance['costs']['fixed_costs'] / self.balance['processed_quantities'])
        unit_revenue = self.balance['revenue'] / self.balance['processed_quantities']
        variable_costs =  (self.balance['costs']['manufacturing_costs'] - self.balance['costs']['overhead_costs']) / self.balance['processed_quantities']
        break_even = round(fixed_costs / (unit_revenue - variable_costs),2)
        if DEBUG:
            print(f'{self.id} -----> Estimated Break Even Point = {break_even}')

class Node(Agent):
    '''Represents a single service demander or service provider in the simulation.'''
    #ENUM NODE STATES
    INACTIVE = 0
    ACTIVE = 1

    def __init__(self, pos, model, init_state=INACTIVE):
        '''
        Create a node, in the given state, at the given x, y position.
        '''
        super().__init__(pos, model)
        self.x, self.y = pos
        self.model = model
        self.state = init_state
        self.id = "node_" + str(uuid.uuid4())
        self.capacity = random.randint(NODE_MIN_CAPACITY,NODE_MAX_CAPACITY)
        self.initial_capacity = self.capacity
        self.mfg_costs = round(random.uniform(MFG_COSTS_MIN,MFG_COSTS_MAX),2)
        self.fixed_costs = round(random.uniform(FIXED_COSTS_MIN,FIXED_COSTS_MAX),2)
        self.overhead_costs = round(random.uniform(OVERHEAD_COSTS_MIN,OVERHEAD_COSTS_MAX),2)
        self.min_margin = MARGIN_MIN
        self.service_requests_queue = []
        self.service_pending_queue = {}
        self.tasks_queue = []
        self.running_tasks = []
        self.tasks_archive = []
        self.balance = {
            'revenue': 0,
            'costs': {
                'capital_investment': self.capacity * MACHINE_UNIT_PRICE,                   #starting investment
                'fixed_costs': 0,                                                           #fixed cost of keep open the manufacturing node (equipments,general electricity, facilities etc. etc.)
                'manufacturing_costs': 0,                                                   #variable cost of running a machine of capacity 1 per 1 unit of time
                'logistics_costs': 0,                                                       #cost of delivery one unit of end product to the final point
                'overhead_costs': 0                                                         #variable costs not directly related to the machine or processing
            },
            'processed_quantities': 0
        }

        if DEBUG:
            print(f"[INIT] => Created a new agent with pos {self.x,self.y}, capacity {self.capacity}: {self.id}")

    @property
    def isActive(self):
        if len(self.tasks_queue) > 0:
            self.state = 1
            return True
        else:
            self.state = 0
            return False
            
    @property
    def hasRequests(self):
        if len(self.service_requests_queue) > 0:
            return True
        else:
            return False

    @property
    def hasPendingRequests(self):
        if len(self.service_pending_queue) > 0:
            return True
        else:
            return False

    @property
    def hasCompletedTasks(self):
        if len(self.tasks_archive)>0:
            return True
        else:
            return False            

    def step(self):
        '''
        Check the node status and Compute if the node has received any messages to process  
        at the next tick. Based on the number of service request received and left capacity 
        each node will first analyze and then accept or refuse service requests.
        '''
        if self.hasRequests:
            if DEBUG:
                print(f"[NODE MANAGER] => Agent {self.id} has {len(self.service_requests_queue)} service requests in queue @t={self.model.clock}|STEP")
            for service in self.service_requests_queue:
                if analyze_service(self,service):
                    service_id, availability, distance = analyze_service(self,service)
                    self.service_pending_queue[service_id] = {
                        "service_id": service_id,
                        "quantity":  availability,
                        "distance": distance
                    }
                else:
                    pass
                #either analyzed or rejected delete service requests from the node manager queue
                self.service_requests_queue.remove(service)
        else:
            if DEBUG:
                print(f"[NODE MANAGER] => Agent {self.id} currently has no service requests @t={self.model.clock}|STEP")

        '''
        if self.isActive:
            print(f"[NODE MANAGER] => Agent {self.id} is working on {len(self.tasks_queue)} task(s) @t={self.model.clock}|STEP")
            #manage tasks
            taskManager(self)
        else:
            if DEBUG:
                print(f"Agent {self.id} has no task to process and is doing a step fwd")
        '''

    def advance(self):
        if self.hasPendingRequests:
            if DEBUG:
                print(f"[NODE MANAGER] => Agent {self.id} has {len(self.service_pending_queue)} pending service(s) @t={self.model.clock}|ADVANCE")
            launchProduction(self)

        if self.isActive:
            if DEBUG:
                print(f"[NODE MANAGER] => Agent {self.id} is working on {len(self.tasks_queue)} task(s) @t={self.model.clock}|ADVANCE")
            #manage tasks
            taskManager(self)
        else:
            if DEBUG:
                print(f"Agent {self.id} has no task to process and is going to next step @t={self.model.clock}|ADVANCE")
        
        if self.hasCompletedTasks:
            if DEBUG:
                print(f"[NODE MANAGER] => Agent {self.id} has completed {len(self.tasks_archive)} task(s) @t={self.model.clock}|ADVANCE")
        
        bookKeeping(self)
        '''
        #Update book keeping only at last step
        if self.model.clock == self.model.last_step - 1:
            bookKeeping(self)
        '''