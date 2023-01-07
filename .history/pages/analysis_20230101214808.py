from dash import Dash, dcc, callback, html, Input, Output, State

import sys
import dash
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import numpy as np


sys.path.append('..') # for relative import of datafarm.py

dash.register_page(__name__, path='/analysis')

test = 0

# Line Graph
x = np.arange(10)
line_graph = go.Figure(data=go.Scatter(x=x, y=x**2))
line_graph.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="#01161E",
            paper_bgcolor="#01161E",
            font_color="white"
        )

# APP LAYOUT

layout = html.Div(
    children=[

        html.Div(
            children=[

                dcc.RadioItems(
                    [
                        {'label': 'Sort-by Group', 'value': 'group-graph'},
                        {'label': 'Sort-by Speaker', 'value': 'spkr-graph'}
                    ], 
                    value='group-graph', 
                    inline=True,
                    id='radio',
                ),

                html.Div(
                    children=[

                            dcc.Graph(
                                style={
                                    'width': '100%', 
                                    'height': '100%',
                                    },

                                id='graph'

                                ),

                        ],    

                    className='column'

                ),


                html.Div(
                        children=[

                            html.H3(
                                'Group #',
                                style={
                                    'padding': '0',
                                    'margin': '0 auto',
                                    'color': 'white',
                                    'textAlign': 'center',
                                    'lineHeight': '0px',
                                    'fontWeight': 'normal'
                                }
                            ), 
                           
                        ],

                    className='h3-text',

                    ),

                html.Div(
                    children=[
                    
                        html.Div(
                            children=[
                                
                                html.Div(

                                children=[
                                    dcc.Graph(
                                        figure=line_graph,
                                        id='line-graph',
                                        style={'width': '100%', 'height': '100%'}
                                    )
                                ],   

                                className='sub-a'
                                ),

                                html.Div(

                                    children=[

                                        html.H3(
                                            'Feature Utterance:',
                                            className='page2-subtitles'
                                        ), 

                                        html.P(
                                            'Selected Feature: Group Satisfaction',
                                        ),

                                        html.P(
                                            'Score: 123',
                                        ), 

                                        html.P(
                                            'Ex. Utterance: Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                                        ), 
                                    ],

                                className='sub-b'
                                ),

                            ],  

                            className='mini-column-a',

                        ),

                        html.Div(
                            children=[

                                 html.H3(
                                    'Feature Selection:',
                                    className='page2-subtitles'
                                 ), 

                                 dcc.Dropdown([
                                    'Group Satisfaction', 'Hedging', 
                                    'First Person Please', 'First Person Start', 'Personal Pronouns',
                                    'Prepositions'], 'Group Satisfaction',

                                    style={
                                        'color': 'black',
                                        }
                                    ),
                                    

                            ],   

                            className='mini-column-b'

                        ),

                    ],

                    className='column'

                )
                
            ],
            
            className='row'

        ),

        dcc.Link(
                html.Button(
                    children='Next', 
                    className='submit-button'
                ),
                href='/analytics'
        ),

        html.Div(
            id='output-container',
            style={'color': 'white'}
        ),

    ]
)


# CALLBACKS

@dash.callback(
    Output(component_id='output-container', component_property='children'),
    Input(component_id='df-files', component_property='data')
)
def update_output(data):
    return html.H3(f'Data: {data}')

   
@dash.callback(
    Output(component_id='graph', component_property='figure'),
    Input(component_id='radio', component_property='value')
)
def configure_graph(value):
    if value == 'group-graph':
        df = pd.read_csv("ugi-gap-grp-feats.csv")
        bar_graph = px.bar(
                    df, x='Group', y='Group_Sat',
                )
    elif value == 'spkr-graph':
        df = pd.read_csv("ugi-gap-gen-spkr-feats.csv")
        bar_graph = px.bar(
                    df, x='article', y='quant', # temp graph for functionality purposes - setup actual graph later
                )

    bar_graph.update_layout(
                margin=dict(l=20, r=20, t=15, b=15),
                paper_bgcolor="#01161E",
                plot_bgcolor="#01161E",
                font_color="white",
            )
    
    return bar_graph



    
    

