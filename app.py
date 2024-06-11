import os
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import geopandas as gpd
import json

# Get the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Load your GeoJSON file
geojson_path = os.path.join(current_directory, 'data/departements.geojson')
gdf = gpd.read_file(geojson_path)

# Extract code and nom properties
code_nom_df = gdf[['code', 'nom', 'geometry']]

# Load and preprocess the data
data = pd.read_csv(
    os.path.join(
        current_directory,
        'data/merged_data.csv'),
    sep=';')
data.fillna('', inplace=True)

# Convert 'annais' to numeric
data['annais'] = pd.to_numeric(data['annais'], errors='coerce')

# Ensure type of 'dpt' is string and add leading zeros if necessary
data['dpt'] = data['dpt'].astype(str).str.zfill(2)
code_nom_df['code'] = code_nom_df['code'].astype(str).str.zfill(2)

# Replace 'preusuel' with the correct column name containing the person's name
data['year'] = data['annais'].astype(int)
# merge the data with the code_nom_df
df_merged = pd.merge(
    data,
    code_nom_df,
    left_on='dpt',
    right_on='code',
    how='left')
df_merged['nom'] = df_merged['nom'].astype(str)
geojson_data = json.loads(gdf.to_json())

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = dbc.Container([
    dbc.Card(
        dbc.CardBody([
            html.H1(
                "Number of births by name",
                className="text-center mb-4"),

            dbc.Row([
                dbc.Col([
                    dcc.Input(
                        id='search-input',
                        type='text',
                        placeholder="Enter person's name",
                        value='Camille',
                        className="form-control"
                    ),
                    html.Button(
                        "Clear",
                        id="clear-button",
                        n_clicks=0,
                        className="btn btn-danger mt-2")
                ], width=6),

                dbc.Col([
                    dcc.RangeSlider(
                        id='year-slider',
                        min=data['annais'].min(),
                        max=data['annais'].max(),
                        step=1,
                        value=[data['annais'].min(), data['annais'].max()],
                        marks={str(year): str(year) for year in range(
                            int(data['annais'].min()), int(data['annais'].max()) + 1, 10)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], width=6)
            ]),

            html.Br(),

            html.Label('Select departement', className="form-label"),
            dcc.Dropdown(
                id='multi-select-dropdown',
                options=[{'label': department, 'value': department}
                         for department in sorted(df_merged['nom'].unique())],
                multi=True,
                className="mb-4"
            ),

            dbc.Row([
                dbc.Col([
                    html.Label('Gender Dropdown', className="form-label"),
                    dcc.Dropdown(
                        id='gender-dropdown',
                        options=[
                            {'label': 'Male', 'value': 1},
                            {'label': 'Female', 'value': 2},
                            {'label': 'All', 'value': 'All'}
                        ],
                        value='All',
                        className="mb-4"
                    )
                ], width=4),


                dbc.Col([
                    html.Label('Display Option', className="form-label"),
                    dcc.RadioItems(
                        id='display-option',
                        options=[
                            {'label': 'Count', 'value': 'count'},
                            {'label': 'Proportion', 'value': 'proportion'}
                        ],
                        value='count',
                        className="form-check"
                    )
                ], width=4)
            ]),

            html.Div(id='search-output', className="text-center mt-4"),

            html.Hr(),

            # Position the map at the top
            dbc.Row([
                dbc.Col(
                    dcc.Graph(id='map-graph'),
                    width=8
                ),
                dbc.Col(
                    dcc.Graph(id='top-shops-graph'),
                    width=4
                )
            ]),

            html.Br(),

            dcc.Graph(id='yearly-graph')
        ])
    ),
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
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


@app.callback([Output('yearly-graph',
                      'figure'),
               Output('search-output',
                      'children')],
              [Input('search-input',
                     'value'),
               Input('year-slider',
                     'value'),
               Input('gender-dropdown',
                     'value'),
               Input('display-option',
                     'value'),
               Input('interval-component',
                     'n_intervals'),
               Input('multi-select-dropdown',
                     'value')])
def update_graph(
        name,
        year_range,
        gender,
        display_option,
        n_intervals,
        department):
    if name is None or name == '':
        return dash.no_update, dash.no_update

    name = name.lower()
    filtered_data = df_merged[df_merged['preusuel'].str.lower(
    ).str.contains(name)]

    if year_range is not None:
        filtered_data = filtered_data[(filtered_data['annais'] >= year_range[0]) & (
            filtered_data['annais'] <= year_range[1])]

    if gender != 'All':
        filtered_data = filtered_data[filtered_data['sexe'] == gender]
    if department is not None:
        filtered_data = filtered_data[filtered_data['nom'].isin(department)]

    # Group by year and count entries
    yearly_counts = filtered_data.groupby('year')['nombre'].sum().reset_index()
    yearly_counts.columns = ['year', 'count']

    # Calculate total counts for each year
    total_counts = data.groupby('year')['nombre'].sum().reset_index()
    total_counts.columns = ['year', 'total']

    # Merge yearly_counts and total_counts
    yearly_counts = pd.merge(yearly_counts, total_counts, on='year')

    # Calculate proportion
    yearly_counts['proportion'] = yearly_counts['count'] / \
        yearly_counts['total']

    # Sort by year
    yearly_counts = yearly_counts.sort_values('year')

    # Create line chart
    if display_option == 'count':
        fig = px.line(
            yearly_counts,
            x='year',
            y='count',
            title=f'Number of Entries Per Year for {
                name.capitalize()}')
    else:
        fig = px.line(
            yearly_counts,
            x='year',
            y='proportion',
            title=f'Proportion of Entries Per Year for {
                name.capitalize()}')

    if len(filtered_data) == 0:
        return dash.no_update, html.Div(
            "No results found for '{}'. Please try again.".format(name))
    else:
        if n_intervals == 1:  # This is to avoid displaying the message when the app loads
            return fig, dash.no_update
        else:
            return fig, html.Div("Results for '{}'.".format(name))


@app.callback(Output('top-shops-graph',
                     'figure'),
              [Input('search-input',
                     'value'),
               Input('year-slider',
                     'value'),
               Input('gender-dropdown',
                     'value'),
               Input('display-option',
                     'value'),
               Input('interval-component',
                     'n_intervals')])
def update_top_departments_graph(
        name,
        year_range,
        gender,
        display_option,
        n_intervals):
    if name is None or name == '':
        return dash.no_update, dash.no_update

    name = name.lower()
    filtered_data = df_merged[df_merged['preusuel'].str.lower(
    ).str.contains(name)]

    # Apply other filters
    if year_range is not None:
        filtered_data = filtered_data[(filtered_data['annais'] >= year_range[0]) & (
            filtered_data['annais'] <= year_range[1])]

    if gender != 'All':
        filtered_data = filtered_data[filtered_data['sexe'] == gender]

    # Group by department and count entries
    department_counts = filtered_data.groupby(
        'nom')['nombre'].sum().reset_index()
    department_counts.columns = ['Department', 'Count']

    # Sort by count in descending order
    department_counts = department_counts.sort_values('Count', ascending=False)

    # Calculate total number of names
    total_names = department_counts['Count'].sum()

    # Calculate percentage
    department_counts['Percentage'] = (
        department_counts['Count'] / total_names) * 100

    # Select the top 5 departments
    top_departments = department_counts.head(5)
    top_departments = top_departments.sort_values('Percentage', ascending=True)

    if display_option == 'count':
        # Create bar chart
        fig = px.bar(
            top_departments, x='Count', y='Department', title=f'Top 5 Departments for {
                name.capitalize()}', text='Count', labels={
                'Number': 'Number of Total Names'}, orientation='h')
        fig.update_layout(barcornerradius=30)
    else:
        # Create bar chart
        fig = px.bar(
            top_departments,
            y='Department',
            x='Percentage',
            title=f'Top 5 Departments for {
                name.capitalize()}',
            text='Percentage',
            labels={
                'Percentage': 'Percentage of Total Names'},
            orientation='h')
        fig.update_layout(barcornerradius=30)
        fig.update_traces(texttemplate='%{text:.2s}%', textposition='outside')

    return fig


@app.callback(
    Output('map-graph', 'figure'),
    [Input('search-input', 'value'),
     Input('year-slider', 'value'),
     Input('gender-dropdown', 'value'),
     Input('display-option', 'value')]
)
def update_map_figure(name, year_range, gender, display_option):
    if name is None or name == '':
        return dash.no_update

    name = name.lower()
    filtered_data = df_merged[df_merged['preusuel'].str.lower(
    ).str.contains(name)]

    if year_range is not None:
        filtered_data = filtered_data[(filtered_data['annais'] >= year_range[0]) & (
            filtered_data['annais'] <= year_range[1])]

    if gender != 'All':
        filtered_data = filtered_data[filtered_data['sexe'] == gender]

    if filtered_data.empty:
        return dash.no_update

    # Group by department and count entries
    if display_option == 'count':
        department_counts = filtered_data.groupby(
            'nom')['nombre'].sum().reset_index()
        department_counts.columns = ['department', 'count']
    else:
        department_counts = filtered_data.groupby(
            'nom')['nombre'].sum().reset_index()
        department_counts.columns = ['department', 'count']
        total_count = department_counts['count'].sum()
        department_counts['proportion'] = department_counts['count'] / total_count

    # Create the map figure
    if display_option == 'count':
        fig = px.choropleth_mapbox(
            department_counts,
            geojson=geojson_data,
            locations='department',
            featureidkey="properties.nom",
            color='count',
            hover_name='department',
            color_continuous_scale="reds",
            mapbox_style="carto-positron",
            title=f'Number of Entries Per Department for {name.capitalize()}',
            center={"lat": 46.603354, "lon": 1.888334},
            labels={'count': 'Number of Entries'},
            zoom=3,
        )
    else:
        fig = px.choropleth(
            department_counts,
            geojson=geojson_data,
            locations='department',
            featureidkey="properties.nom",
            color='proportion',
            hover_name='department',
            color_continuous_scale="reds",
            projection="arto-positron",
            title=f'Proportion of Entries Per Department for {
                name.capitalize()}',
            center={
                "lat": 46.603354,
                "lon": 1.888334},
            zoom=3,
        )

    fig.update_geos(fitbounds="locations", visible=False)

    # Set the zoom level to 4
    fig.update_geos(
        projection_scale=4,
        center={
            "lat": 46.603354,
            "lon": 1.888334})

    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8052)
