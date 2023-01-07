from dash import Dash, dcc, html, Input, Output, State, callback, dash_table
from ast import In
from datafarm import *

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


corpus_list = get_corpus_list()

# UPLOADED FILES CONFIGURATION

def get_upload_component():
    """
    Pre-configures & returns upload component 
    
    :return: Upload component
    """ 
    return du.Upload(
            id='upload-data',
            text='Drag and Drop Here to Upload!',
            upload_id=uuid.uuid1(),
        )

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
            options=corpus_list,
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

        html.Div(
            children=[
                get_upload_component(),
                html.Div(id='uploader-output')
            ]
        ),

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

# CALLBACKS

@dash.callback(
    Output(component_id='df-files', component_property='data'),
    Input(component_id='option-one-dropdown', component_property='value'),
)
def clean_data(value):
    """
    Stores user-selected drop-down value from the first page
    
    :param value: Selected drop-down value(s)
    :return: Selected drop-down value(s)
    """
    print('Selected Corpus:', value)
    print('Processing..')

    datafarm = DataFarm(value) # pass parent_dir param to datafarm ? so can generalize to uploaded files too w/o having to code more
  
    spkr_df = datafarm.create_spkr_df() # save these to the page
    print(spkr_df)

    grp_df = datafarm.create_grp_df(spkr_df)
    print(grp_df)

    datasets = {
        'spkr_df': spkr_df.to_json(orient='split', date_format='iso'),
        'grp_df': grp_df.to_json(orient='split', date_format='iso'),
    }

    print('Done processing.')
    return json.dumps(datasets)



