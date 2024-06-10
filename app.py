import os
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import geopandas as gpd

# Get the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Load your GeoJSON file
geojson_path = os.path.join(current_directory, 'data/departements.geojson')
gdf = gpd.read_file(geojson_path)

# Extract code and nom properties
code_nom_df = gdf[['code', 'nom']]

# Load and preprocess the data
data = pd.read_csv(os.path.join(current_directory, 'data/merged_data.csv'), sep=';')
data.fillna('', inplace=True)

# Convert 'annais' to numeric
data['annais'] = pd.to_numeric(data['annais'], errors='coerce')

# Ensure type of 'dpt' is string
data['dpt'] = data['dpt'].astype(str)

# Replace 'preusuel' with the correct column name containing the person's name
data['year'] = data['annais'].astype(int)
# merge the data with the code_nom_df
df_merged = pd.merge(data, code_nom_df, left_on='dpt', right_on='code', how='left')

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
        dbc.Col([
            dcc.RadioItems(
                id='display-option',
                options=[
                    {'label': 'Count', 'value': 'count'},
                    {'label': 'Proportion', 'value': 'proportion'}
                ],
                value='count'
            )
        ], width=3),
    ]),
    html.Div(id='search-output', className="text-center"),
    html.Hr(),
    dcc.Graph(id='yearly-graph'),
    dcc.Graph(id='top-shops-graph'),  # Add a new graph for top shops
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

@app.callback(
    [Output('yearly-graph', 'figure'), Output('search-output', 'children')],
    [Input('search-input', 'value'), Input('year-slider', 'value'), Input('gender-dropdown', 'value'), Input('display-option', 'value'), Input('interval-component', 'n_intervals')]  # Add this input
)
def update_graph(name, year_range, gender, display_option, n_intervals):
    if name is None or name == '':
        return dash.no_update, dash.no_update

    name = name.lower()
    filtered_data = df_merged[df_merged['preusuel'].str.lower().str.contains(name)]

    if year_range is not None:
        filtered_data = filtered_data[(filtered_data['annais'] >= year_range[0]) & (filtered_data['annais'] <= year_range[1])]

    if gender != 'All':
        filtered_data = filtered_data[filtered_data['sexe'] == gender]

    # Group by year and count entries
    yearly_counts = filtered_data.groupby('year')['nombre'].sum().reset_index()
    yearly_counts.columns = ['year', 'count']

    # Calculate total counts for each year
    total_counts = data.groupby('year')['nombre'].sum().reset_index()
    total_counts.columns = ['year', 'total']

    # Merge yearly_counts and total_counts
    yearly_counts = pd.merge(yearly_counts, total_counts, on='year')

    # Calculate proportion
    yearly_counts['proportion'] = yearly_counts['count'] / yearly_counts['total']

    # Sort by year
    yearly_counts = yearly_counts.sort_values('year')

    # Create line chart
    if display_option == 'count':
        fig = px.line(yearly_counts, x='year', y='count', title=f'Number of Entries Per Year for {name.capitalize()}')
    else:
        fig = px.line(yearly_counts, x='year', y='proportion', title=f'Proportion of Entries Per Year for {name.capitalize()}')

    if len(filtered_data) == 0:
        return dash.no_update, html.Div("No results found for '{}'. Please try again.".format(name))
    else:
        if n_intervals == 1:  # This is to avoid displaying the message when the app loads
            return fig, dash.no_update
        else:
            return fig, html.Div("Results for '{}'.".format(name))
@app.callback(
    Output('top-shops-graph', 'figure'), 
    [Input('search-input', 'value'), Input('year-slider', 'value'), Input('gender-dropdown', 'value'), Input('display-option', 'value'), Input('interval-component', 'n_intervals')]
)
def update_top_departments_graph(name, year_range, gender, display_option, n_intervals):
    if not name:
        return dash.no_update

    # Filter the data for the given name
    filtered_data = df_merged[df_merged['preusuel'].str.lower().str.contains(name.lower())]

    if filtered_data.empty:
        return dash.no_update

    # Apply other filters
    if year_range is not None:
        filtered_data = filtered_data[(filtered_data['annais'] >= year_range[0]) & (filtered_data['annais'] <= year_range[1])]

    if gender != 'All':
        filtered_data = filtered_data[filtered_data['sexe'] == gender]

    # Group by department and count entries
    department_counts = filtered_data.groupby('nom')['nombre'].sum().reset_index()
    department_counts.columns = ['Department', 'Count']

    # Calculate total counts for each department
    total_counts = df_merged.groupby('nom')['nombre'].sum().reset_index()
    total_counts.columns = ['Department', 'Total']

    # Merge department_counts and total_counts
    department_counts = pd.merge(department_counts, total_counts, on='Department')

    # Calculate proportion
    department_counts['Proportion'] = department_counts['Count'] / department_counts['Total']
    
    # Sort by proportion in descending order and select the top 5 departments
    top_departments = department_counts.sort_values('Proportion', ascending=False).head(5)

    # Create bar chart
    fig = px.bar(top_departments, x='Department', y='Proportion', title=f'Top 5 Departments for {name.capitalize()}',
                 text='Proportion', labels={'Proportion': 'Proportion of Total Names'}, color='Department')
    
    fig.update_yaxes(tickformat=".2%")

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8052)
