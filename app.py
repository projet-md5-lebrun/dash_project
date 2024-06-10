import os
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Get the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Load and preprocess the data
data = pd.read_csv(os.path.join(current_directory, 'data/merged_data.csv'), sep=';')
data.fillna('', inplace=True)

# Convert 'annais' to numeric
data['annais'] = pd.to_numeric(data['annais'], errors='coerce')

# Replace 'preusuel' with the correct column name containing the person's name
data['year'] = data['annais'].astype(int)

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = dbc.Container([
    html.H1("Search in Merged Data", className="text-center"),
    dbc.Row([
        dbc.Col([
            dcc.Input(id='search-input', type='text', placeholder='Enter person\'s name', value='camille'),
            html.Button("Clear", id="clear-button", n_clicks=0)
        ], width=6),
        dbc.Col([
            dcc.RangeSlider(
                id='year-slider',
                min=data['annais'].min(),
                max=data['annais'].max(),
                step=1,
                value=[data['annais'].min(), data['annais'].max()],
                marks={str(year): str(year) for year in range(int(data['annais'].min()), int(data['annais'].max())+1, 10)}
            )
        ], width=6),
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id='gender-dropdown',
                options=[
                    {'label': 'Male', 'value': 1},
                    {'label': 'Female', 'value': 2},
                    {'label': 'All', 'value': 'All'}
                ],
                value='All'
            )
        ], width=3),
    ]),
    html.Div(id='search-output', className="text-center"),
    html.Hr(),
    dcc.Graph(id='yearly-graph'),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)  # Add this line
], fluid=True)

# Define the callback to clear the search input
@app.callback(
    Output('search-input', 'value'),
    [Input('clear-button', 'n_clicks')]
)
def clear_search_input(n_clicks):
    if n_clicks > 0:
        return ''
    return dash.no_update

# Define the callback to update the graph and display a message when no results are found
@app.callback(
    [Output('yearly-graph', 'figure'), Output('search-output', 'children')],
    [Input('search-input', 'value'), Input('year-slider', 'value'), Input('gender-dropdown', 'value'), Input('interval-component', 'n_intervals')]  # Add this input
)
def update_graph(name, year_range, gender, n_intervals):
    if name is None or name == '':
        return dash.no_update, dash.no_update

    name = name.lower()
    filtered_data = data[data['preusuel'].str.lower().str.contains(name)]

    if year_range is not None:
        filtered_data = filtered_data[(filtered_data['annais'] >= year_range[0]) & (filtered_data['annais'] <= year_range[1])]

    if gender != 'All':
        filtered_data = filtered_data[filtered_data['sexe'] == gender]

    # Group by year and count entries
    yearly_counts = filtered_data['year'].value_counts().reset_index()
    yearly_counts.columns = ['year', 'count']
    yearly_counts = yearly_counts.sort_values('year')

    # Create bar chart
    fig = px.line(yearly_counts, x='year', y='count', title=f'Number of Entries Per Year for {name.capitalize()}', 
                  text= "count")
    fig.update_traces(textposition='bottom right')
    if len(filtered_data) == 0:
        return dash.no_update, html.Div("No results found for '{}'. Please try again.".format(name))
    else:
        if n_intervals == 1:  # This is to avoid displaying the message when the app loads
            return fig, dash.no_update
        else:
            return fig, html.Div("Results for '{}'.".format(name))

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
