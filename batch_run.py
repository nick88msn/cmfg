import dash
import dash_core_components as dcc
import dash_html_components as html
from collections import deque
import plotly.graph_objs as go
import plotly.express as px

from cmfg.model import SMfgModel, LAST_STEP

model = SMfgModel()

#batch launch the model
for _ in range(LAST_STEP):
    model.step()

#get model data collected
data = model.datacollector.get_model_vars_dataframe()

print(data)

#get agent data collected
node_managers = model.datacollector.get_agent_vars_dataframe()
print(node_managers)

#Capacity Figure
capacity_fig = go.Figure()

capacity_fig.add_trace(
    go.Scatter(x=data.index, y=data['Platform Overall Capacity'], fill='tozeroy', text='Overall Capacity', name='Platform Overall Capacity')
    )
capacity_fig.add_trace(
    go.Scatter(x=data.index, y=data['Platform Overall Capacity'] - data['Platform Current Capacity'], fill='tozeroy', text='Current Capacity Utilization', name='Platform Capacity Utilization')
)

capacity_fig.update_layout(
    title_text='Cloud Manufacturing Platform'
)

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
    title_text='Service Requests'
)

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
    title_text='Order Requests'
)

service_fig.update_layout(
    title_text='Orders Analysis'
)

#Completed vs Rejected Orders -> Figure
completed_order_fig = go.Figure()
completed_order_fig.add_trace(
    go.Bar(x=data.index, y=data['Completed Capacity'], text='Completed Capacity', name='Completed Orders')
)
completed_order_fig.add_trace(
    go.Bar(x=data.index, y=data['Rejected Capacity'], text='Rejected Capacity', name='Rejected Capacity')
)

completed_order_fig.update_layout(
    title_text='Capacity Evasion'
)

#Completed vs Rejected Capacity -> 
completed_capacity_fig = go.Figure()
completed_capacity_fig.add_trace(
    go.Scatter(x=data.index, y=data['Completed Services'], fill='tozeroy', text='Completed Orders', name='Completed Orders')
)
completed_capacity_fig.add_trace(
    go.Scatter(x=data.index, y=data['Rejected Services'], fill='tozeroy', text='Rejected Orders', name='Rejected Orders')
)

completed_capacity_fig.update_layout(
    title_text='Order Evasion'
)

app = dash.Dash()

app.layout = html.Div(children=[
    html.H1('Dashboard'),
    dcc.Graph(id = 'capacity-graph', figure = capacity_fig),
    dcc.Graph(id = 'service-analysis-graph', figure = service_fig),
    dcc.Graph(id = 'order-analysis-graph', figure = order_fig),
    dcc.Graph(id = 'completed-orders-graph', figure = completed_order_fig),
    dcc.Graph(id = 'completed-capacity-graph', figure = completed_capacity_fig)      
])

if __name__ == '__main__':
    app.run_server(debug=True,threaded=True)