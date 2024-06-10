import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import os  # Add this import for handling file paths

# Get the current directory
current_directory = os.path.dirname(os.path.abspath(__file__))

# Load and preprocess the data
data = pd.read_csv(os.path.join(current_directory, 'data/merged_data.csv'), sep=';') 
data.fillna('', inplace=True)

# Replace 'preusuel' with the correct column name containing the person's name
data['year'] = pd.to_datetime(data['annais']).dt.year

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1("Search in Merged Data"),
    dcc.Input(id='search-input', type='text', placeholder='Enter person\'s name'),
    html.Div(id='search-output'),
    html.Hr(),
    dcc.Graph(id='yearly-graph')
])

# Define the callback to update the graph
@app.callback(
    Output('yearly-graph', 'figure'),
    [Input('search-input', 'value')]
)
def update_graph(name):
    if not name:
        return {}  # Return an empty figure when input is empty
    
    name = name.lower()
    filtered_data = data[data['preusuel'].str.lower().str.contains(name)]
    
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
