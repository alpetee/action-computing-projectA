"""
Author: Allie Peterson
Credits: storytelling with data
Course: CS150 Community Action Computing, Prof Mike Ryu
"""


import calendar
import dash
from dash import dcc, html
import plotly.express as px
import requests
import pandas as pd

# Load and preprocess the data
df = pd.read_csv('ad_viz_plotval_data.csv')
df['Date'] = pd.to_datetime(df['Date'])  # Convert the Date column to datetime
df['Month'] = df['Date'].dt.month  # Extract the month from the Date

# Calculate the average PM2.5 for each 'County' and month
avg_pm25 = df.groupby(['County', 'Month'])['Daily Mean PM2.5 Concentration'].mean().reset_index()

# Get California county GeoJSON
geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/california-counties.geojson"
response = requests.get(geojson_url)
counties_geojson = response.json()

# Calculate global min and max for PM2.5 across all months for a consistent color scale
global_min = avg_pm25['Daily Mean PM2.5 Concentration'].min()
global_max = avg_pm25['Daily Mean PM2.5 Concentration'].max()

# Create a Dash app
app = dash.Dash(__name__)

# Define the app layout
app.layout = html.Div([
    html.H1(
        "California Monthly PM2.5 Averages",
        style={
            'font-family': 'Arial, sans-serif',  # Change to your desired font
            'text-align': 'center',  # Center the title
            'font-size': '36px',  # Optional: Adjust the font size as needed
            'font-weight': 'bold',  # Optional: Make the title bold
        }
    ),

    # Slider for selecting the month
    html.Div(
        dcc.Slider(
            id='month-slider',
            min=1,
            max=12,
            step=1,
            marks={i: {'label': calendar.month_abbr[i], 'style': {'font-weight': 'bold', 'color': '#333'}} for i in
                   range(1, 13)},  # Bold & dark text
            value=0,  # Default value is January
            included=False,
            # tooltip={"placement": "bottom", "always_visible": True},  # Show selected month
        ),
        style={'margin': '0 auto', 'width': '85%', 'padding': '10px'}  # Indents left & right
    ),

    # Button to start the "show me the year" process
    html.Div(
        html.Button(
            '2024 Year in Review',
            id='show-year-button',
            n_clicks=0,
            style={
                'background-color': '#D3D3D3',  # Green button
                'color': 'black',  # White text
                'border': 'none',  # Remove border
                'padding': '12px 24px',  # Adjust padding for better size
                'font-size': '14px',  # Increase font size
                'font-weight': 'bold',
                'border-radius': '6px',  # Rounded corners
                'cursor': 'pointer',  # Pointer cursor on hover
                'transition': '0.3s',  # Smooth hover effect
            }
        ),
        style={'text-align': 'center', 'margin': '20px 0'}  # Centers the button
    ),

    # Interval component to auto-update the month
    dcc.Interval(
        id='month-interval',
        interval=700,  # 0.7 second interval
        n_intervals=0,
        disabled=True  # Start with interval disabled
    ),

    # Graph to display the choropleth map
    dcc.Graph(id='pm25-map',
              style={'height': '660px'})  # Increase graph height)
])

@app.callback(
    dash.dependencies.Output('pm25-map', 'figure'),
    [dash.dependencies.Input('month-slider', 'value')]
)
def update_map(selected_month):
    # Ensure selected_month is an integer
    if isinstance(selected_month, (list, tuple)):
        selected_month = selected_month[0]  # Pick the first value if it's a list

    # Filter the data based on the selected month
    filtered_data = avg_pm25[avg_pm25['Month'] == selected_month]

    # Create a mapping of 'County' to average PM2.5 value for the selected month
    location_data = filtered_data.set_index('County')['Daily Mean PM2.5 Concentration'].to_dict()

    # Generate the color values based on the county names in GeoJSON
    color_values = [location_data.get(feature['properties']['name'], 0) for feature in counties_geojson['features']]

    # Create the choropleth map with a fixed color scale
    fig = px.choropleth(
        geojson=counties_geojson,
        locations=[feature['properties']['name'] for feature in counties_geojson['features']],
        featureidkey="properties.name",  # Adjust this key based on your GeoJSON structure
        color=color_values,
        color_continuous_scale="Greens",
        range_color=[global_min, global_max]  # Set fixed range for color scale
    )

    # Customizing title position
    fig.update_layout(
        title=f"PM2.5 Concentration by County for {calendar.month_name[selected_month]} 2024",
        title_x=0.5,  # Center the title horizontally (0.5 = center)
        title_y=0.95,  # Set the title slightly lower (1 is top, 0 is bottom)
        title_xanchor='center',  # Anchor the title in the center horizontally
        title_yanchor='top',  # Anchor the title to the top vertically
    )

    # Update the map appearance
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin=dict(l=60, r=60, t=50, b=50), height=600)

    return fig

# Callback to update the month value periodically
@app.callback(
    dash.dependencies.Output('month-slider', 'value'),
    [dash.dependencies.Input('month-interval', 'n_intervals')],
    [dash.dependencies.State('month-slider', 'value')]
)
def rotate_month(n_intervals, current_month):
    # Increment the month, reset to 1 after December (12)
    next_month = 1 if current_month >= 12 else current_month + 1

    # Check if it has gone through all 12 months
    if next_month > 12:
        return current_month  # Keep it on December

    return next_month  # Continue to next month

@app.callback(
    dash.dependencies.Output('month-interval', 'disabled'),
    dash.dependencies.Output('show-year-button', 'n_clicks'),  # Reset button clicks
    [dash.dependencies.Input('show-year-button', 'n_clicks'),
     dash.dependencies.Input('month-slider', 'value')]
)
def control_interval(n_clicks, selected_month):
    # If the button is clicked and we're not at December, start rotating
    if n_clicks > 0 and selected_month < 12:
        return False, n_clicks  # Keep button click count the same

    # If we reach December, stop the interval and reset the button
    if selected_month == 12:
        return True, 0  # Reset button clicks so it can be pressed again

    return True, n_clicks  # Default case (before clicking)

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
