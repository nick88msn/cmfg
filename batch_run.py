import dash
from dash.dependencies import Input, Output
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

GRAPH_UPDATE = 50

model = SMfgModel()

#DATACOLLECTOR
#get model data collected
data = model.datacollector.get_model_vars_dataframe()

print(data)

#get agent data collected
node_managers = model.datacollector.get_agent_vars_dataframe()
print(node_managers)



#MAP
mapbox_access_token = secrets.MAPBOX_PUBLIC_TOKEN
no_nodes = no_nodes
fig = go.Figure()

origin_dict = {
        'Rome': (41.9028,12.4964),
        'London': (51.5074,0.1278),
        'New York': (40.7128, -74.0060)
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

map_fig = go.Figure()

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
        )
)

map_fig.update_layout(
        showlegend = False,
        hovermode='closest',
        #autosize = False,
        #width = 500,
        #height = 500,
        title='Manufacturing Network',
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

app = dash.Dash()
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})
app.config.suppress_callback_exceptions = True
TIMEOUT = 3
cache.clear()

@cache.memoize(timeout=TIMEOUT)
def query_data():
    # This could be an expensive data querying step
    #DATACOLLECTOR
    #get model data collected
    data = model.datacollector.get_model_vars_dataframe()[-GRAPH_UPDATE:]

    #get agent data collected
    node_managers = model.datacollector.get_agent_vars_dataframe()[-GRAPH_UPDATE:]
    now = dt.datetime.now()
    #node_managers['time'] = [now - dt.timedelta(seconds=5*i) for i in range(len(node_managers))]
    #data['time'] = [now - dt.timedelta(seconds=5*i) for i in range(len(data))]

    return data, node_managers


app.layout = html.Div(children=[
    html.H1('Dashboard'),
    html.Div(id = 'mapbox', children=[
        dcc.Graph(id='plot', figure=map_fig)
    ]),
    html.Div(id = 'capacity-graph-div', children=[]),
    html.Div(id = 'service-analysis-div', children=[]),
    html.Div(id = 'order-analysis-div', children=[]),
    html.Div(id = 'completed-order-div', children=[]),
    html.Div(id = 'completed-capacity-div', children=[]),
    dcc.Interval(id='graph-update', interval= 3 * 1000)     
])

@app.callback([
    Output('capacity-graph-div', 'children'),
    Output('service-analysis-div', 'children'),
    Output('order-analysis-div', 'children'),
    Output('completed-order-div', 'children'),
    Output('completed-capacity-div', 'children')
    ], 
    [
        Input("graph-update", "n_intervals")
        ])
def updateModel(_):
    #BATCHRUNNING THE MODEL
    for _ in range(1):
        model.step()

    data, node_managers = query_data()

    #GRAPHS & FIGURES
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
        xaxis=dict(range=[min(data.index), max(data.index)]), yaxis=dict(range=[0, max(data['Platform Overall Capacity']) + 10])
    )
    capacity_graph = dcc.Graph(id = 'capacity-graph', figure = capacity_fig, animate=True)

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
        xaxis=dict(range=[min(data.index), max(data.index)]), yaxis=dict(range=[0, max(max(data['Service Capacity Request']), max(data['Capacity Queued']), max(data['Running Capacity'])) + 10])
    )
    service_analysis_graph = dcc.Graph(id = 'service-analysis-graph', figure = service_fig)

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
        xaxis=dict(range=[min(data.index), max(data.index) + 1]), yaxis=dict(range=[0, max(max(data['Service Orders']),max(data['Service Queued']),max(data['Running Services'])) + 10])
    )

    order_analysis_graph = dcc.Graph(id = 'order-analysis-graph', figure = order_fig)

    #Completed vs Rejected Orders -> Figure
    completed_order_fig = go.Figure()
    completed_order_fig.add_trace(
        go.Bar(x=data.index[-GRAPH_UPDATE:], y=data['Completed Capacity'][-GRAPH_UPDATE:], text='Completed Capacity', name='Completed Orders')
    )
    completed_order_fig.add_trace(
        go.Bar(x=data.index[-GRAPH_UPDATE:], y=data['Rejected Capacity'][-GRAPH_UPDATE:], text='Rejected Capacity', name='Rejected Capacity')
    )

    completed_order_fig.update_layout(
        title_text='Capacity Evasion',
        xaxis=dict(range=[min(data.index), max(data.index) +1]), yaxis=dict(range=[0, max(max(data['Completed Capacity']),max(data['Rejected Capacity'])) + 10])
    )
    completed_order_graph = dcc.Graph(id = 'completed-orders-graph', figure = completed_order_fig)

    #Completed vs Rejected Capacity -> 
    completed_capacity_fig = go.Figure()
    completed_capacity_fig.add_trace(
        go.Scatter(x=data.index[-GRAPH_UPDATE:], y=data['Completed Services'][-GRAPH_UPDATE:], fill='tozeroy', text='Completed Orders', name='Completed Orders')
    )
    completed_capacity_fig.add_trace(
        go.Scatter(x=data.index[-GRAPH_UPDATE:], y=data['Rejected Services'][-GRAPH_UPDATE:], fill='tozeroy', text='Rejected Orders', name='Rejected Orders')
    )

    completed_capacity_fig.update_layout(
        title_text='Order Evasion',
        xaxis=dict(range=[max(0, max(data.index) - GRAPH_UPDATE + 2), max(data.index[-GRAPH_UPDATE:])]), yaxis=dict(range=[0, max(max(data['Completed Services']),max(data['Rejected Services'])) + 10])
    )  
    completed_capacity_graph = dcc.Graph(id = 'completed-capacity-graph', figure = completed_capacity_fig)
    #END GRAPHS

    return capacity_graph, service_analysis_graph, order_analysis_graph, completed_order_graph, completed_capacity_graph

if __name__ == '__main__':
    app.run_server(debug=True,threaded=True)