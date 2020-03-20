import redis
import dash
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import numpy as np

NAMESPACE = "filterbank-directory-monitor"

external_stylesheets = []
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
client = redis.StrictRedis("apsuse-monitor-redis")

# from redis client:
# filterbank-directory-monitor:directory /TEST/
# filterbank-directory-monitor:coherent:file arse.fil
# filterbank-directory-monitor:coherent:bandpass [] #packed numpy array
# filterbank-directory-monitor:incoherent:file other_arse.fil
# filterbank-directory-monitor:incoherent:bandpass [] #packed numpy array

colors = {
    'background': '#212124',  # To match Grafana background
    'text': '#7FDBFF'
}

app.layout = html.Div(children=[
    html.H4(id='directory-label', children="Current directory: ", style= {
        'color': '#CCCCCC',
        'margin-bottom': "0px",
        'margin-left': "10px",
        'padding-top': "10px"
        }),
    html.H4(id='cb-file-label', children="CB file: ", style= {
        'color': '#CCCCCC',
        'margin-bottom': "0px",
        'margin-left': "10px",
        'padding-top': "0px"
        }),
    html.H4(id='ib-file-label', children="IB file: ", style= {
        'color': '#CCCCCC',
        'margin-bottom': "0px",
        'margin-left': "10px",
        'padding-top': "0px"
        }),
    dcc.Graph(
        id='bandpass-graph',
        figure={
            'data': [
                {'x': [0], 'y': [0], 'type': 'line', 'name': 'Coherent Beam'},
                {'x': [0], 'y': [0], 'type': 'line', 'name': 'Incoherent Beam'}
            ],
            'layout': {
                'title': 'Bandpass Monitor',
                'xaxis': {
                    'title': 'Frequency (MHz)'
                },
                'yaxis': {
                    'title': 'Selected statistic'
                },
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
        },
    ),
    dcc.Interval(
        id='interval-component',
        interval=10*1000,
        n_intervals=0
    ),
    html.Div(id='controls-div', children=[

        html.Div(id='toggle-div', children=[
            daq.ToggleSwitch(
                id='hold-toggle', value=False, size=50,
                label={
                    "label": "Prevent updates",
                    "style": {
                        "color": colors['text'],
                        "font-family": "arial,helvetica",
                        "font-size":16,
                        "margin-bottom":"10px"
                    }
                },
                labelPosition="bottom",
                className=".toggle-switch")
            ],
            style={
                'float': 'left',
                'left': '30px',
                'width': '200px',
                'background-color': '#212124'
            }),

        html.Div(id='dropdown-div', children=[
            html.Label([
                "Select statistic",
                dcc.Dropdown(
                    id='statistic-dropdown',
                    options=[
                        {'label': 'Mean', 'value': 'mean'},
                        {'label': 'Standard deviation', 'value': 'std'}
                    ],
                    value='mean'
                )],
                style={
                    "color": colors['text'],
                    "font-family": "arial,helvetica",
                    "font-size":16,
                    "margin-bottom":"10px"
                })],
            style={
                'float': 'left',
                'left': '30px',
                'width': '200px',
                'background-color': '#212124'
            }),
        ],
        style={
            'background-color': '#212124'
        })
], style=colors)


def upack_numpy_array(packed):
    """
    Unpack a numpy array from a string

    :param      packed:  Numpy array that has been packed as
                         [('frequency', 'float32', ), ('power', 'float32')]
    :type       packed:  { type_description }
    """
    return np.frombuffer(packed, dtype=[
       ("frequency", "float32"),
       ("mean", "float32"),
       ("std", "float32")])


@app.callback(
    [Output(component_id='bandpass-graph', component_property='figure'),
     Output(component_id='directory-label', component_property='children'),
     Output(component_id='cb-file-label', component_property='children'),
     Output(component_id='ib-file-label', component_property='children')],
    [Input('interval-component', 'n_intervals'),
     Input('statistic-dropdown', 'value')],
    [State('bandpass-graph', 'figure'),
     State('hold-toggle', 'value')])
def update_plot(n_intervals, stat_selection, figure, hold):
    if hold:
        raise PreventUpdate
    for line in figure['data']:
        if line["name"] == 'Coherent Beam':
            beam = upack_numpy_array(
                client.get("{}:coherent:bandpass".format(NAMESPACE)))
        elif line["name"] == 'Incoherent Beam':
            beam = upack_numpy_array(
                client.get("{}:incoherent:bandpass".format(NAMESPACE)))
        else:
            print("Unknown data set: '{}'".fomat(line["name"]))
        line["x"] = beam["frequency"]/1e6
        line["y"] = beam[stat_selection]
    figure["layout"]["uirevision"] = True
    figure["layout"]["yaxis"]["title"] = stat_selection.capitalize()
    # I would like to update the figure title
    # here but it seems to be bugged out
    dir_label = "Current directory:    {}".format(
        client.get("{}:directory".format(NAMESPACE)).decode())
    cb_file = "CB file:    {}".format(
        client.get("{}:coherent:file".format(NAMESPACE)).decode())
    ib_file = "IB file:    {}".format(
        client.get("{}:incoherent:file".format(NAMESPACE)).decode())
    return figure, dir_label, cb_file, ib_file


if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
