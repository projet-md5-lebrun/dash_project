import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import os

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
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1("Search in Merged Data"),
    dcc.Input(id='search-input', type='text', placeholder='Enter person\'s name'),
    dcc.RangeSlider(
        id='year-slider',
        min=data['annais'].min(),
        max=data['annais'].max(),
        step=1,
        value=[data['annais'].min(), data['annais'].max()],
        marks={str(year): str(year) for year in range(int(data['annais'].min()), int(data['annais'].max())+1, 10)}
    ),
    html.Div(id='search-output'),
    html.Hr(),
    dcc.Graph(id='yearly-graph')
])

# Define the callback to update the graph
@app.callback(
    Output('yearly-graph', 'figure'),
    [Input('search-input', 'value'), Input('year-slider', 'value')]
)
def update_graph(name, year_range):
    if not name:
        return {}  # Return an empty figure when input is empty
    
    name = name.lower()
    filtered_data = data[data['preusuel'].str.lower().str.contains(name)]
    
    if year_range:
        filtered_data = filtered_data[(filtered_data['annais'] >= year_range[0]) & (filtered_data['annais'] <= year_range[1])]
    
    # Group by year and count entries
    yearly_counts = filtered_data['year'].value_counts().reset_index()
    yearly_counts.columns = ['year', 'count']
    yearly_counts = yearly_counts.sort_values('year')
    
    # Create bar chart
    fig = px.bar(yearly_counts, x='year', y='count', title=f'Number of Entries Per Year for {name.capitalize()}')
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
