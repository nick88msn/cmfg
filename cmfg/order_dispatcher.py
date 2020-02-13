from mesa import Agent
import uuid,random

#visualization
import matplotlib.pyplot as plt 

DEBUG = False

'''HYPERPARAMETER'''
MIN_ORDER_QTY = 1
MAX_ORDER_QTY = 50
UNIT_PRICE = round(random.uniform(6,25),2)
MACHINE_TIME = random.randint(1,4)
LOGISTICS_UNIT_COST_PCG = round(random.uniform(0.005,0.02),4)
SUBSET_RADIUS = 20

# Service Status
INACTIVE = 0
SENT_TO_NODES = 1
SCHEDULING = 2
QUEUEING = 3
RUNNING = 4
REJECTED = 5
CONCLUDED = 6

#Service Generation
SERVICE_PER_ROUND = random.randint(1,30)

'''Functions'''
# General Utils
def getDictID(dictionary):
    return list(dictionary.keys())[0]

# Generate Services and Tasks
def generate_service(self,model):
    service_id = "service_" + str(uuid.uuid4())
    service = {
        service_id :{
                "task_type": "a",
                "quantity": random.randint(MIN_ORDER_QTY,MAX_ORDER_QTY),
                "unit_price": UNIT_PRICE,
                "logistics_cost": LOGISTICS_UNIT_COST_PCG,
                "machine_time": MACHINE_TIME,
                "delivery": self.model.grid.find_empty(),
                "status": INACTIVE,
                "schedule": {},
                "registration_time": self.model.clock,
                "enter_queue_time": 0,
                "start_processing_time": 0,
                "end_processing_time": 0
                }
        }
    return service

# Service requests (subset identification and request protocol)
def find_neighbors_node(self,service,id,model):
    pos = (service[id]['delivery'])
    node_subset = self.model.grid.get_neighbors(pos, moore=True, include_center=True, radius=SUBSET_RADIUS)
    if DEBUG:
        print(f"[SERVICE MANAGER] => NEIGHBORS ANALYZER : For service {id} there are {len(node_subset)} nodes available in a 15 cells radius from {pos}")
    return node_subset

def sendServiceRequests(self,service):
    id = list(service.keys())[0]
    node_subset = find_neighbors_node(self,service,id,self.model)
    for node in node_subset:
        if service not in node.service_requests_queue: 
            node.service_requests_queue.append(service)
            service[id]['status'] = SENT_TO_NODES

# Service Scheduling
def findAvailableNodes(self,service):
    id = list(service.keys())[0]
    node_subset = find_neighbors_node(self,service,id,self.model)
    for node in node_subset:
        if id in list(node.service_pending_queue.keys()):
            if DEBUG:
                print(f"[SERVICE MANAGER] => Requesting {node.id} availability to process {id}")
            service[id]["schedule"][node.id] = {
                "available_quantity": node.service_pending_queue[id]["quantity"],
                "distance": node.service_pending_queue[id]["distance"],
                "scheduled_quantity": 0
                } 

def getServiceCurrentTasks(self,service):
    service_id = getDictID(service)
    tasks_list = []
    network = list(service[service_id]['schedule'].keys())
    for node in network:
        if service[service_id]['schedule'][node]['scheduled_quantity'] == 0:
            network.remove(node)
    nodes = self.model.schedule.agents

    for node in nodes:
        if node.id in network:
            for task in node.tasks_queue:
                task_id = getDictID(task)
                if task[task_id]['service'] == service_id:
                    tasks_list.append(task)
            for task in node.running_tasks:
                task_id = getDictID(task)
                if task[task_id]['service'] == service_id:
                    tasks_list.append(task)
            for task in node.tasks_archive:
                task_id = getDictID(task)
                if task[task_id]['service'] == service_id:
                    tasks_list.append(task)
    return tasks_list

def getServiceSchedule(self,service):
    service_id = getDictID(service)
    network = list(service[service_id]['schedule'].keys())

    if service[service_id]['status'] > 5:
        tasks_list = getServiceCurrentTasks(self,service)

def scheduleService(self,service):
    #print(service)
    id = list(service.keys())[0]       
    service_quantity = service[id]['quantity']
    available_quantity = 0
    for node in service[id]['schedule']:
        available_quantity += service[id]['schedule'][node]['available_quantity']
    if available_quantity >= service_quantity:
        if DEBUG:
            print(f'[SERVICE MANAGER] => SCHEDULER : Preliminary Analysis: From nodes availability responses there is enough capacity to process {id}')
        #Nearest First Farthest Last (N2FL) method
        schedule = service[id]['schedule']
        schedule = sorted(schedule, key=lambda x: (schedule[x]['distance']))    #sort nodes id by distance
        if DEBUG:
            print(f'[SERVICE MANAGER] => SCHEDULER : Current scheduling plan for {id} -> {schedule}')
        scheduled_quantity = 0
        temp = 0
        while scheduled_quantity != service_quantity:
            for node in schedule:
                temp += service[id]['schedule'][node]['available_quantity']
                if temp <= service_quantity:
                    service[id]['schedule'][node]['scheduled_quantity'] = service[id]['schedule'][node]['available_quantity']
                    scheduled_quantity += service[id]['schedule'][node]['available_quantity']
                else:
                    service[id]['schedule'][node]['scheduled_quantity'] = service_quantity - scheduled_quantity
                    scheduled_quantity += service_quantity - scheduled_quantity
            if DEBUG:
                print(f"[SERVICE MANAGER] => SCHEDULER : Scheduled_Quantity: {scheduled_quantity} | Service_Quantity {service_quantity} | Temp {temp}")
        if service in self.order_register:
            self.order_register.remove(service)
        if service not in self.order_queue:
            service[id]['status'] = QUEUEING
            service[id]['enter_queue_time'] = self.model.clock
            self.order_queue.append(service)
            
    elif available_quantity > 0 and available_quantity < service_quantity:
        if DEBUG:
            print(f'[SERVICE MANAGER] => SCHEDULER : Not enough capacity in the network for process {id}. It is possible to manufacture only: {available_quantity} out of {service_quantity}')
        if service in self.order_register:
            service[id]['status'] = REJECTED
            self.order_register.remove(service)
            self.order_archive.append(service)   

    '''
        !IMPORTANT - Add that if service is rejected because scheduled nodes are currently unavailable the scheduling delete this nodes and reschedule to other available nodes
            Without it the platform only create a big queue inside the network.
    '''

# Service Manager
def manageServiceRequests(self,service):
    service_id = getDictID(service)
    network = list(service[service_id]['schedule'].keys())
    nodes = self.model.schedule.agents

    #task running
    running_tasks = []
    archive_tasks = []
    queueing_tasks = []
    for node in nodes:
        if node.id in network:
            running_tasks.append(node.running_tasks) 
            archive_tasks.append(node.tasks_archive)
            queueing_tasks.append(node.tasks_queue)


    for running_task in running_tasks:
        if running_task != []:
            if DEBUG:
                print(f'[NICO] -> Current Running Task {running_task}')
            for task in running_task:
                if task != []:
                    task_id = list(task.keys())[0]
                    service_key = task[task_id]['service']
                    if DEBUG:
                        print(f'Need to update to running {service_id}')
                    if service_key == service_id:
                        if service[service_id]['status'] == QUEUEING and service[service_id]['start_processing_time'] == 0:
                            if DEBUG:
                                print(f'[NICO] -> Found {service_key} in ORDER QUEUE to update')
                            index = self.order_queue.index(service)
                            self.order_queue[index][service_key]['start_processing_time'] = task[task_id]['start_time']
                            self.order_queue[index][service_key]['status'] = RUNNING
                            if DEBUG:
                                print(f'[NICO] -> Updated start time for {service_key}')

#in order to change service status to --> completed we need to ensure that every taks in the scheduling is completed
    #!!!! ADD QUEUEING TASKS TO AVOID ASSIGN END PROCESSING TIME WITH THE FIRST TASK COMPLETED
    check = []
    #@the end of the for loop if service is running and check is empty than all tasks for the job are completed
    for tasks in (queueing_tasks + running_tasks + archive_tasks):
        if tasks != []:
            for task in tasks:
                if task != []:
                    task_id = getDictID(task)
                    service_key = task[task_id]['service']
                    if DEBUG:
                        print(f'Need to update to running {service_id}')
                    if service_key == service_id:
                        check.append(task)

    for completed_task in archive_tasks:
        if completed_task != []:
            if DEBUG:
                print(f'[NICO] -> Current Completed Taks {completed_task}')
            for task in completed_task:
                task_id = list(task.keys())[0]
                service_key = task[task_id]['service']
                if DEBUG:
                    print(f'Need to update {service_id}')
                if service_key == service_id:
                    processed_quantities = [task[getDictID(task)]['quantity'] for task in check]                 
                    if  sum(processed_quantities) >= service[service_id]['quantity'] and service[service_id]['status'] == 4 and service[service_id]['end_processing_time'] == 0:
                        if DEBUG:
                            print(f'[NICO] -> Found {service_key} to finalize')
                        service[service_key]['end_processing_time'] = task[task_id]['end_time']
                        service[service_key]['status'] = 6
                        if DEBUG:
                            print(f'[NICO] -> Updated Service:::>>> {service}')
                        self.order_archive.append(service)
                        self.order_queue.remove(service)
                        if DEBUG:
                            print(f'[NICO] -> Removed Service from queue and added to archive')

    '''
    if is running delete node in schedule with scheduled_quantity = 0
    '''

    #print(f"[NICO] -> Current Service Order: {self.order_register}")
    #print(f"[NICO] -> Current Service Queue: {self.order_queue}")
    #print(f"[NICO] -> Current Service Archive: {self.order_archive}")

    #print(f'[NICO] -> Current Service Agent Analyze {service}')
    #print(f'[NICO] -> Current Service Network {network}')

    #task running
    running_tasks = []
    archive_tasks = []
    for node in nodes:
        running_tasks.append(node.running_tasks) 
        archive_tasks.append(node.tasks_archive)
    #print(f'[NICO] -> Current running tasks {running_tasks}')
    #print(f'[NICO] -> Current Tasks Archive {archive_tasks}')

def getServiceGantt(self,service):
    # Declaring a figure "gnt" 
    service_id = list(service.keys())[0]
    if service[service_id]['status'] == CONCLUDED:
        fig, gnt = plt.subplots() 
        #print(service)
        y_label = list(service.keys())[0]
        x_label = 'Clock Time (steps)'

        # Setting labels for x-axis and y-axis 
        gnt.set_xlabel(x_label) 
        gnt.set_ylabel(y_label)

        # Setting X-axis limits 
        gnt.set_xlim(service[y_label]['start_processing_time'] - 20, service[y_label]['end_processing_time'] + 20) 

        #extracting tasks timelines
        nodes = self.model.schedule.agents
        scheduled_nodes = service[y_label]['schedule'].keys()
        tasks_list = []

        for node in nodes:
            if node.id in scheduled_nodes:
                for task in node.tasks_archive:
                    task_id = list(task.keys())[0]
                    if task[task_id]['service'] == service_id:
                        tasks_list.append(task)

        y_ticks = []
        for i in range(len(tasks_list) + 1):
            y_ticks.append(15 + i * 10)

        # Setting Y-axis limits 
        if len(tasks_list) > 0:
            gnt.set_ylim(0, y_ticks[-1] + 10)
        else:
            gnt.set_ylim(0, 10)

        yticklabels = [service_id]
        for task in tasks_list:
            yticklabels.append(list(task.keys())[0])
        
        # Setting ticks on y-axis
        gnt.set_yticks(y_ticks)
        # Labelling tickes of y-axis
        gnt.set_yticklabels(yticklabels)

        # Declaring multiple bars in at same level and same width
        reg_time = service[y_label]['registration_time']
        reg_time2queue_time = service[y_label]['enter_queue_time'] - service[y_label]['registration_time']
        queue_time = service[y_label]['enter_queue_time']
        queueing_time = service[y_label]['start_processing_time'] - service[y_label]['enter_queue_time']
        start_running = service[y_label]['start_processing_time']
        processing_time = service[y_label]['end_processing_time'] - service[y_label]['start_processing_time']

        #in future take for every task the element in the gantt with a for loop, this is the service bar
        gnt.broken_barh([(reg_time, reg_time2queue_time), (queue_time, queueing_time), (start_running, processing_time)], (10,9), 
                                facecolors =('blue','red','yellow'))
        i = 10
        for task in tasks_list:
            i += 10
            task_id = list(task.keys())[0]
            task_duration = task[task_id]['end_time'] - task[task_id]['start_time']
            gnt.broken_barh([(task[task_id]['start_time'], task_duration)], (i,9), 
                                facecolors =('yellow'))

        # Setting grid attribute 
        gnt.grid(True)
        plt.show()

class OrderManager(Agent):
    '''Represents a middleware to register and dispatch order bulletin to nodes.'''

    def __init__(self, unique_id, model):
        '''
        Create an agent with an empty service request register.
        '''
        super().__init__(unique_id, model)
        self.order_register = []    #service bulletin with current service requests pool 
        self.order_queue = []       #service list for orders that have already been analyzed and sent to nodes
        self.order_archive = []     #archive with all services, either completed and rejected 
        self.model = model
        if DEBUG:
            print(f"Created the Order Manager")

    @property
    def hasServiceOrder(self):
        if len(self.order_register) > 0:
            return True
        else:
            return False
    
    @property
    def hasQueuedServices(self):
        if len(self.order_queue) > 0:
            return True
        else:
            return False
    
    @property
    def hasCompletedServices(self):
        if len(self.order_archive) > 0:
            return True
        else:
            return False

    def step(self):
        '''
        A random method to generate and append new service request to the bulletin
        '''

        if random.randint(0,1) == 0:
            pass
        else:
            for _ in range(SERVICE_PER_ROUND):
                service = generate_service(self,self.model)
                self.order_register.append(service)

        '''
        A method to analyze current services requests and find suitable nodes
        '''
        if self.hasServiceOrder:
            #find nodes close to the order delivery point and send service requests
            for service in self.order_register:
                sendServiceRequests(self,service)
        
        if DEBUG:
            print(f"Node Manager has done the first step")

    def advance(self):
        '''
        After sending service request to close nodes, the order manager starts to analyze response send scheduling to available nodes
        '''

        if self.hasServiceOrder:
            #manage current orders status
            for service in self.order_register:
                findAvailableNodes(self,service)
                scheduleService(self,service)                

        if self.hasQueuedServices:
            for service in self.order_queue:
                manageServiceRequests(self,service)            #collect availability responses from nodes for each service and put in a schedule dictionary

        if self.hasCompletedServices:
            for service in self.order_archive:
                if self.model.clock == self.model.last_step - 1:
                    getServiceGantt(self,service)

        if DEBUG:
            print(f"Node Manager has advanced step")