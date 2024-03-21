import datetime
import time

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, MATCH, ALL
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import mysql.connector
from mysql.connector import Error
from dash.exceptions import PreventUpdate
from sqlalchemy import create_engine, MetaData, Table, update, Column, String, Integer, Float
from sqlalchemy.orm import sessionmaker, declarative_base

from coordinates import get_coordinates
from wine_card import get_wine_card

# Database connection
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="pranit17",
    database="WineReviews",
    port=3306
)

app = dash.Dash(__name__, suppress_callback_exceptions=True)

Base = declarative_base()

engine = create_engine('mysql+mysqlconnector://root:pranit17@localhost:3306/WineReviews')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
session = Session()

df = pd.read_sql("SELECT * FROM Reviews", engine)

df_countries = pd.read_sql("SELECT DISTINCT country FROM Reviews WHERE country IS NOT NULL", engine)
countries = df_countries['country'].sort_values().tolist()
countries.insert(0, 'All Countries')

mark_values = {
    4: '4', 17: '17', 42: '42',
    65: '65', 80: '80', 100: '100', 150: '150',
    200: '200', 250: '250', 500: '500', 1000: '1000',
}
colorVal = [
    "#F4EC15", "#DAF017", "#BBEC19", "#9DE81B", "#80E41D", "#66E01F",
    "#4CDC20", "#34D822", "#24D249", "#25D042", "#26CC58", "#28C86D",
    "#29C481", "#2AC093", "#2BBCA4", "#2BB5B8", "#2C99B4", "#2D7EB0",
    "#2D65AC", "#2E4EA4", "#2E38A4", "#3B2FA0", "#4E2F9C", "#603099",
]
mapbox_access_token = 'pk.eyJ1IjoicGVhY2h5MTciLCJhIjoiY2x0ejgzYzZsMHAxbzJpbzhjcDlwMXV2diJ9.g02ifZvTa6lDEPj8xvfRmA'
px.set_mapbox_access_token(mapbox_access_token)

if not df.empty:
    default_wine_data = df.iloc[0].to_dict()
    # Transform any NaN values to None (or another placeholder you prefer)
    default_wine_data = {key: (None if pd.isna(value) else value) for key, value in default_wine_data.items()}
else:
    # Define a default structure in case your DataFrame is empty
    default_wine_data = {
        'wine_id': None,
        'title': "",
        'country': "",
        'region': "",
        'variety': "",
        'winery': "",
        'price': None,
        'points': None,
        'description': ""
    }

    df_initial = pd.read_sql("SELECT * FROM Reviews", engine)
    initial_map_fig = go.Figure(go.Scattermapbox(
        lat=df_initial['latitude'],
        lon=df_initial['longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(size=9),
    ))

    initial_map_fig.update_layout(
        mapbox_style="light",
        mapbox=dict(
            center=go.layout.mapbox.Center(
                lat=df_initial['latitude'].mean(),
                lon=df_initial['longitude'].mean()
            ),
            zoom=5,
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

app.layout = html.Div([

    # ------------SIDE BAR-----------------------------------------
    html.Div([
        html.H1("Wine Reviews", className="title"),
        html.P("How Expensive are your taste buds? Find the country with the most expensive wines or find the most "
               "expensive wine in a specific country!", className="description"),
        html.Div([
            dcc.Dropdown(
                id='country_dropdown',
                options=[{'label': country, 'value': country} for country in countries],
                value='All Countries',
                clearable=False,
                className="dropdown"
            ),
            html.Button('Toggle Text', id='toggle-text-button', n_clicks=0, className="button-4")
        ], className="dropdown-button-container"),
        html.Div(id='dynamic-wine-card', className="wine-card"),
        dcc.Store(id='edit-mode-flag', storage_type='session', data={'edit_mode': False}),
        dcc.Store(id='wine-data-store', storage_type='session', data={}),
        dcc.Store(id='db-update-trigger', storage_type='session', data={'last_updated': str(datetime.datetime.now())}),
        html.Button(id='edit-save-button', n_clicks=0, style={'display': 'none'}, className="button-4"),

    ], className="sidebar-container"),

    # ------------MAIN CONTENT-----------------------------------------
    html.Div([
        dcc.Graph(id='the_graph', className="graph-container"),
        dcc.RangeSlider(
            id='the_price',
            min=4,
            max=1000,
            value=[4, 17],
            marks=mark_values,
            step=None,
            className="slider-container"
        ),
        dcc.Graph(id='mapbox-map',
                  figure={
                      'data': [
                          go.Scattermapbox(
                              lat=[0],
                              lon=[0],
                              mode='markers',
                              marker=go.scattermapbox.Marker(size=10),
                          )
                      ],
                      'layout': go.Layout(
                          mapbox_style="light",
                          mapbox=dict(
                              center=go.layout.mapbox.Center(lat=0, lon=0),
                              zoom=10,
                              accesstoken='pk.eyJ1IjoicGVhY2h5MTciLCJhIjoiY2x0ejgzYzZsMHAxbzJpbzhjcDlwMXV2diJ9'
                                          '.g02ifZvTa6lDEPj8xvfRmA',
                          ),
                          margin={"r": 0, "t": 0, "l": 0, "b": 0}
                      ),
                  },
                  style={'height': '550px'}),
    ], className="main-content"),
], className="app-container")


@app.callback(Output('the_graph', 'figure'),
              [Input('the_price', 'value'),
               Input('country_dropdown', 'value'),
               Input('db-update-trigger', 'data'),
               Input('toggle-text-button', 'n_clicks')]
              )
def update_graph(price_chosen, country_chosen, db_trigger, toggle_text):
    print(price_chosen, country_chosen)
    show_text = toggle_text % 2 == 0
    text = None
    df_local = fetch_db()
    if country_chosen == 'All Countries':
        dff = df_local[(df_local['price'] >= price_chosen[0]) & (df_local['price'] <= price_chosen[1])]
        dff = dff.groupby(["country"], as_index=False)[["price",
                                                        "points"]].mean()
        dff = dff.sort_values(by='price')
        max_mean_price = dff['price'].max()
        dff['mean_price_normalized'] = dff['price'] / max_mean_price
        dff['color'] = dff['mean_price_normalized'].apply(lambda x: color(x, colorVal))
        text = 'country' if show_text else None
    else:
        dff = reset_graph()
        dff = df_local[(df_local['country'] == country_chosen) & (df_local['price'] >= price_chosen[0]) &
                       (df_local['price'] <= price_chosen[1])].copy()
        dff = dff.sort_values(by='price')
        max_price_selected = dff['price'].max()
        dff.loc[:, 'price_normalized'] = dff['price'] / max_price_selected
        dff.loc[:, 'color'] = dff['price_normalized'].apply(lambda x: color(x, colorVal))
        text = 'region_1' if show_text else None

        cursor = mydb.cursor()

        for index, row in dff.iterrows():
            update_query = """
                    UPDATE Reviews
                    SET color = %s
                    WHERE id = %s;
                """
            cursor.execute(update_query, (row['color'], row['id']))
            mydb.commit()

    scatterplot = px.scatter(
        data_frame=dff,
        x='price',
        y='points',
        color='color',
        hover_data=['country'] if country_chosen == 'All Countries' else ['id', 'region_1', 'title'],
        text=text,
        height=550
    )
    scatterplot.update_traces(textposition='top center')

    return scatterplot


@app.callback(
    [Output('edit-save-button', 'children'),
     Output('edit-save-button', 'style')],
    [Input('edit-mode-flag', 'data')]
)
def update_button_text_and_style(edit_mode_data):
    if edit_mode_data and edit_mode_data.get('edit_mode'):
        return 'Save Changes', {'display': 'block'}
    else:
        return 'Edit Wine', {'display': 'block'}


@app.callback(
    Output('edit-mode-flag', 'data'),  # Update the data of the dcc.Store
    [Input('edit-save-button', 'n_clicks')],  # Listen for clicks on the consolidated button
    [State('edit-mode-flag', 'data')]  # Current state of the edit_mode_flag
)
def toggle_edit_mode(n_clicks, edit_mode_data):
    if n_clicks is None or n_clicks == 0:
        raise PreventUpdate

    if edit_mode_data is None:
        edit_mode_data = {'edit_mode': False}

    # Toggle the edit mode
    edit_mode_data['edit_mode'] = not edit_mode_data['edit_mode']
    return edit_mode_data


@app.callback(
    Output('dynamic-wine-card', 'children'),
    [Input('the_graph', 'clickData'),
     Input('edit-mode-flag', 'data'),
     Input('wine-data-store', 'data'),
     Input('db-update-trigger', 'data'), ]
)
def display_wine_details(click_data, edit_mode_flag, wine_data, db_trigger):
    if click_data is None:
        return html.Div('Click on a point in the graph to see detailed information.',
                        style={'color': 'black', 'padding-left': '5%'})

    edit_mode = edit_mode_flag['edit_mode'] if edit_mode_flag is not None else False
    wine_id = click_data['points'][0]['customdata'][0]
    df_local = fetch_db()
    wine_data = df_local[df_local['id'] == wine_id].iloc[0].to_dict()
    wine_card = get_wine_card(wine_data, edit_mode)
    return wine_card


@app.callback(
    [Output('wine-data-store', 'data'),
     Output('db-update-trigger', 'data')],
    [Input('edit-save-button', 'n_clicks'),
     Input('wine-data-store', 'data')],
    [State('wine-title', 'value'),
     State('wine-country', 'value'),
     State('wine-region', 'value'),
     State('wine-variety', 'value'),
     State('wine-winery', 'value'),
     State('wine-price', 'value'),
     State('wine-points', 'value'),
     State('wine-description', 'value'),
     State('wine-id', 'value'),
     State('edit-mode-flag', 'data')
     ],
)
def save_wine(n_clicks, wine_data, title, country, region, variety, winery, price, points, description, id,
              edit_mode_data):
    update_trigger = wine_data.get('last_update', {'last_updated': str(datetime.datetime.now().timestamp())})

    if n_clicks == 0:
        raise PreventUpdate

    if wine_data is None:
        print("ur cooked buddy")

    if edit_mode_data['edit_mode']:
        wine_data['title'] = title
        wine_data['country'] = country
        wine_data['region'] = region
        wine_data['variety'] = variety
        wine_data['winery'] = winery
        wine_data['price'] = price
        wine_data['points'] = points
        wine_data['description'] = description

    try:
        cursor = mydb.cursor()

        update_statement = """
                UPDATE Reviews
                SET title=%s, country=%s, region_1=%s, variety=%s, winery=%s, price=%s, points=%s, description=%s
                WHERE id=%s
                """
        data_tuple = (title, country, region, variety, winery, price, points, description, id)
        cursor.execute(update_statement, data_tuple)
        mydb.commit()
        update_trigger = {'last_updated': str(datetime.datetime.now().timestamp())}
        print(cursor.rowcount, "row(s) updated.")
    except mysql.connector.Error as e:
        print(f"Error: {e}")

    return wine_data, update_trigger


@app.callback(
    Output('mapbox-map', 'figure'),
    [Input('the_graph', 'clickData'),
     Input('db-update-trigger', 'data')],
    [State('the_graph', 'figure'),
     State('country_dropdown', 'value')]  # To access the data from the graph
)
def display_map(click_data, db_trigger, figure_data, country):
    if click_data is None:
        # Optionally, you can decide what to display when no points are clicked
        raise PreventUpdate

    df_local = fetch_db()

    region = click_data['points'][0]['customdata'][1]
    wine_id = click_data['points'][0]['customdata'][0]

    wine_data = df_local[df_local['id'] == wine_id]
    if not wine_data.empty and pd.notnull(wine_data.iloc[0]['latitude']) and pd.notnull(wine_data.iloc[0]['longitude']):

        lat = wine_data.iloc[0]['latitude']
        lng = wine_data.iloc[0]['longitude']
    else:
        formatted_location = f"{region}, {country}"
        lat, lng = get_coordinates(formatted_location)

    try:
        cursor = mydb.cursor()

        update_statement = """
               UPDATE Reviews
               SET latitude = %s, longitude = %s
               WHERE id = %s;
           """
        cursor.execute(update_statement, (lat, lng, wine_id))
        mydb.commit()
        print(f"Wine location added for this wine: {wine_id}")
        print(cursor.rowcount, "row(s) updated.")
    except mysql.connector.Error as e:
        print(f"Error: {e}")

    fig = go.Figure(go.Scattermapbox(
        lat=df_local['latitude'],
        lon=df_local['longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(size=8,
                                       color=df_local['color'])
    ))

    fig.update_layout(
        mapbox_style="light",
        mapbox=dict(
            center=go.layout.mapbox.Center(lat=lat, lon=lng),
            zoom=3,
            accesstoken='pk.eyJ1IjoicGVhY2h5MTciLCJhIjoiY2x0ejgzYzZsMHAxbzJpbzhjcDlwMXV2diJ9.g02ifZvTa6lDEPj8xvfRmA'
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    return fig


def reset_graph():
    empty_df = pd.read_sql("SELECT * FROM Blank", engine)
    return empty_df


def color(price, scale):
    index = min(int(price * (len(scale) - 1)), len(scale) - 1)
    return scale[index]


def fetch_db():
    return pd.read_sql("SELECT * FROM Reviews", engine)


if __name__ == '__main__':
    app.run_server(debug=True)
