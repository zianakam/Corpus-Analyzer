from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from datafarm import *
from zipfile import ZipFile
from pathlib import Path
from capture import * 

import json
import dash, os
import time
import uuid
import shutil
import base64
import zipfile
import io
import redis
import pickle
import zlib
import dash_bootstrap_components as dbc
import time
import sys


# Home Page

dash.register_page(__name__, path='/', title='Corpus Analyzer')

# Unique user session path folder for temp data
UPLOAD_FOLDER_ROOT = os.path.join(os.getcwd(), 'tmp/Uploads')
user_id = uuid.uuid1()
path_to_user_folder = os.path.join(UPLOAD_FOLDER_ROOT, str(user_id)) 
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")

def get_corpus_list():
    """
    Lists pre-downloaded Corpus folders
    
    :return: String containing list of availabe Corpuses
    """ 
    corpus_dir = "ck_datasets"
    
    list = []
    for folder in os.listdir(corpus_dir):
        folder = folder[:-4].replace('_', ' ') # Remove zip extension & hyphen for display purposes
        list.append(folder)

    list.sort()
    return list


layout = html.Div(
    children=[

        html.Div(
            children=[
                html.Div(
                    children=[
                        "An interactive dashboard for exploring conversational dynamics and linguistic features. "
                        "Corpus Analyzer cleans, pre-processes, and extracts conversational ",
                        "features using the ",
                        html.A(
                            children="ConvoKit toolkit",
                            href="https://convokit.cornell.edu/"
                        ),
                        " and other feature extraction strategies. ",
                    ]
                ),
            ],
            className='subheader',
        ),

        html.Div(
            children=[
                html.Span(
                    "counter_1",
                    className="material-symbols-outlined counter_1",
                    id='counter_icon',
                ),

                dcc.Link(
                    html.Button(
                        [
                            DashIconify(icon="mdi:chart-box-outline", style={"marginRight": "8px", "fontSize": "20px"}),
                            "Preview with a Sample Dataset"
                        ], 
                        style={
                            "textDecoration": "none"
                        },
                        id='preview_button',
                    ),
                    href='/overview',
                    style={"textDecoration": "none"}
                ),
            ],
            id='preview'
        ),

        html.Div(
            children=[
                'OR'
            ],
            className='or_statement'
        ),

        html.Div(
            children=[
                html.Span(
                    "counter_2",
                    className="material-symbols-outlined"
                ),
                'Load a corpus from ConvoKit\'s ',
                html.A(
                    children="website",
                    href="https://convokit.cornell.edu/datasets.html"
                ),
            ], 
            className='options_text',
        ),

        dcc.Dropdown(
            options=get_corpus_list(),
            id='options_dropdown'
        ),

        html.Div(
            children='OR', 
            className='or_statement'
        ),

        html.Div(
            children=[
                html.Span(
                    "counter_3",
                    className="material-symbols-outlined"
                ),
                'Upload a zipped version of your own corpus in ',
                html.A(
                    children="ConvoKit format ",
                    href="https://github.com/CornellNLP/ConvoKit/blob/master/examples/corpus_from_pandas.ipynb"
                ), 
            ],
            className='options_text'
        ),

        html.Div(
            children=[
                dcc.Upload(
                    id='uploaded_zip',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    accept=".zip",
                    multiple=False
                ),
            ],
            id='upload_container'
        ),

        html.Div(id='error_message'),

        html.Button(
                    'Submit', 
                    id="submit_button", 
                    disabled=True,
                    style={"visibility": "visible"}
                    ),
        
        html.Div(
            children=[
                dbc.Progress(
                    id="progress_bar",
                    className="progress",
                    value=0, 
                    striped=True, 
                    animated=True, 
                    style={
                        "visibility":"hidden",
                        },
                )
            ],
            style={
                "height": "20px !important",
                "width": "40%",
                "margin": "0 auto",
                "margin-top": "-5px",
                "margin-bottom": "80px",
            },
        ),

    ],
)

# Functions 

def process_zip(user_zip_path, filename):
    """
    Processes the zip file uploaded by the user

    :param user_zip_path: The file path to the zip file
    :param filename: The name of the zip file
    :return: The instantiated Object or an error message
    """
    datafarm = None
    content_type, content_string = user_zip_path.split(',')
    decoded = base64.b64decode(content_string)
    zip_str = io.BytesIO(decoded)

    try:
        zip_file = ZipFile(zip_str, 'r')
        zip_file.extractall(path_to_user_folder)

        # Check for multiple files 
        if len(os.listdir(path_to_user_folder)) > 1:
            shutil.rmtree(path_to_user_folder)
            return ['Error: Please ensure your files are stored within a single folder in your zip file and try again.']
        
        # Grab unzipped contents
        unzipped_path = path_to_user_folder + "/" + os.listdir(path_to_user_folder)[0]
        try:
            datafarm = DataFarm(unzipped_path)
            shutil.rmtree(path_to_user_folder)
        except FileNotFoundError:
            shutil.rmtree(path_to_user_folder) 
            return ['Error: Please ensure files are stored within a single folder in your zip file and try again.']
        except UnboundLocalError:
            shutil.rmtree(path_to_user_folder) 
            return ['Error: Invalid Convokit object. Please try again.']

    except zipfile.BadZipFile:
        shutil.rmtree(path_to_user_folder)
        return [f'Error: {filename} is a bad zipfile. Please try again.']

    return datafarm


def process_dropdown(dropdown_selection):
    """
    Processes the dropdown selection by the user

    :param dropdown_selection: The file selected
    :return: The instantiated Object or an error message
    """
    datafarm = None
    dropdown_selection = dropdown_selection.replace(' ', '_') + '.zip'

    if not Path(path_to_user_folder).exists():
        os.makedirs(path_to_user_folder)

    # Grab downloaded corpus (zipped)
    zip_path = os.path.join(os.getcwd(), 'ck_datasets/', dropdown_selection)
    
    # Copy the file from the ck_datasets folder to the user's directory
    shutil.copy(zip_path, f'{path_to_user_folder}/', follow_symlinks=False)

    # Extract the zip file
    with zipfile.ZipFile(path_to_user_folder + f'/{dropdown_selection}', 'r') as z:
        z.extractall(path_to_user_folder)

    # Delete the original zip file and grab the unzipped directory path
    os.remove(path_to_user_folder + f'/{dropdown_selection}')
    folder_name = os.listdir(path_to_user_folder)[0]
    unzipped_path = path_to_user_folder + f'/{folder_name}'
    try:
        datafarm = DataFarm(unzipped_path)
        shutil.rmtree(path_to_user_folder) 
    except FileNotFoundError:
        shutil.rmtree(path_to_user_folder) 
        return [f'Error: Please ensure files are stored within a folder in your zip file and try again.']
    except UnboundLocalError as e:
        print(e)
        shutil.rmtree(path_to_user_folder) 
        return [f'Invalid Convokit object. Please try again.']

    return datafarm


def save_files(speaker_df, group_df, speaker_time_df, group_time_df, utt_df, speaker_meta_df, group_meta_df):
    """
    Save the processed DataFrames to a Redis database

    :param speaker_df: DataFrame of speaker information
    :param group_df: DataFrame of conversation ("group") information
    :param speaker_time_df: DataFrame of combined speaker & time information
    :param group_time_df: DataFrame of combined conversation & time information
    :param speaker_df: DataFrame of speaker metadata information
    :param group_df: DataFrame of conversation metadata information
    :param utt_df: DataFrame of utterance information
    """ 

    if 'REDIS_URL' in os.environ:
        r = redis.from_url(redis_url) # Production environment
    else:
        r = redis.Redis(host='localhost', port=6379, db=0) # Local deployment

    r.set(f"{user_id}_speaker_df", zlib.compress(pickle.dumps(speaker_df)), ex=86400)  # expires in 24hrs
    r.set(f"{user_id}_group_df", zlib.compress(pickle.dumps(group_df)), ex=86400) 

    r.set(f"{user_id}_speaker_time_df", zlib.compress(pickle.dumps(speaker_time_df)), ex=86400)  
    r.set(f"{user_id}_group_time_df", zlib.compress(pickle.dumps(group_time_df)), ex=86400) 

    r.set(f"{user_id}_speaker_meta_df", zlib.compress(pickle.dumps(speaker_meta_df)), ex=86400)
    r.set(f"{user_id}_group_meta_df", zlib.compress(pickle.dumps(group_meta_df)), ex=86400)

    r.set(f"{user_id}_utt_df", zlib.compress(pickle.dumps(utt_df)), ex=86400) 

# Callbacks

@dash.callback(
    Output(component_id='submit_button', component_property='disabled'),
    Output(component_id='uploaded_zip', component_property='children'),
    Input(component_id='options_dropdown', component_property='value'),
    Input(component_id='uploaded_zip', component_property='contents'),
    Input(component_id='uploaded_zip', component_property='filename'),
    prevent_initial_call=True
)
def update_button(dropdown_value, zipfile, filename):
    """
    Enables/disables the submit button according to whether or not content is selected/uploaded.

    :param dropdown_value: Content from the dropdown component
    :param zipfile: Content from upload component
    :param filename: The name of the file uploaded
    :return: Boolean representing whether or not to disable the button 
    :return: Content to update the upload component text with
    """
    if zipfile is not None:
        return False, f'Uploaded file: {filename}'
    elif dropdown_value is not None:
        return False, 'Drag and Drop or Select Files'
    else: # Dropdown de-selected
        return True, 'Drag and Drop or Select Files'
    

@dash.callback(
    output=[
        Output(component_id='jsonified_user_id', component_property='data'),
        Output(component_id='corpus_name', component_property='data'),
        Output(component_id='error_message', component_property='children'),
        Output(component_id='url', component_property='href'),
    ],
    inputs=[
        Input(component_id='submit_button', component_property='n_clicks'),
    ],
    state=[
       State(component_id='options_dropdown', component_property='value'),
       State(component_id='uploaded_zip', component_property='contents'),
       State(component_id='uploaded_zip', component_property='filename'),
    ],
    background=True,
    running=[
        (
            Output("submit_button", "style"),
            {"visibility": "hidden"},
            {"visibility": "visible"},
        ),
        (
            Output("progress_bar", "style"),
            {"visibility": "visible"},
            {"visibility": "hidden"},
        ),
    ],
    progress=[
        Output("progress_bar", "value"), 
        Output("progress_bar", "label")
    ],
    prevent_initial_call=True,
)
def pre_process_data(set_progress, n_clicks, dropdown_selection, user_zip_path, filename):
    """
    Grabs user input file, pre-process the conversation Corpus and saves the resulting DataFrames
    
    :param set_progress: Value to set load bar
    :param n_clicks: The number of times the submit button is pressed
    :param dropdown_selection: Content from dropdown component
    :param user_zip_path: Content from upload component
    :param filename: The name of the file uploaded
    :return: The unique user session ID
    :return: The name of the corpus input
    :return: An error message
    :return: The website path
    """
    if n_clicks is None: 
        raise PreventUpdate

    datafarm = None
    corpus_name = ''
    current_value = 0

    if user_zip_path is not None:
        set_progress((current_value, "Validating corpus..."))
        corpus_name = filename[:-4].replace("-", " ").replace("_", " ").title() # Remove zip extension 
        datafarm = process_zip(user_zip_path, filename)
    elif dropdown_selection is not None: 
        set_progress((current_value, "Grabbing corpus..."))
        corpus_name = dropdown_selection
        datafarm = process_dropdown(dropdown_selection)

    current_value += 5
    set_progress((current_value, "Processing corpus..."))

    # If instantiation returned an error code
    if type(datafarm) is list:
        return None, None, datafarm, None # Datafarm contains an error message
    elif type(datafarm.corpus) is list:
        return None, None, datafarm.corpus, None # Datafarm.corpus contains an error message

    current_value += 5
    set_progress((current_value, "Cleaning corpus..."))

    old_stdout = sys.stdout
    # Capture stdout data from ConvoKit function & pass to loading bar
    try:
        sys.stdout = ProgressCapture(set_progress, current_value)
        datafarm.pre_process()  
    finally:
        sys.stdout = old_stdout

    current_value += 55
    set_progress((current_value, "Calculating speaker statistics..."))

    speaker_df, speaker_time_df, speaker_meta_df = datafarm.create_speaker_dfs() 
    speaker_df = datafarm.clean_columns(speaker_df)
    speaker_time_df = datafarm.clean_columns(speaker_time_df)

    current_value += 10
    set_progress((current_value, "Calculating group statistics..."))

    group_df, group_time_df, group_meta_df = datafarm.create_group_dfs(speaker_df, speaker_time_df)
    group_df = datafarm.clean_columns(group_df)
    group_time_df = datafarm.clean_columns(group_time_df)

    current_value += 10
    set_progress((current_value, "Calculating utterance statistics..."))

    utt_df = datafarm.corpus.get_utterances_dataframe()
    utt_df = datafarm.format_utt_df(utt_df)
    utt_df = datafarm.clean_columns(utt_df)

    current_value += 10
    set_progress((current_value, "Saving..."))

    save_files(speaker_df, group_df, speaker_time_df, group_time_df, utt_df, speaker_meta_df, group_meta_df)

    set_progress((100, "100%"))

    return json.dumps(str(user_id)), json.dumps(str(corpus_name)), [''], '/overview'
   


    
