import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine


def get_wine_card(selected_wine, edit_mode):
    wine_id = selected_wine['id']
    # wine_card = html.Div([html.Button('Edit Wine', id='dynamic-update-wine', n_clicks=0)])
    # print(edit_mode)
    if edit_mode:
        wine_card = html.Div([
            html.Button('Save Changes', id='edit-save-button', n_clicks=0, className="button-4 edit-button"),
            html.Div([
                html.H5('Wine Title: '),
                dcc.Input(id='wine-title', value=selected_wine['title'], type='text')
            ], className="input-field"),
            html.Div([
                html.P('Country: '),
                dcc.Input(id='wine-country', value=selected_wine['country'], type='text')
            ], className="input-field"),
            html.Div([
                html.P('Region: '),
                dcc.Input(id='wine-region', value=selected_wine['region_1'], type='text')
            ], className="input-field"),
            html.Div([
                html.P('Variety: '),
                dcc.Input(id='wine-variety', value=selected_wine['variety'], type='text')
            ], className="input-field"),
            html.Div([
                html.P('Winery: '),
                dcc.Input(id='wine-winery', value=selected_wine['winery'], type='text')
            ], className="input-field"),
            html.Div([
                html.P('Price: '),
                dcc.Input(id='wine-price', value=selected_wine['price'], type='text')
            ], className="input-field"),
            html.Div([
                html.P('Points: '),
                dcc.Input(id='wine-points', value=selected_wine['points'], type='text')
            ], className="input-field"),
            html.Div([
                html.P('Description: '),
                dcc.Textarea(id='wine-description', value=selected_wine['description'])
            ], className="input-field"),
            html.Div([
                html.P('ID: '),
                dcc.Input(id='wine-id', value=selected_wine['id'])
            ], className="input-field"),

        ], className='wine-card-content')
    else:
        wine_card = html.Div([
            html.Button('Edit Wine', id='edit-save-button', n_clicks=0, className="button-4 edit-button"),
            html.H5(f"Wine Title: {selected_wine['title']}"),
            html.P(f"Country: {selected_wine['country']}"),
            html.P(f"Region: {selected_wine['region_1']}"),
            html.P(f"Variety: {selected_wine['variety']}"),
            html.P(f"Winery: {selected_wine['winery']}"),
            html.P(f"Price: ${selected_wine['price']}"),
            html.P(f"Points: {selected_wine['points']}"),
            html.P(f"Description: {selected_wine['description']}"),
            html.P(f"ID: {selected_wine['id']}")
        ])

    return html.Div(wine_card, className="wine-card-container")
