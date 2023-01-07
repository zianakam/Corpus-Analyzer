from dash import Dash, html, dcc, Output, Input, State
from flask import Flask, send_from_directory
from urllib.parse import quote as urlquote

import dash
import os
import base64
import dash_uploader as du

# APP LAYOUT

app = dash.Dash(__name__)

app.layout = html.Div([

        dcc.Link(
            html.H1(
                children='HEADER',
                className='header',
            ),
            href='/'
        ),
        
        dcc.Store(id='df-files', storage_type='local'), # saved until cleared/browser closed

        dash.page_container

    ])

# MAIN

if __name__ == '__main__':
    app.run_server(debug=True, port=8888)