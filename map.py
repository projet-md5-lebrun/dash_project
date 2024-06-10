@app.callback(
    Output('map-graph', 'figure'),
    [Input('search-input', 'value'),
     Input('year-slider', 'value'),
     Input('multi-select-dropdown', 'value'),
     Input('gender-dropdown', 'value'),
     Input('department-dropdown', 'value'),
     Input('display-option', 'value')]
)
def update_map_figure(search_name, year_range, selected_departments, gender, department, display_option):
    try:
        # Filter data based on inputs
        filtered_data = df_merged[
            (df_merged['annais'] >= year_range[0]) & 
            (df_merged['annais'] <= year_range[1])
        ]
        
        if search_name:
            filtered_data = filtered_data[filtered_data['name'].str.contains(search_name, case=False)]

        if selected_departments:
            filtered_data = filtered_data[filtered_data['department'].isin(selected_departments)]

        if gender != 'All':
            filtered_data = filtered_data[filtered_data['gender'] == gender]

        if department != 'All':
            filtered_data = filtered_data[filtered_data['department'] == department]

        # Aggregate data based on display option
        if display_option == 'count':
            aggregated_data = filtered_data.groupby('department').size().reset_index(name='count')
        else:
            total_count = filtered_data.shape[0]
            aggregated_data = filtered_data.groupby('department').size().reset_index(name='count')
            aggregated_data['proportion'] = aggregated_data['count'] / total_count
        
        geojson_data = json.loads('data/departements.geojson')
        # Create the map figure
        fig = px.choropleth_mapbox(
            aggregated_data,
            geojson=geojson_data,  # Ensure you have your geojson data loaded
            locations='department',
            color='count' if display_option == 'count' else 'proportion',
            hover_name='department',
            color_continuous_scale="Viridis",
            scope="europe"
        )
        fig.update_geos(fitbounds="locations", visible=False)

        return fig
    
    except Exception as e:
        # Log the error and return an empty figure
        print(f"Error updating map figure: {e}")
        return px.choropleth()