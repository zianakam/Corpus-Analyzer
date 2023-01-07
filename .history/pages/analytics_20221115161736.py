from dash_extensions.enrich import Dash, dcc, html, Input, Output
#from dash import Dash, dcc, html, Input, Output
import dash
import plotly.express as px
import pandas as pd

dash.register_page(__name__, path='/analytics')

layout = html.Div(
    children=[

        html.H3(
            'Feature Scores:',
            className='analytics-text',
        ),

        #Program to generate this over & over according to feats avail
        html.Div(
            children=[
                html.P(
                    '(1) Politeness - Hedging',
                ),

                html.P(
                    'Score: 123',
                ), 

                html.P(
                    'Ex. Utterance: Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                ),  
            ],  
            className='analytics-text'
        ),

        html.Div(
            children=[
                html.P(
                    '(1) Politeness - Hedging',
                ),

                html.P(
                    'Score: 123',
                ), 

                html.P(
                    'Ex. Utterance: Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                ),  
            ],  
            className='analytics-text'
        ),

        html.Div(
            children=[
                html.P(
                    '(1) Politeness - Hedging',
                ),

                html.P(
                    'Score: 123',
                ), 

                html.P(
                    'Ex. Utterance: Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                ),  
            ],  
            className='analytics-text'
        ),

        html.Div(
            'Features Not Available:',
            className='analytics-text'
        ),

        dcc.Link(
                html.Button(
                    children='Previous', 
                    className='submit-button'
                ),
                href='/analysis'
        ),
        
    ]
)