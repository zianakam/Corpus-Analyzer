from dash import Dash, dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
from ast import In
from datafarm import *

import base64
import datetime
import io
import dash, os
import plotly.express as px
import pandas as pd
import dash_uploader as du
import uuid
import json


dash.register_page(__name__, path='/')

# CORPUS FILES CONFIGURATION

def get_corpus_list():
    """
    Lists pre-installed corpus folders
    
    :return: String containing list of corpuses
    """ 
    corpus_dir = "convokitdatasets"
    list = []
    for folder in os.listdir(corpus_dir):
        list.append(folder)

    return list

# APP LAYOUT

layout = html.Div(
    children=[

        html.Div(
            children='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce semper vulputate enim eget iaculis. Curabitur dictum nisi sit amet felis vestibulum elementum', 
            className='subheader',
        ),

        # Include all Convokit datasets
        html.Div(
            children='(1) Select a pre-installed ConvoKit Dataset', 
            className='options-text',
        ),

        dcc.Dropdown(
            options=get_corpus_list(),
            id='option-one-dropdown'
        ),

        html.Div(
            children='OR', 
            className='options-text'
        ),

        # Fix so can only upload certain files of a certain format
        html.Div(
            children='(2) Insert custom dataset files in Convokit format', 
            className='options-text'
        ),

        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            multiple=True
        ),

        dcc.Link(
            html.Button(
                children='Submit', 
                id='button-one',
                n_clicks=0
            ),
            href='/analysis'
        ),

        html.Div(id='output-data-upload'),

    ]
)

# METHODS

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            print('CSV found')
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
            print('XLS found')
        else:
            raise Exception()
    except Exception as e:
        print('Exception')
        print(e)
        return html.Div(
            children='There was an error processing this file. Please ensure you\'re uploading a .csv or .xls file.',
            style={
                'color': 'white',
                'textAlign': 'center'
            },
        )

# CALLBACKS

@dash.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            print('CSV found')
            raise PreventUpdate
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
            print('XLS found')
            raise PreventUpdate
        else:
            raise Exception()
    except Exception as e:
        print('Exception')
        print(e)
        return html.Div(
            children='There was an error processing this file. Please ensure you\'re uploading a .csv or .xls file.',
            style={
                'color': 'white',
                'textAlign': 'center'
            },
        )


@dash.callback(
    Output(component_id='df-files', component_property='data'),
    Input(component_id='option-one-dropdown', component_property='value'), prevent_initial_call=True
)
def pre_process_data(value):
    """
    Grab user input and use to pre-process the corpus & produce resulting dataframes
    
    :param value: Selected drop-down value(s)
    :return: Json of processed datasets
    """
    if (value is not None): # later submit btn state should trigger processing not dropdown and if/else
        print('Selected Corpus:', value)
        print('Processing..')

        datafarm = DataFarm(value) # pass parent_dir param to datafarm ? so can generalize to uploaded files too w/o having to code more
    
        spkr_df = datafarm.create_spkr_df() 
        grp_df = datafarm.create_grp_df(spkr_df)

        datasets = {
            'spkr_df': spkr_df.to_json(orient='split', date_format='iso', index=True),
            'grp_df': grp_df.to_json(orient='split', date_format='iso', index=True),
        }

        print('Done processing.')
        return json.dumps(datasets)
    else:
        dash.no_update



