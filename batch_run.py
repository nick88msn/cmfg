import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from collections import deque
import plotly.graph_objs as go
import plotly.express as px

import utilities as u
import secrets
from flask_caching import Cache
import datetime as dt

from cmfg.model import SMfgModel, LAST_STEP, no_nodes, model_height, model_width

import cProfile
import pandas as pd

RUN_SERVER = True

GRAPH_UPDATE = 10       #axis range and data interval of graphs
TIMEOUT = 24            #cache timeout
UPDATE_INTERVAL = 5    #graphs update interval 

model = SMfgModel()

#DATACOLLECTOR
#get model data collected
data = model.datacollector.get_model_vars_dataframe()

#get agent data collected
node_managers = model.datacollector.get_agent_vars_dataframe()
print(node_managers)

if RUN_SERVER:
    #MAP data
    mapbox_access_token = secrets.MAPBOX_PUBLIC_TOKEN
    origin_dict = {
        'Rome': (41.9028,12.4964),
        'London': (51.5074,0.1278),
        'New York': (40.7128, -74.0060),
        'Salerno': (40.67545, 14.79328)
    }
    origin = origin_dict['Rome']
    nodes = [a for a in model.schedule.agents]
    nodes_pos = [a.pos for a in nodes]
    latitudes = []
    longitudes = []
    for positions in nodes_pos:
        lat, lon = u.getPointFromDistance(point1=(0,0),point2=(positions[0],positions[1]), origin=origin, grid=(model_width,model_height))
        latitudes.append(lat)
        longitudes.append(lon)

    sizes = [a.initial_capacity for a in nodes]
    capacities = [a.capacity for a in nodes]
    node_names = [a.id for a in nodes]
    labels = u.getLabels(node_names,sizes,capacities)

    #Creating the server
    app = dash.Dash(meta_tags = 
                    [{'name':"viewport", 'content':"width=device-width, initial-scale=1"}])

    #localhost
    app.scripts.config.serve_locally=True

    #Adding a cache 
    cache = Cache(app.server, config={
        'CACHE_TYPE': 'filesystem',
        'CACHE_DIR': 'cache-directory'
    })
    app.config.suppress_callback_exceptions = True
    cache.clear()
    #Caching Generator
    @cache.memoize(timeout=TIMEOUT)
    def query_data():
        # This could be an expensive data querying step
        #DATACOLLECTOR
        #get model data collected
        data = model.datacollector.get_model_vars_dataframe()[-GRAPH_UPDATE:]

        #get agent data collected
        #now = dt.datetime.now()
        #data['time'] = [now - dt.timedelta(seconds=5*i) for i in range(len(data))]

        return data

    @cache.memoize(timeout=TIMEOUT)
    def query_nodes():
        # This could be an expensive data querying step
        capacities = [a.capacity for a in nodes]
        labels = u.getLabels(node_names,sizes,capacities)
        return capacities, labels

    @cache.memoize(timeout=TIMEOUT)
    def getNodesInfo(node):
        if node == '':
            data = model.datacollector.get_agent_vars_dataframe()[-GRAPH_UPDATE * no_nodes:]
        else:
            df = model.datacollector.get_agent_vars_dataframe()[-GRAPH_UPDATE * no_nodes:]
            data = df.loc[df['ID'] == node]
        return data

    def getServices():
        service_requests = [s.order_register for s in model.order_schedule.agents]
        service_queue = [s.order_queue for s in model.order_schedule.agents]
        service_archived = [s.order_archive for s in model.order_schedule.agents]
        services = service_requests[0] + service_queue[0] + service_archived[0]
        df = pd.DataFrame(columns=['service_id', 'task_type', 'quantity','unit_price', 'logistics_cost','machine_time','delivery','status','schedule','registration_time','enter_queue_time', 'start_processing_time', 'end_processing_time' ])
        df['service_id'] = [list(a.keys())[0] for a in services]
        df['task_type'] = [lis[list(lis.keys())[0]]['task_type'] for lis in services]
        df['quantity'] = [lis[list(lis.keys())[0]]['quantity'] for lis in services]
        df['unit_price'] = [lis[list(lis.keys())[0]]['unit_price'] for lis in services]
        df['logistics_cost'] = [lis[list(lis.keys())[0]]['logistics_cost'] for lis in services]
        df['machine_time'] = [lis[list(lis.keys())[0]]['machine_time'] for lis in services]
        df['delivery'] = [lis[list(lis.keys())[0]]['delivery'] for lis in services]
        df['status'] = [lis[list(lis.keys())[0]]['status'] for lis in services]
        df['schedule'] = [lis[list(lis.keys())[0]]['schedule'] for lis in services]
        df['registration_time'] = [lis[list(lis.keys())[0]]['registration_time'] for lis in services]
        df['enter_queue_time'] = [lis[list(lis.keys())[0]]['enter_queue_time'] for lis in services]
        df['start_processing_time'] = [lis[list(lis.keys())[0]]['start_processing_time'] for lis in services]
        df['end_processing_time'] = [lis[list(lis.keys())[0]]['end_processing_time'] for lis in services]

        return df


    #Frontend
    app.layout = html.Div(children=[
        #TITLE
        html.H1('Dashboard'),
        #Upper Widgets
        html.Div(className = 'widgets', children=[
            html.Div(className='textBox', children=[
                html.H4(f'No. nodes: {len(nodes)}')
                ], style={"width": "25%", "display": "inline-block", "margin-right": "-4 px", "box-sizing": "border-box", "padding": "1%"}),

            html.Div(className='textBox', children=[
                html.H4(f'Area width: {model_width} km')
                ], style={"width": "25%", "display": "inline-block", "margin-right": "-4 px", "box-sizing": "border-box", "padding": "1%"}),

            html.Div(className='textBox', children=[
                html.H4(f'Area height: {model_height} km')
                ], style={"width": "25%", "display": "inline-block", "margin-right": "-4 px", "box-sizing": "border-box", "padding": "1%"})
            ], style={'width': '50%'}),
        #MAP
        html.Div(id = 'mapbox', children=[]),
        dcc.Interval(id='map-update', interval= 5 * UPDATE_INTERVAL * 1000),
        #TABS
        dcc.Tabs(id='tabs-home', children=[
            #Platform tab
            dcc.Tab(label="Platform", children=[
                        html.Div(id = 'capacity-graph-div', children=[]),
                        html.Div(id = 'service-analysis-div', children=[]),
                        html.Div(id = 'order-analysis-div', children=[]),
                        html.Div(id = 'completed-order-div', children=[]),
                        html.Div(id = 'completed-capacity-div', children=[])
            ]),
            #Node tab
            dcc.Tab(label="Nodes", children=[
                dcc.Dropdown(id='nodes-list', options=[{'label': s, 'value': s} for s in node_names], value=node_names, multi=False),
                html.Div(id='node-stats', children=[]),
                html.Div(id='node-capacity-graph', children=[]),
                html.Div(id='node-tasks-graph', children=[]),
                html.Div(id='node-balance-graph', children=[])
            ]),
            dcc.Tab(label="Services", children=[])
        ]),
        dcc.Interval(id='graph-update', interval= UPDATE_INTERVAL * 1000),
        # dummy signal value to trigger mesa model step
        html.Div(id='signal', style={'display': 'none'})  
    ])

    #Utilities for graphs

    def xAxisLowerRange(index):
        if index.empty: 
            return 0
        else: 
            return min(index)
    def xAxisUpperRange(index):
        if index.empty: 
            return 10
        else: 
            return max(index)

    #CALLBACK FUNCTION
    @app.callback(Output('signal', 'children'), [Input("graph-update", "n_intervals")])
    def updateData(interval):
        #BATCHRUNNING THE MODEL
        if model.clock % 20:
            cache.clear()
        for _ in range(1):
            model.step()
        
    @app.callback(Output('capacity-graph-div', 'children'), [Input("map-update", "n_intervals")])
    def updateCapacityGraph(_):
        data = query_data()
        #Capacity Figure
        capacity_fig = go.Figure()
        capacity_fig.add_trace(
            go.Scatter(x=data.index, y=data['Platform Overall Capacity'], fill='tozeroy', text='Overall Capacity', name='Platform Overall Capacity')
            )
        capacity_fig.add_trace(
            go.Scatter(x=data.index, y=data['Platform Overall Capacity'] - data['Platform Current Capacity'], fill='tozeroy', text='Current Capacity Utilization', name='Platform Capacity Utilization')
        )
        capacity_fig.update_layout(
            title_text='Cloud Manufacturing Platform',
            xaxis=dict(range=[xAxisLowerRange(data.index), xAxisUpperRange(data.index)]), yaxis=dict(range=[0, max(0,max(data['Platform Overall Capacity'])) + 10])
        )
        capacity_graph = dcc.Graph(id = 'capacity-graph', figure = capacity_fig, animate=True)
        #END GRAPHS

        return capacity_graph

    @app.callback(Output('service-analysis-div', 'children'), [Input("map-update", "n_intervals")])
    def updateServiceAnalysis(_):
        data = query_data()

        #Service Analysis Figure
        service_fig = go.Figure()
        service_fig.add_trace(
            go.Scatter(x=data.index, y=data['Service Capacity Request'], fill='tozeroy', text='Current Service Capacity Requests', name='Current Service Capacity Requests')
        )
        service_fig.add_trace(
            go.Scatter(x=data.index, y=data['Capacity Queued'], fill='tozeroy', text='Current Queued Capacity', name='Current Queued Capacity')
        )
        service_fig.add_trace(
            go.Scatter(x=data.index, y=data['Running Capacity'], fill='tozeroy', text='Current Request Processing', name='Current Request Processing')
        )
        service_fig.update_layout(
            title_text='Service Requests',
            xaxis=dict(range=[xAxisLowerRange(data.index), xAxisUpperRange(data.index)]), yaxis=dict(range=[0, max(0,max(data['Service Capacity Request']), max(data['Capacity Queued']), max(data['Running Capacity'])) + 10])
        )
        service_analysis_graph = dcc.Graph(id = 'service-analysis-graph', figure = service_fig)

        return service_analysis_graph

    @app.callback(Output('order-analysis-div', 'children'), [Input("map-update", "n_intervals")])
    def updateOrderAnalysisGraph(_):
        data = query_data()

        #Order Analysis Figure
        order_fig = go.Figure()
        order_fig.add_trace(
            go.Bar(x=data.index, y=data['Service Orders'], text='Incoming Orders', name='Incoming Orders')
        )
        order_fig.add_trace(
            go.Bar(x=data.index, y=data['Service Queued'], text='Queued Orders', name='Queued Orders')
        )
        order_fig.add_trace(
            go.Bar(x=data.index, y=data['Running Services'], text='Running Orders', name='Running Orders')
        )

        order_fig.update_layout(
            title_text='Order Requests',
            xaxis=dict(range=[xAxisLowerRange(data.index) - 1, xAxisUpperRange(data.index) + 1]), yaxis=dict(range=[0, max(0,max(data['Service Orders']),max(data['Service Queued']),max(data['Running Services'])) + 10])
        )

        order_analysis_graph = dcc.Graph(id = 'order-analysis-graph', figure = order_fig)
        return order_analysis_graph

    @app.callback(Output('completed-order-div', 'children'), [Input("map-update", "n_intervals")])
    def updateCompletedOrderGraph(_):
        data = query_data()
        #Completed vs Rejected Orders -> Figure
        completed_order_fig = go.Figure()
        completed_order_fig.add_trace(
            go.Bar(x=data.index, y=data['Completed Capacity'], text='Completed Capacity', name='Completed Orders')
        )
        completed_order_fig.add_trace(
            go.Bar(x=data.index, y=data['Rejected Capacity'], text='Rejected Capacity', name='Rejected Capacity')
        )

        completed_order_fig.update_layout(
            title_text='Capacity Evasion',
            xaxis=dict(range=[xAxisLowerRange(data.index) -1 , xAxisUpperRange(data.index) +1]), yaxis=dict(range=[0, max(0,max(data['Completed Capacity']),max(data['Rejected Capacity'])) + 10])
        )
        completed_order_graph = dcc.Graph(id = 'completed-orders-graph', figure = completed_order_fig)
        return completed_order_graph

    @app.callback(Output('completed-capacity-div', 'children'), [Input("map-update", "n_intervals")])
    def updateCapacityCompleted(_):
        data = query_data()
        #Completed vs Rejected Capacity -> 
        completed_capacity_fig = go.Figure()
        completed_capacity_fig.add_trace(
            go.Scatter(x=data.index, y=data['Completed Services'], fill='tozeroy', text='Completed Orders', name='Completed Orders')
        )
        completed_capacity_fig.add_trace(
            go.Scatter(x=data.index, y=data['Rejected Services'], fill='tozeroy', text='Rejected Orders', name='Rejected Orders')
        )

        completed_capacity_fig.update_layout(
            title_text='Order Evasion',
            xaxis=dict(range=[xAxisLowerRange(data.index), xAxisUpperRange(data.index)]), yaxis=dict(range=[0, max(0,max(data['Completed Services']),max(data['Rejected Services'])) + 10])
        )  
        completed_capacity_graph = dcc.Graph(id = 'completed-capacity-graph', figure = completed_capacity_fig)
        #END GRAPHS
        return completed_capacity_graph

    #MAP CALLBACK
    @app.callback(Output('mapbox', 'children'), [Input("map-update", "n_intervals")])
    def updateMap(_):
        #MAP
        map_fig = go.Figure()
        global latitudes, longitudes, sizes
        capacities, labels = query_nodes()

        #Actual Map
        map_fig.add_trace(go.Scattermapbox(
                    lat=latitudes,
                    lon=longitudes,
                    mode='markers',
                    marker=go.scattermapbox.Marker(
                        size=sizes,
                        color='red'
                    ),
                    text=labels,
                    hoverinfo='text'
                )
        )

        map_fig.add_trace(go.Scattermapbox(
                    lat=latitudes,
                    lon=longitudes,
                    mode='markers',
                    marker=go.scattermapbox.Marker(
                        size=capacities,
                        color='#ffffff',
                        opacity=0.7
                    ),
                    hoverinfo='none',
                ))
        
        map_fig.update_layout(
                showlegend = False,
                hovermode='closest',
                #autosize = False,
                #width = 500,
                #height = 500,
                title='Manufacturing Network',
                uirevision= False,
                mapbox=dict(
                    accesstoken=mapbox_access_token,
                    bearing=0,
                    center=go.layout.mapbox.Center(
                        lat=origin[0],
                        lon=origin[1]
                    ),
                    pitch=0,
                    zoom=9
                )
        )
        map_graph = dcc.Graph(id='plot', figure=map_fig)
        return map_graph
    
    # NODES GRAPHS

    # Node Dropdown Input
    @app.callback(Output('node-capacity-graph', 'children'), [Input("map-update", "n_intervals"), Input("nodes-list", "value")])
    def nodeCapacityGraph(interval,node):
        if type(node) == str:
            data = getNodesInfo(node)
            #Node Capacity Figure
            node_capacity_fig = go.Figure()
            node_capacity_fig.add_trace(
                go.Scatter(x=data.index.get_level_values(0), y=data['Full Capacity'], fill='tozeroy', text='Node Full Capacity', name='Node Full Capacity')
            )
            node_capacity_fig.add_trace(
                go.Scatter(x=data.index.get_level_values(0), y=data['Full Capacity'] - data['Current Capacity'], fill='tozeroy', text='Node Current Capacity Used', name='Node Current Capacity Used')
            )
            node_capacity_fig.update_layout(
                title_text=f'Node Capacity @{model.clock}',
                xaxis=dict(range=[xAxisLowerRange(data.index.get_level_values(0)), xAxisUpperRange(data.index.get_level_values(0))]), yaxis=dict(range=[0, max(0,max(data['Full Capacity'])) + 2])
            )
            node_capacity_graph = dcc.Graph(id='node-capacity-graph', figure=node_capacity_fig)
            return node_capacity_graph
        else:
            pass

    @app.callback(Output('node-tasks-graph', 'children'), [Input("map-update", "n_intervals"), Input("nodes-list", "value")])
    def nodeTasksGraph(interval,node):
        if type(node) == str:
            data = getNodesInfo(node)
            #Node Capacity Figure
            node_tasks_fig = go.Figure()
            node_tasks_fig.add_trace(
                go.Scatter(x=data.index.get_level_values(0), y=data['Tasks queue'], fill='tozeroy', text='Node Tasks queue', name='Node Tasks queue')
            )
            node_tasks_fig.add_trace(
                go.Scatter(x=data.index.get_level_values(0), y=data['Running Tasks'], fill='tozeroy', text='Node Running Tasks', name='Node Running Tasks')
            )
            node_tasks_fig.update_layout(
                title_text=f'Completed Tasks: {data["Completed Tasks"][-1]} @{model.clock}',
                xaxis=dict(range=[xAxisLowerRange(data.index.get_level_values(0)), xAxisUpperRange(data.index.get_level_values(0))]), yaxis=dict(range=[0, max(0,max(max(data['Tasks queue']),max(data['Running Tasks']))) + 2])
            )
            node_tasks_graph = dcc.Graph(id='node-tasks-graph', figure=node_tasks_fig)
            return node_tasks_graph
        else:
            pass

    #Node Balance Pie Chart
    @app.callback(Output('node-balance-graph', 'children'), [Input("map-update", "n_intervals"), Input("nodes-list", "value")])
    def NodeBalanceGraph(interval,node):
        if type(node) == str:
            data = getNodesInfo(node)
            colors = ['green', 'red', 'darkorange']
            labels = ['revenue', 'fixed costs', 'variable costs']
            #Node Capacity Figure
            revenue = data['Revenue'][-1]
            fixed_costs = data['Fixed Costs'][-1]
            variable_costs = data['Variable Costs'][-1]
            values = [revenue, fixed_costs, variable_costs]
            balance_pie_fig = go.Figure(data=[go.Pie(labels=labels,
                                        values=values, hole=.3)])
            balance_pie_fig.update_traces(hoverinfo='label+percent', textinfo='value', textfont_size=20,
                            marker=dict(colors=colors, line=dict(color='#000000', width=2)))
            balance_pie_fig.update_layout(title_text=f"Balance @{model.clock}")
            node_balance_graph = dcc.Graph(id='node-balance-graph', figure=balance_pie_fig)
            return node_balance_graph
        else:
            pass
    
    # Node Stats Widget
    @app.callback(Output('node-stats', 'children'), [Input("map-update", "n_intervals"), Input("nodes-list", "value")])
    def updateNodeStats(interval,node):
        if type(node) == str:
            stats = []
            data = getNodesInfo(node)
            location = data['Location'][-1]
            current_balance = data['Balance'][-1]
            processed_quantities = data['Processed Quantities'][-1]
            avg_rev_per_step = round(data['Revenue'][-1] / model.clock,2)
            avg_rev_per_unit = round(data['Revenue'][-1] / processed_quantities,2)

            name = html.Div(className='textBox', children=[
                            html.H3(f'Node: {data["ID"][-1]} @{model.clock}')
                            ])
            stats.append(name)

            pos = html.Div(className='textBox', children=[
                            html.P(f'Location: {location}')
                            ], style={"width": "20%", "display": "inline-block", "margin-right": "-4 px", "box-sizing": "border-box", "padding": "1%"})
            stats.append(pos)

            balance = html.Div(className='textBox', children=[
                            html.P(f'Current Balance: {current_balance}')
                            ], style={"width": "20%", "display": "inline-block", "margin-right": "-4 px", "box-sizing": "border-box", "padding": "1%"})
            stats.append(balance)

            quantities = html.Div(className='textBox', children=[
                            html.P(f'Processed Items: {processed_quantities}')
                            #html.Small('in services completed')
                            ], style={"width": "20%", "display": "inline-block", "margin-right": "-4 px", "box-sizing": "border-box", "padding": "1%"})
            stats.append(quantities)

            tasks_completed = html.Div(className='textBox', children=[
                            html.P(f'Completed tasks: {data["Completed Tasks"][-1]}')
                            ], style={"width": "20%", "display": "inline-block", "margin-right": "-4 px", "box-sizing": "border-box", "padding": "1%"})
            stats.append(tasks_completed)


            rev_per_step = html.Div(className='textBox', children=[
                            html.P(f'Avg Revenue per step: {avg_rev_per_step}')
                            ], style={"width": "20%", "display": "inline-block", "margin-right": "-4 px", "box-sizing": "border-box", "padding": "1%"})
            stats.append(rev_per_step)

            rev_per_unit = html.Div(className='textBox', children=[
                            html.P(f'Avg Revenue per unit: {avg_rev_per_unit}')
                            ], style={"width": "20%", "display": "inline-block", "margin-right": "-4 px", "box-sizing": "border-box", "padding": "1%"})
            stats.append(rev_per_unit)
            return stats

    if __name__ == '__main__':
        app.run_server(debug=False,threaded=True)
        #cProfile.run("app.run_server(debug=False,threaded=True)")
else:
    while True:
        #cProfile.run("model.step()")
        model.step()
        #node_managers = model.datacollector.get_agent_vars_dataframe()
        #print(node_managers.tail())
