from dash import Dash, html, dcc, Output, Input, State
from flask import Flask, send_from_directory
from urllib.parse import quote as urlquote

import dash
import os
import base64
import dash_uploader as du

# UPLOADED FILES + APP CONFIGURATION

UPLOAD_FOLDER_ROOT = "uploadedfiles"

if not os.path.exists(UPLOAD_FOLDER_ROOT):
    os.makedirs(UPLOAD_FOLDER_ROOT)


app = Dash(__name__, use_pages=True)

du.configure_upload(app, UPLOAD_FOLDER_ROOT)

# APP LAYOUT

def get_app_layout():
    return html.Div([

        dcc.Link(
            html.H1(
                children='HEADER',
                className='header',
            ),
            href='/'
        ),
        
        dcc.Store(id='selected-corpus-dropdown', storage_type='session'), # saved until page reloaded

        dash.page_container

    ])

# CALLBACKS

app.layout = get_app_layout

@du.callback(
    output=Output("uploader-output", "children"),
    id="upload-data",
)
def callback_on_completion(status: du.UploadStatus):
    """
    Updates front-end with string containing recently uploaded file

    :param du.UploadStatus: Current upload status
    :return: String containing uploaded files
    """ 
    return html.Ul([html.Li(str(x)) for x in status.uploaded_files])

# MAIN

if __name__ == '__main__':
    app.run_server(debug=True, port=8888)