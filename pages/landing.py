from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
from datafarm import *
from zipfile import ZipFile
from pathlib import Path

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
        folder = folder[:-4].replace('-', ' ') # Remove zip extension & hyphen for display purposes
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
                    className="material-symbols-outlined"
                ),
                'Select a pre-created corpus from ConvoKit\'s ',
                html.A(
                    children="website",
                    href="https://convokit.cornell.edu/documentation/datasets.html"
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
            className='options_text'
        ),

        html.Div(
            children=[
                html.Span(
                    "counter_2",
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
                        value=0, striped=True, 
                        animated=True, 
                        style={"visibility":"hidden"}
                    )
            ],
            style={
                "width": "30%",
                "height": "30px",
                "margin": "0 auto",
                "margin-top": "-15px",
                "margin-bottom": "80px",
                },
        ),

    ],
)

# Functions 

def process_zip(user_zip_path, filename, datafarm):
    """
    Processes the zip file uploaded by the user

    :param user_zip_path: The file path to the zip file
    :param filename: The name of the zip file
    :param datafarm: An Object to be instantiated
    :return: The instantiated Object or an error message
    """
    content_type, content_string = user_zip_path.split(',')
    decoded = base64.b64decode(content_string)
    zip_str = io.BytesIO(decoded)

    try:
        zip_file = ZipFile(zip_str, 'r')
        zip_file.extractall(path_to_user_folder)

        # Check for multiple files 
        if len(os.listdir(path_to_user_folder)) > 1:
            shutil.rmtree(path_to_user_folder)
            return ['Please only upload one zipped folder at a time.']
        
        # Grab unzipped contents
        unzipped_path = os.listdir(path_to_user_folder)[0]
        
        try:
            datafarm = DataFarm(unzipped_path)
            shutil.rmtree(path_to_user_folder)
        except FileNotFoundError:
            shutil.rmtree(path_to_user_folder) 
            return ['Error: Please ensure files are stored within a folder in your zip file and try again.']
        except UnboundLocalError:
            shutil.rmtree(path_to_user_folder) 
            return ['Invalid Convokit object. Please try again.']

    except zipfile.BadZipFile:
        shutil.rmtree(path_to_user_folder)
        return [f'Error: {filename} is a bad zipfile. Please try again.']

    return datafarm


def process_dropdown(dropdown_selection, datafarm):
    """
    Processes the dropdown selection by the user

    :param dropdown_selection: The file selected
    :param datafarm: An Object to be instantiated
    :return: The instantiated Object or an error message
    """
    dropdown_selection = dropdown_selection.replace(' ', '-') + '.zip'

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
    except UnboundLocalError:
        shutil.rmtree(path_to_user_folder) 
        return [f'Invalid Convokit object. Please try again.']

    return datafarm


def save_files(speaker_df, group_df, speaker_time_df, group_time_df, utt_df):
    """
    Save the processed DataFrames to a Redis database

    :param speaker_df: DataFrame of speaker information
    :param group_df: DataFrame of conversation ("group") information
    :param speaker_time_df: DataFrame of combined speaker & time information
    :param group_time_df: DataFrame of combined conversation & time information
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
    :return: An error message
    :return: The status of the processing
    """
    if n_clicks is None: 
        raise PreventUpdate

    start = time.time()
    datafarm = None

    set_progress((20, "20%"))

    if user_zip_path is not None:
        datafarm = process_zip(user_zip_path, filename, datafarm)
    elif dropdown_selection is not None: 
        datafarm = process_dropdown(dropdown_selection, datafarm)
        
    # If instantiation returned an error code
    if type(datafarm) is list:
        return None, datafarm, None # Datafarm contains an error message
    elif type(datafarm.corpus) is list:
        return None, datafarm.corpus, None # Datafarm.corpus contains an error message
    
    set_progress((40, "40%"))

    datafarm.pre_process()
    
    set_progress((60, "60%"))
    
    speaker_df, speaker_time_df = datafarm.create_speaker_dfs() 
    speaker_df = datafarm.clean_columns(speaker_df)
    speaker_time_df = datafarm.clean_columns(speaker_time_df)

    set_progress((80, "80%"))

    group_df, group_time_df = datafarm.create_group_dfs(speaker_df, speaker_time_df)
    group_df = datafarm.clean_columns(group_df)
    group_time_df = datafarm.clean_columns(group_time_df)

    set_progress((90, "90%"))

    utt_df = datafarm.corpus.get_utterances_dataframe()
    utt_df = datafarm.format_utt_df(utt_df)
    utt_df = datafarm.clean_columns(utt_df)

    save_files(speaker_df, group_df, speaker_time_df, group_time_df, utt_df)
    
    set_progress((100, "100%"))

    end = time.time()

    print("=====")
    print(speaker_df)
    print(group_df)
    print(utt_df)
    print("=====")

    return json.dumps(str(user_id)), [''], '/overview'
   


    
