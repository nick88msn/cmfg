from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa.visualization.UserParam import UserSettableParameter
from cmfg.model import SMfgModel,model_height,model_width,no_nodes
from cmfg.node_manager import Node
from cmfg.order_dispatcher import OrderManager

colors = {
    'green': '#46FF33',
    'red': '#FF3C33',
    'blue': '#3349FF',
    'yellow': '#FFFF00'
}

def getDictID(dictionary):
    return list(dictionary.keys())[0]

def model_draw(agent):
    '''
    Portrayal Method for canvas
    '''
    if agent is None:
        return
    portrayal = {}
    
    if isinstance(agent, Node):
        portrayal["Shape"] = "circle"
        portrayal["r"] = .2 * agent.initial_capacity   #nodes with bigger capacity have bigger radius
        portrayal["Layer"] = 0
        portrayal["Filled"] = "true"
        portrayal["label"] = f"Capacity: {agent.initial_capacity} | Processing {agent.initial_capacity - agent.capacity} | {agent.id}"
        color = colors['blue']
        #set Node color based on status
        if len(agent.running_tasks) > 0 :
            portrayal["r"] = .2 * agent.capacity   #nodes with bigger capacity have bigger radius
            portrayal["Layer"] = 1
            color = colors['yellow']
        elif len(agent.service_requests_queue) > 0:
            color = colors['red']
            portrayal["r"] = .2 * agent.initial_capacity
        portrayal["Color"] = color
    return portrayal


model_params = {
    "height": UserSettableParameter("slider", "Model Height", 20, 1, 1000, 5),
    "width": UserSettableParameter("slider", "Model Width", 20, 1, 1000, 5),
    "no_nodes": UserSettableParameter("slider", "Nodes Managers", 20, 1, 1000, 5),
}

canvas_element = CanvasGrid(model_draw, model_height, model_width, 1000, 1000)

server = ModularServer(SMfgModel,
                       [canvas_element],
                       "Cloud Manufacturing", model_params)
server.port = 8000