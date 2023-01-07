from dash import Dash, dcc, html, Input, Output, State, callback, dash_table
from ast import In

import datetime
import io
import dash, os
import plotly.express as px
import pandas as pd
import dash_uploader as du
import uuid


dash.register_page(__name__, path='/')

# CORPUS FILES CONFIGURATION

CORPUS_DIR = "convokitdatasets"


def get_corpus_list():
    """
    Lists pre-installed corpus folders
    
    :return: String containing list of corpuses
    """ 
    list = []
    for folder in os.listdir(CORPUS_DIR):
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
    Output(component_id='user-input', component_property='data'),
    Input(component_id='option-one-dropdown', component_property='dropdown_value'),
    Input(component_id='button-one', component_property='n_clicks')
)
def save_output(dropdown_value, n_clicks):
    """
    Stores user-selected drop-down value from the first page
    
    :param value: Selected drop-down value(s)
    :return: Selected drop-down value(s)
    """
    # return value
    return  {
        'option-one-dropdown': dropdown_value,
        'button-one': n_clicks
        } 



