from dash import Dash, dcc, callback, html, Input, Output, State
from datafarm import *

import sys
import dash
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import numpy as np


sys.path.append('..') # for relative import of datafarm.py

dash.register_page(__name__, path='/analysis')

# GRAPHS

# Bar Graph
df = pd.read_csv("ugi-gap-grp-feats.csv")
bar_graph = px.bar(
                df, x='Group', y='Group_Sat',
             )

bar_graph.update_layout(
                margin=dict(l=20, r=20, t=15, b=15),
                paper_bgcolor="#01161E",
                plot_bgcolor="#01161E",
                font_color="white",
            )


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
                    ['Sort-by Group', 'Sort-by Speaker'], 
                    'Sort-by Group', 
                    inline=True,
                    className='option2-dropdown',
                ),

                html.Div(
                    children=[

                            dcc.Graph(
                                figure=bar_graph,
                                style={
                                    'width': '100%', 
                                    'height': '100%',
                                    }
                                )

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
        )

    ]
)

# CALLBACKS


"""
@dash.callback(
    Output(component_id='output-container', component_property='children'),
    Input(component_id='selected-corpus-dropdown', component_property='data')
)
"""
@dash.callback(
    Output(component_id='output-container', component_property='children'),
    Input(component_id='button-save', component_property='data'),
    # State(component_id='selected-corpus-dropdown', component_property='data'),
)
def update_output(data):
    if data['button-save'] is not 0:
        print(data['button-save'])

    #print(f'Selected corpus to {data['option1-dropdown']}')
    # pass parent_dir param to datafarm ? so can generalize to uploaded files too w/o having to code more
    """
    datafarm = DataFarm(data)

    spkr_df = datafarm.create_spkr_df() # save these to the page
    print(spkr_df)

    grp_df = datafarm.create_grp_df(spkr_df)
    print(grp_df)
    """
    return html.H3(f'Selected corpus to {data}')
    

