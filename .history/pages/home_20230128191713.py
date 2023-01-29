from dash import Dash, dcc, html, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
from ast import In
from datafarm import *
import zipfile

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

        html.Div(id='output-data-upload'),

        dcc.Link(
            html.Button(
                children='Submit', 
                id='button-one',
                n_clicks=0
            ),
            href='/analysis'
        ),

    ]
)

# METHODS

# remove print statements from below 2 methods
def validate_json(zip_obj, filename):
    file = zip_obj.read(filename)

    try:
        if 'jsonl' in filename:
            result = [json.loads(jline) for jline in file.splitlines()]
            print('Valid JSON')   
            return True
        else:
            json.loads(file)
            print('Valid JSON')
            return True
    except ValueError as e:
        print('[', filename, ']', 'invalid json: %s' % e)
        return False
    

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
        
    content_decoded = base64.b64decode(content_string)
        
    zip_str = io.BytesIO(content_decoded)
        
    try:
        zip_obj = zipfile.ZipFile(zip_str, 'r')
        for filename in zip_obj.namelist():
            if 'json' in filename:
                print(filename)
                valid = validate_json(zip_obj, filename)
                if valid is not True:
                    return html.Div(
                        children=f'Invalid json: [{filename}] %s %e',
                        style={
                            'textAlign': 'center',
                            'color': 'white',
                            'padding': '10px'
                        }
                    )
            else:
                print('Invalid file type: [', filename, ']') 
                return html.Div(
                    children=f'Invalid file type: [{filename}]',
                    style={
                        'textAlign': 'center',
                        'color': 'white',
                        'padding': '10px'
                    }
                )
    except zipfile.BadZipFile as error:
        print(error)
        return html.Div(
                    children='File is not a zip file',
                    style={
                        'textAlign': 'center',
                        'color': 'white',
                        'padding': '10px'
                    }
        )


# CALLBACKS

@dash.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def grab_upload_data(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


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



