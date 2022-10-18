from dash import Dash, html, dcc, Input, Output
import pandas as pd
import csv
import plotly.express as px
from scipy.signal import savgol_filter
import plotly.graph_objects as go
from skimage import io
from plotly.subplots import make_subplots
#-----------------------------------------------------------------------------------------------------------------------
# Read data from 'SN_m_tot_V2.0.csv' and create list of .csv lines
dflines = []
with open('SN_m_tot_V2.0.csv', 'r') as infile:
    for row in csv.reader(infile):
        dflines.append([x.strip() for x in row[0].split(';')])

# Create pandas dataframe from .csv lines and assign each column its appropriate data type
df = pd.DataFrame(dflines, columns=['Year', 'Month', 'Date in Fraction of Year', 'Monthly Mean',
                                    'Monthly Mean STD', 'Number of Observations', 'Definitive?'])
df = df.astype({'Year': 'int64', 'Month': 'int64', 'Date in Fraction of Year': 'float', 'Monthly Mean': 'float',
                'Monthly Mean STD': 'float', 'Number of Observations': 'float', 'Definitive?': 'int64'})
#-----------------------------------------------------------------------------------------------------------------------
# Initialize Dash app
app = Dash(__name__)

# Create line plot using the monthly sunspot count means from each date
fig = px.line(df, x='Date in Fraction of Year', y='Monthly Mean', labels={'Date in Fraction of Year': "Date (Years)",
                                                                  'Monthly Mean': "Mean Number of Sunspots"},
                                                                  title='Monthly Means of Sunspot Counts')

# Define starting years on x-axis for user
year_label = 'You are currently viewing the years 1749 to 2022!'

# Create new dataframe column of sunspot variability by year by using the modulo of each date with its cycle length,
# starting with an assumed average cycle length of 11 years
df['Variability'] = df.apply(lambda row: row['Date in Fraction of Year'] % 11, axis=1)

# Create scatter plot using the modulo expression and the monthly mean sunspot count from that date
var_fig = px.scatter(df, x='Variability', y='Monthly Mean',
                     labels={'Date in Fraction of Year': 'Years', 'Variability': 'Number of Sunspots'},
                     title=f'Variability, Sunspot Cycle Length: 11.0 Years')

# Read real-time sun image urls into plotly images
urls = ['https://soho.nascom.nasa.gov/data/realtime/eit_284/1024/latest.jpg',
        'https://soho.nascom.nasa.gov/data/realtime/eit_171/1024/latest.jpg',
        'https://soho.nascom.nasa.gov/data/realtime/eit_195/1024/latest.jpg']
img1 = px.imshow(io.imread(urls[0]))
img2 = px.imshow(io.imread(urls[1]))
img3 = px.imshow(io.imread(urls[2]))

# Set up Dash app layout
app.layout = html.Div([
    html.H1('Royal Observatory of Belgium: Sunspot Data', style={'textAlign': 'center'}),

    # Display line plot of sunspot monthly means
    dcc.Graph(id='year-plot', figure=fig),

    # Display to user what years they are currently viewing on the x-axis
    html.P(children=[year_label], id='year-label'),

    # Give user option to zoom in or out of line plot by changing x-axis,
    # starting with showing the user the entire domain of the plot
    dcc.RangeSlider(id='year-slider', min=1749, max=2022, value=[1749, 2022],
                    marks={opacity: f'{opacity:.0f}' for opacity in list(range(1752,2032,15))},
                    tooltip={"placement": "bottom", "always_visible": True}),
    html.H4('Years Displayed', style={'text-align': 'center'}),

    # Give user option to change smoothness of second line on plot by updating degree of best-fit polynomial function,
    # starting with a value of degree=5
    dcc.Slider(min=1, max=25, step=1, value=5, id='smoothness'),
    html.H4('Every Nth Observation in Smoothness Trace', style={'text-align': 'center'}),

    # Display scatter plot displaying the variability of the sunspot counts
    dcc.Graph(id='var-plot', figure=var_fig),

    # Give user option to change the assumed value for average sun cycle length, starting with value of 11 years
    dcc.Slider(id='cycle-len', min=1.0, max=100.0, value=11.0,
               tooltip={"placement": "bottom", "always_visible": True}),

    # Display realtime sun images using 3 different filters
    html.H4('Realtime Sun Images', style={'text-align': 'center'}),
    html.Div([
             html.Div([dcc.Graph(figure=img1)], style={'width': '33%', 'display': 'inline'}),
             html.Div([dcc.Graph(figure=img2)], style={'width': '33%', 'display': 'inline'}),
             html.Div([dcc.Graph(figure=img3)], style={'width': '33%', 'display': 'inline'})],
             style={'display': 'flex'})

])

@app.callback(
    Output(component_id='year-plot', component_property='figure'),
     Output(component_id='var-plot', component_property='figure'),
    Output(component_id='year-label', component_property='children'),
    [Input(component_id='year-slider', component_property='value'),
     Input(component_id='smoothness', component_property='value'),
     Input(component_id='cycle-len', component_property='value')])

def _refresh_plots(year_slider_value, smoothness_value, cycle_length_value):
    # Update axes according to desired years in RangeSlider
    fig.update_xaxes(range=[year_slider_value[0], year_slider_value[1]])

    # Clear past traces from plot
    fig.data = (fig.data[0:1])

    # Smooth data by selecting only every nth observation and plot this new trace over the original line plot
    smoothed_df = df.iloc[::smoothness_value]
    fig.add_trace(go.Scatter(x=list(smoothed_df['Date in Fraction of Year']), y=list(smoothed_df['Monthly Mean']),
                             mode='lines', name='Smoothed', line_color='red'))

    # Update x-axis year label for user
    year_label = f'You are currently viewing the years {year_slider_value[0]} to {year_slider_value[1]}!'

    # Re-calculate moduli with new user-inputted assumed cycle length
    df['Variability'] = df.apply(lambda row: row['Date in Fraction of Year'] % cycle_length_value, axis=1)

    # Define new scatter plot using new cycle length
    var_fig = px.scatter(df, x='Variability', y='Monthly Mean',
                         labels={'Date in Fraction of Year': 'Number of Sunspots',
                                 'Variability': 'Years'},
                         title=f'Variability, Sunspot Cycle Length: {cycle_length_value} Years')
    return fig, var_fig, year_label

if __name__ == '__main__':
    app.run_server(debug=True)