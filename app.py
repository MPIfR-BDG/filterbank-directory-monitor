import redis
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import numpy as np

external_stylesheets = []
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
client = redis.StrictRedis("redis")

# from redis client:
# filterbank-directory-monitor:directory /TEST/
# filterbank-directory-monitor:coherent:file arse.fil
# filterbank-directory-monitor:coherent:bandpass [1,2,3]
# filterbank-directory-monitor:coherent:timeseries [2,3,4]
# filterbank-directory-monitor:incoherent:file other_arse.fil
# filterbank-directory-monitor:incoherent:bandpass [2,2,2]
# filterbank-directory-monitor:incoherent:timeseries [4,4,4]

colors = {
    'background': '#212124',  # To match Grafana background
    'text': '#7FDBFF'
}

app.layout = html.Div(children=[
    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [0], 'y': [0], 'type': 'line', 'name': 'Coherent Beam'},
                {'x': [0], 'y': [0], 'type': 'line', 'name': 'Incoherent Beam'}
            ],
            'layout': {
                'title': 'Bandpass Monitor',
                'transition': {
                    'duration': 500,
                    'easing': 'cubic-in-out'
                },
                'legend': {
                    'orientation': 'h',
                    'yanchor': 'bottom',
                    'y': -0.2
                },
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {
                    'color': colors['text']
                }

            }
        }
    ),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,
        n_intervals=0
    ),
    daq.ToggleSwitch(id='hold-toggle', value=False, size=50,
        label={
        "label": "Prevent updates",
        "style": {
            "color": colors['text'],
            "font-family": "arial,helvetica",
            "font-size":16,
            "margin-bottom":"10px",
            }
        },
        labelPosition="bottom", className=".toggle-switch")
], style=colors)


@app.callback(
    Output(component_id='example-graph', component_property='figure'),
    [Input('interval-component', 'n_intervals')],
    [State('example-graph', 'figure'),
     State('hold-toggle', 'value')])
def update_plot(n_clicks, figure, hold):
    if hold:
        raise PreventUpdate
    for line in figure['data']:
        line["x"] = np.arange(10)
        line["y"] = np.random.randint(0, 100, 10)
    figure["layout"]["uirevision"] = True
    print(figure)
    return figure


if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)