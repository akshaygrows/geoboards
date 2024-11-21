from sshtunnel import SSHTunnelForwarder
import numpy as np
import psycopg2 as psy
import pandas as pd
from IPython.display import FileLink
import geopandas as gpd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import paramiko
from io import StringIO
from shapely.geometry import MultiPoint, MultiPolygon
from shapely.ops import unary_union
import calendar
from datetime import datetime
import os

def get_df_from_sql(SSH_required, query,key_path):   #for getting a datafarame as a result

    db='datawarehouse'
    DB_HOST='datawarehouse.cdgpvetprks3.ap-south-1.rds.amazonaws.com'
    conn = None
    if SSH_required == 'Yes':
        SSH_HOST='ec2-15-206-161-154.ap-south-1.compute.amazonaws.com'
        #LOCALHOST="0.0.0.0"
        ssh_tunnel= SSHTunnelForwarder(
                (SSH_HOST, 22),
                ssh_username="ec2-user",
                ssh_private_key= key_path,
                ssh_private_key_password= "",
                remote_bind_address=(DB_HOST, 5432),
                local_bind_address=('127.0.0.1', 0)
        )
        # ssh_tunnel._server_list[0].block_on_close = False
        ssh_tunnel.start()
        conn = psy.connect(
            host=ssh_tunnel.local_bind_host,
            port=ssh_tunnel.local_bind_port,
            user='postgres',
            password= "Simply1234",
            database='postgres')
        df_results = pd.read_sql(query, conn)
        conn.close()
        ssh_tunnel.stop()
        return df_results
    else:
        conn = psy.connect(
            host = DB_HOST,
            port = 5432,
            user = 'postgres',
            password= "Simply1234",
            database='postgres')
        df_results = pd.read_sql(query, conn)
        conn.close()
        return df_results
    
# Usage with the actual path to the private key
SSH_required = 'No'
script_dir = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(script_dir, 'tunnel-ssh .cer')

query = """
select 
    awb ,
    latitude, 
    longitude, 
    shipping_city, 
    last_mile_hub, 
    shipping_pincode,
    case 
        when first_ofd_time is null then 0 
        else 1
    end as ofd_done
from public.ops_main
where date_trunc('day', shipper_edd) = date_trunc('day', now() + interval '5.5 hours')
and extract(hour from shipper_edd) < 16   -- MORNING EDD
and (first_ofd_time is null or first_ofd_time::date = date_trunc('day', now() + interval'5.5 hours'))
and shipment_cost_type not in ('2 hour', '3 hour')
and latitude is not null
and shipment_status not like '%RTO%'
and closure_status = 'open'
"""

# Retrieve data into a DataFrame
df = get_df_from_sql(SSH_required, query, key_path)
df['color'] = np.where(df['ofd_done'] == 1, 'green', 'red')
print(df.head())

# Initialize the app
app = Dash(__name__)

# Define app layout
app.layout = html.Div([
    html.H1("OFD Analysis | EDD = Today", style={'text-align': 'center'}),
    dcc.Input(
        id='search_shippingcity',
        type = 'text',
        placeholder='Search Shipping City here',
        value='Bangalore',
        style={'width': "40%"}
    ),
    dcc.Input(
        id='search_last_mile_hub',
        type = 'text',
        placeholder='Search Last Mile Hub here',
        value='MRTH',
        style={'width': "40%"}
    ),
    dcc.Input(
        id='search_pincode',
        type = 'number',
        placeholder='Search Shipping Pincode here',
        style={'width': "40%"}
    ),
    html.Div(id='output_container_city', children=[]),
    html.Div(id='output_container_last_mile_hub', children=[]),
    html.Div(id='output_container_shipping_pincode', children=[]),
    dcc.Graph(
        id='map',
        figure={},
        style={'height': '90vh','width': '100%', 'margin': '0 auto'}  # Set the height of the graph to 90% of the viewport height
    ),
    html.Div(
        [
            html.P("Access the app at:"),
            html.A("http://127.0.0.1:8052", href="http://127.0.0.1:8052", target="_blank")  # Link to the app
        ],
        style={'text-align': 'center', 'margin-top': '20px'}
    )
])

# Callback to update the graph
@app.callback(
    [
        Output(component_id='output_container_city', component_property='children'),
        Output(component_id='output_container_last_mile_hub', component_property='children'),
        Output(component_id='output_container_shipping_pincode', component_property='children'),
        Output(component_id='map', component_property='figure')
    ],
    [
        Input(component_id='search_shippingcity', component_property='value'),
        Input(component_id='search_last_mile_hub', component_property='value'),
        Input(component_id='search_pincode', component_property='value')
    ]
)
def update_graph(city_slctd, hub_slctd, pincode_slctd):
    if not city_slctd or city_slctd not in df['shipping_city'].unique():
        return "", "", {}
    
    output_container_city = f"Results are shown for the Shipping City: {city_slctd}"
    output_container_last_mile_hub = f"Results are shown for Hub: {hub_slctd}"
    output_container_shipping_pincode = f"Results are shown for Hub: {pincode_slctd}"
    
    # Filter the dataframe based on selected city and hub
    dff = df[df["shipping_city"] == city_slctd]
    if hub_slctd:
        dff = dff[dff["last_mile_hub"] == hub_slctd]
    if pincode_slctd:
        dff = dff[dff["shipping_pincode"] == pincode_slctd]
    
    # Set map center based on the filtered data
    center_lat = dff['latitude'].mean()
    center_lon = dff['longitude'].mean()

    # Increase the size of red markers and adjust opacity
    marker_size = [12 if color == 'red' else 8 for color in dff['color']]
    marker_opacity = [1.0 if color == 'red' else 0.6 for color in dff['color']]

    # Create new figure similar to combined_figure
    fig = {
        'data': [
            {
                'type': 'scattermapbox',
                'lat': dff['latitude'],  # Filtered data latitude
                'lon': dff['longitude'],  # Filtered data longitude
                'mode': 'markers',
                'marker': {
                    'size': marker_size,  # Adjusted size based on color
                    'opacity': marker_opacity,  # Adjusted opacity based on color
                    'color': dff['color'],  # Use color based on ofd_done
                },
                'customdata': dff[['awb', 'last_mile_hub', 'shipping_pincode']].values,
                'name': 'OFD Analysis'
            }
        ],
        'layout': {
            'mapbox': {
                'style': "open-street-map",
                'center': {'lat': center_lat, 'lon': center_lon},
                'zoom': 10
            },
            'template': 'plotly_dark',
        }
    }

    # Optionally, add hover template or traces update
    for trace in fig['data']:
        trace['hovertemplate'] = (
            '<b>AWB:</b> %{customdata[0]}<br>'
            '<b>Hub:</b> %{customdata[1]}<br>'  # Add more hover data if needed
            '<b>Shipping Pincode:</b> %{customdata[2]}'
        )


    return output_container_city, output_container_last_mile_hub, output_container_shipping_pincode, fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=8052)
