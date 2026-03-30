from dash import dcc, html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
from sklearn import preprocessing

import dash_bootstrap_components as dbc
import dash
import redis
import json
import pickle
import zlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import string
import contractions
import re
import os

dash.register_page(__name__, path='/comparison')

if 'REDIS_URL' in os.environ:
    r = redis.from_url(os.environ.get("REDIS_URL")) # Production environment
else:
    r = redis.Redis(host='localhost', port=6379, db=0) # Local deployment

feature_list = ["age of acquisition", "concreteness", "familiarity", "imageability",
                "please", "please start", "has hedge", "indirect (btw)", "hedges", "factuality",
                "deference", "gratitude", "apologizing", "1st person please", "1st person", 
                "1st person start", "2nd person", "2nd person start", "indirect (greeting)",
                "direct question", "direct start", "has positive", "has negative", "subjunctive", "indicative"]

layout = html.Div(
    children=[
        # Header
        html.Div(
            children=[
                "Linguistic Feature Explorer"
            ],
            className="page_header"
        ),
        # Nav
        html.Div(
            children=[
                dcc.Link(
                    html.Button(
                        children="Overview",
                        className="overview_button"
                    ),
                    href='/overview'
                ),
                dcc.Link(
                    html.Button(
                        children="Timeline",
                        className="timeline_button"
                    ),
                    href='/timeline'
                ),
                html.Button(
                    children="Comparison",
                    className="comparison_button"
                ),
            ],
            className="nav"
        ),
        # Row Div
        html.Div(
            children=[
                # Left Column
                html.Div(
                    children=[
                        # Page Sort
                        html.Div(
                            children=[
                                html.Div(
                                    children=[
                                        "Page View Mode",
                                        html.Span(
                                            "info",
                                            className="material-symbols-outlined info",
                                            id='page_view_id'
                                        ),
                                        dbc.Tooltip(
                                            "View the page & visualizations according to either the speaker or group dataset",
                                            target="page_view_id",
                                            placement="top"
                                        )
                                        ],
                                    className="page_view_header",
                                ),
                                dcc.RadioItems(
                                    [
                                        {'label': 'Sort-by Speaker', 'value': 'speaker'},
                                        {'label': 'Sort-by Group', 'value': 'group'}
                                    ], 
                                    value='group', 
                                    inline=True,
                                    id='radio_buttons',
                                    inputStyle={"margin-right": "5px"}, # between the icon and the label
                                    labelStyle={'display': 'inline-block', 'margin-right': '10px'} # between radio buttons
                                ),
                            ],
                            className="page_view"
                        ),
                        
                        html.Div(
                            children=[
                                html.Div(
                                    children=[
                                        "Feature Correlations",
                                        html.Span(
                                            "info",
                                            className="material-symbols-outlined info",
                                            id='scatter_graph_info'
                                        ),
                                        dbc.Tooltip(
                                            "Compare the correlation of features with a scatterplot",
                                            target="scatter_graph_info",
                                            placement="top"
                                        ),
                                        ],
                                    className="page_view_header",
                                ),

                                html.Div(
                                    children=[
                                        html.Div(
                                            children=[
                                                html.Div(
                                                    "Feature X: ",
                                                    className='scatter_subtitle'
                                                    ),

                                                dcc.Dropdown(
                                                    placeholder='Select a new x-axis',
                                                    id='scatter_x_dropdown',
                                                    options=feature_list,
                                                    searchable=False
                                                ),
                                            ],
                                            className='dropdown_col'
                                        ),
                                        

                                        html.Div(
                                            children=[
                                                html.Div(
                                                    "Feature Y: ",
                                                    className='scatter_subtitle'
                                                    ),

                                                dcc.Dropdown(
                                                    placeholder='Select a new y-axis',
                                                    id='scatter_y_dropdown',
                                                    options=feature_list,
                                                    searchable=False
                                                ),
                                            ],
                                            className='dropdown_col'
                                        ),
                                    ],
                                    className='dropdown_row'
                                ),

                                html.Div(
                                    children=[
                                        html.Div(
                                            "On-Hover Features: ",
                                            className='scatter_subtitle'
                                            ),

                                        dcc.Dropdown(
                                            placeholder='Select features visible on-hover',
                                            multi=True,
                                            id='scatter_hover_dropdown',
                                        ),
                                    ],
                                    className='dropdown_col'
                                )
                            ],
                            className='graph_dropdown'
                        ),

                        dcc.Graph(
                            id='scatter_plot',
                        ),
                        

                    ],
                    className='column_a'
                ),
                # Right Column
                html.Div(
                    children=[
                    # Table
                    html.Div (
                        children=[
                            html.Div(
                                children=[
                                    "Feature Dataset",
                                    html.Span(
                                        "info",
                                        className="material-symbols-outlined info",
                                        id='feature_dataset_info'
                                    ),
                                    dbc.Tooltip(
                                        "The dataset of extracted linguistic features",
                                        target="feature_dataset_info",
                                        placement="top"
                                    ),
                                ],
                                className='section_subheader'
                            ),

                            html.Div(
                                children=[
                                    dash_table.DataTable(
                                        id='data_table',
                                        style_table={
                                            'overflowX': 'auto',
                                            'overflowY': 'auto',
                                            'height': '275px'
                                                    },
                                        style_cell={
                                            'textAlign': 'left',
                                            'border': '1px solid rgb(180, 180, 180)'
                                                    },
                                        style_header={
                                            'background': 'rgb(240, 240, 240)',
                                        },
                                        sort_action="native"
                                    ),
                                ],
                                id='table_container'
                            ),
                        ],
                        id='table'
                    ),

                    # Utterance View
                    html.Div(
                        children=[
                            html.Div(
                                children=[
                                    "Individual Utterance View",
                                    html.Span(
                                        "info",
                                        className="material-symbols-outlined info",
                                        id='utterance_view_info'
                                    ),
                                    dbc.Tooltip(
                                        "View the features of an individual utterance. Highlighted text represent markers for a feature (limited to politeness features only).",
                                        target="utterance_view_info",
                                        placement="top"
                                    ),
                                ],
                                className='utterance_subheader'
                            ),

                            html.Div( 
                                children=[
                                    html.Div(
                                        children=[
                                            html.Div("Utterance ID:"),

                                            dcc.Dropdown(
                                                id='utterance_id_dropdown',
                                                searchable=True
                                            ),
                                        ],
                                        className='dropdown_col'
                                    ),

                                    html.Div(
                                        children=[
                                            html.Div("Feature:"),

                                            dcc.Dropdown(
                                                placeholder='Select a new utterance',
                                                id='utterance_feature_dropdown',
                                                searchable=True
                                            ),
                                        ],
                                        className='dropdown_col'
                                    ),
                                ],
                                className='dropdown_row'
                            ),
                            
                            
                            html.P(
                                'Utterance Text',   
                                id='utterance_text_subheader'
                            ),

                            html.Div(
                                '',
                                id='utterance_text'
                            ),

                            html.Hr(),

                            html.Div(
                                'Feature Score',   
                                id='utterance_feature_subheader'
                            ), 

                            html.Div(id='utterance_feature_score'),

                            html.Hr(),

                            html.Div(
                                'Metadata',
                                id='utterance_metadata_subheader'
                            ),

                            html.Div(
                                children=[
                                    html.Div(  
                                        id='utterance_speaker'
                                    ), 

                                    html.Div(  
                                        id='utterance_group'
                                    ), 

                                    html.Div(
                                        id='utterance_timestamp'
                                    ),

                                    html.Div(  
                                        id='utterance_reply_to'
                                    ),
                                ],
                                id='utterance_metadata_block'
                            ) 
                        ],
                        className='utterance_view'
                    ), 
                    
                    ],
                    className='column_b'
                ),
            ],
            className='row'
        )

    ],
    className="comparison_page"
)

# Functions

def get_df(jsonified_user_id, radio_value, time):
    """
    Loads and returns the correct DataFrame according to the input values

    :param jsonified_user_id: The user session ID
    :param radio_value: The selected radio button value ("group" or "speaker")
    :param time: Whether or not the DataFrame includes time values (True or False)
    :return: Selected DataFrame
    """
    user_id = json.loads(jsonified_user_id)
    df = pd.DataFrame()

    if radio_value == 'group' and not time:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_group_df")))
    elif radio_value == 'speaker' and not time: 
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_speaker_df")))
    elif radio_value == 'group' and time:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_group_time_df")))
    elif radio_value == 'speaker' and time:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_speaker_time_df")))

    return df


def grab_markers(data, feature):
    """
    Returns the utterance with markers annotated
    
    :param data: A DataFrame row of utterance data
    :param feature: The linguistic feature marker to extract
    :return: The annotated utterance (or non-annotated if no markers found)
    """
    marked_text = html.Div(children=[])

    if feature == '1st_person_plural':
        feature = '1st_person_pl.'

    col = f'politeness_markers_{feature}'

    if col in data and data.loc[col] != []:
        markers = data.loc[col] # Grab data marker(s)
        markers = [element for innerList in markers for element in innerList] # Un-nest list
        markers = [tuple[0] for tuple in markers] # Get first element in each tuple

        text = data['text'].split() # Split sentences into words

        for word in text:
            cleaned_word = re.sub(r"[^\w\d'\s]+", '', word) # Remove punctuation
            cleaned_word = cleaned_word.lower().strip()
            cleaned_word = contractions.fix(cleaned_word)
            cleaned_word = cleaned_word.split() # Split any words that were contractions

            if any(tok in markers for tok in cleaned_word):
                marked_text.children.append(' ')
                marked_text.children.append(html.Span(f'{word}', className='markers'))
            else:
                marked_text.children.append(f' {word}')
    else:
        return data['text']


    return marked_text


# Callbacks

@dash.callback(
    Output(component_id='utterance_id_dropdown', component_property='options'),
    Output(component_id='utterance_id_dropdown', component_property='placeholder'),
    Output(component_id='utterance_feature_dropdown', component_property='options'),
    Output(component_id='utterance_feature_dropdown', component_property='placeholder'),
    Input(component_id='jsonified_user_id', component_property='data'),
)
def populate_utterance_dropdowns(jsonified_user_id):
    """
    Populates the options and placeholders for the utterance dropdowns

    :param jsonified_user_id: The user session ID
    :return: The utterance ID options
    :return: Placeholder text
    :return: A list of linguistic features
    :return: Placeholder text
    """
    user_id = json.loads(jsonified_user_id)
    utt_df = pickle.loads(zlib.decompress(r.get(f"{user_id}_utt_df")))

    return utt_df.index, 'Select an utterance', feature_list, 'Select a feature'


@dash.callback(
    Output(component_id='utterance_text', component_property='children'),
    Output(component_id='utterance_speaker', component_property='children'),
    Output(component_id='utterance_group', component_property='children'),
    Output(component_id='utterance_timestamp', component_property='children'),
    Output(component_id='utterance_reply_to', component_property='children'),
    Output(component_id='utterance_feature_subheader', component_property='children'),
    Output(component_id='utterance_feature_score', component_property='children'),
    Input(component_id='jsonified_user_id', component_property='data'),
    Input(component_id='utterance_id_dropdown', component_property='value'),
    Input(component_id='utterance_feature_dropdown', component_property='value'),
    prevent_initial_call=True,
)
def populate_utterance_data(jsonified_user_id, utt_id, feature):
    """
    Populates the utterance table with relevant values
    
    :param jsonified_user_id: The user session ID
    :param utt_id: The selected utterance ID
    :param feature: The selected linguistic feature
    :return: The utterance text
    :return: The utterance's speaker
    :return: The utterance's group
    :return: The utterance's timestamp
    :return: Who the utterance is in reply to
    :return: The utterance feature being observed
    :return: The utterance's feature score
    """
    if utt_id is None or feature is None: 
        raise PreventUpdate

    user_id = json.loads(jsonified_user_id)
    utt_df = pickle.loads(zlib.decompress(r.get(f"{user_id}_utt_df"))) 
    utt_df['text'] = utt_df['text'].astype(str)

    row = utt_df.loc[utt_id]
    
    text = grab_markers(row, feature.replace(" ", "_"))
    speaker = 'Speaker: ' + str(row['speaker']) 
    group = 'Group: ' + str(row['conversation_id'])
    timestamp = 'Timestamp: ' + str(row['timestamp']) 
    reply_to = 'Reply To: ' + str(row['reply_to'])
    feat_score = f'{string.capwords(feature)} Score' 
    value = str(row[feature.replace(" ", "_")])

    return text, speaker, group, timestamp, reply_to, feat_score, value


@dash.callback(
    Output(component_id='scatter_hover_dropdown', component_property='options'),
    Input(component_id='radio_buttons', component_property='value'),
    prevent_initial_callback=True
)
def populate_scatter_dropdown(radio_value):
    """
    Populates the dropdown options for the on-hover feature
    
    :param radio_value: The selected radio button value ("group" or "speaker")
    :return: A list of the feature options
    """
    if radio_value == 'speaker':
        list = feature_list.copy()
        list.append('speaker id')

        return list
    elif radio_value == 'group':
        list = feature_list.copy()
        list.append('group id')

        return list
    

@dash.callback(
    Output(component_id='scatter_plot', component_property='figure'),
    Input(component_id='jsonified_user_id', component_property='data'),
    Input(component_id='radio_buttons', component_property='value'),
    Input(component_id='scatter_x_dropdown', component_property='value'),
    Input(component_id='scatter_y_dropdown', component_property='value'),
    Input(component_id='scatter_hover_dropdown', component_property='value'),
)
def populate_scatterplot(jsonified_user_id, radio_value, dropdown_x_value, dropdown_y_value, hover_value):
    """
    Populates the scatterplot

    :param jsonified_user_id: The user session ID
    :param radio_value: The selected radio button value ("group" or "speaker")
    :param dropdown_x_value: The selected x-axis value
    :param dropdown_y_value: The selected y-axis value
    :param hover_value: The selected value(s) to appear on-hover of a point
    :return: A scatterplot
    """
    df = get_df(jsonified_user_id, radio_value, False)
    
    # Populate scatterplot with random features if none are selected
    if dropdown_x_value is None or dropdown_y_value is None:
        raise PreventUpdate
    
    dropdown_x_value = dropdown_x_value.replace(" ", "_")
    dropdown_y_value = dropdown_y_value.replace(" ", "_")

    if hover_value is not None:
        hover_value = [value.replace(" ", "_") for value in hover_value]

    figure = px.scatter(
        df, 
        x=dropdown_x_value, y=dropdown_y_value,
        color=dropdown_y_value, hover_data=hover_value
    )
    

    return figure