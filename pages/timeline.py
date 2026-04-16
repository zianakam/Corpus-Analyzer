from dash import dcc, html, dash_table, Input, Output
from dash.exceptions import PreventUpdate
from datetime import timedelta

import dash_bootstrap_components as dbc
import dash
import redis
import json
import pickle
import zlib
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import os

dash.register_page(__name__, path='/timeline', title='Timeline')

if 'REDIS_URL' in os.environ:
    r = redis.from_url(os.environ.get("REDIS_URL")) # Production environment
else:
    r = redis.Redis(host='localhost', port=6379, db=0) # Local deployment

feature_list = ["age of acquisition", "concreteness", "familiarity", "imageability",
                "please", "please start", "has hedge", "indirect (btw)", "hedges", "factuality",
                "deference", "gratitude", "apologizing", "1st person plural", "1st person", 
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
                html.Button(
                    children="Timeline",
                    className="timeline_button"
                ),
                dcc.Link(
                    html.Button(
                        children="Comparison",
                        className="comparison_button"
                    ),
                    href='/comparison'
                )
            ],
            className="nav"
        ),

        # Row Div
        html.Div(
            children=[
                # Left Column
                html.Div(
                    children=[
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

                        # Line Graph
                        html.Div(
                            children=[
                                html.Div(
                                    children=[
                                        "Feature Trends",
                                        html.Span(
                                            "info",
                                            className="material-symbols-outlined info",
                                            id='line_graph_info'
                                        ),
                                        dbc.Tooltip(
                                            "View the way feature scores change over the course of the conversation (averaged & split into 5 turns)",
                                            target="line_graph_info",
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
                                                    children=["Group(s) ID:"],
                                                    id='line_graph_id'
                                                ),

                                                dcc.Dropdown(
                                                    multi=True,
                                                    id='line_graph_dropdown',
                                                    searchable=True
                                                ),
                                            ],
                                            className="dropdown_col"
                                        ),
                                

                                    html.Div(
                                        children=[
                                            html.Div("Feature:"),

                                            dcc.Dropdown(
                                                placeholder='Select a feature',
                                                value='factuality',
                                                options=feature_list,
                                                multi=False,
                                                id='line_graph_feature',
                                                searchable=True
                                            ),
                                        ],
                                        className="dropdown_col"
                                    )

                                    ],
                                    className="dropdown_row",
                                ),
                            ],
                        className="graph_dropdown"
                        ),

                        dcc.Graph(id="line_graph"),
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
                                    "Feature Time Dataset",
                                    html.Span(
                                        "info",
                                        className="material-symbols-outlined info",
                                        id='feature_dataset_info'
                                    ),
                                    dbc.Tooltip(
                                        "The dataset of extracted linguistic features, over time (evenly split into 5 turns)",
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

                    # Conversation Trendline
                    html.Div(
                        children=[
                            html.Div(
                                children=[
                                        "Conversation Timeline",
                                        html.Span(
                                            "info",
                                            className="material-symbols-outlined info",
                                            id='conversation_timeline_info'
                                        ),
                                        dbc.Tooltip(
                                            "View the distribution of speaker contributions throughout the conversation.",
                                            target="conversation_timeline_info",
                                            placement="top"
                                        ),
                                    ],
                                className="page_view_header",
                            ),

                            html.Span("Group ID:"),

                            dcc.Dropdown(
                                placeholder='Select a group',
                                searchable=True,
                                id='conversation_timeline_dropdown'
                            ),
                        ],
                        className='conversation_timeline_view'
                    ),

                    dcc.Graph(
                        id='conversation_timeline_graph'
                    )
                    
                    ],
                    className='column_b'
                ),
            ],
            className='row'
        )
    ],
    className="timeline_page"
)

# Functions

def get_default(radio_value, time):
    """
    Returns the default DataFrame if no user corpus was input.

    :param radio_value: The selected radio button value ("group" or "speaker")
    :param time: Whether or not the DataFrame includes time values (True or False)
    :return: Selected DataFrame
    """
    df = pd.DataFrame()

    if radio_value == 'group' and not time:
        df = pd.read_csv('default_datasets/default_group.csv', index_col=False)
    elif radio_value == 'speaker' and not time: 
        df = pd.read_csv('default_datasets/default_speaker.csv', index_col=False)
    elif radio_value == 'group' and time:
        df = pd.read_csv('default_datasets/default_group_time.csv', index_col=False)
    else:
        df = pd.read_csv('default_datasets/default_speaker_time.csv', index_col=False)

    return df

 
def get_df(jsonified_user_id, radio_value, time):
    """
    Loads and returns the correct DataFrame according to the input values

    :param jsonified_user_id: The user session ID
    :param radio_value: The selected radio button value ("group" or "speaker")
    :param time: Whether or not the DataFrame includes time values (True or False)
    :return: Selected DataFrame
    """
    df = pd.DataFrame()
    user_id = None

    if jsonified_user_id is not None:
        user_id = json.loads(jsonified_user_id)

    if user_id is None:
        # Default dataset
        df = get_default(radio_value, time)
    elif radio_value == 'group' and not time:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_group_df")))
    elif radio_value == 'speaker' and not time: 
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_speaker_df")))
    elif radio_value == 'group' and time:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_group_time_df")))
    else:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_speaker_time_df")))

    return df

# Callbacks


@dash.callback(
    Output(component_id='line_graph_id', component_property='children'),
    Input(component_id='radio_buttons', component_property='value'),
)
def populate_line_subheader(radio_value):
    """
    Populates the sub-header for the line graph's id dropdown

    :param radio_value: The selected radio button value ("group" or "speaker")
    :return: A string sub-header
    """
    if radio_value == "speaker":
        return "Speaker(s) ID:"
    else: 
        return "Group(s) ID:"


@dash.callback(
    Output(component_id='line_graph_dropdown', component_property='options'),
    Output(component_id='line_graph_dropdown', component_property='placeholder'),
    Output(component_id='line_graph_dropdown', component_property='value'),
    Input(component_id='jsonified_user_id', component_property='data'),
    Input(component_id='radio_buttons', component_property='value'),
    Input(component_id='line_graph_dropdown', component_property='value'),
)
def populate_line_dropdown(jsonified_user_id, radio_value, dropdown_value):
    """
    Populates the options for the line graph's id dropdown

    :param jsonified_user_id: The user session ID
    :param radio_value: The selected radio button value ("group" or "speaker")
    :return: A list of id values
    """
    df = get_df(jsonified_user_id, radio_value, True)

    if radio_value == 'speaker':
        options = list(set(df['speaker_id']))
        options.sort()

        if dropdown_value == None:
            dropdown_value = df['speaker_id'][0]

        return options, "Select a speaker", dropdown_value
    elif radio_value == 'group':
        options = list(set(df['group_id']))
        options.sort()

        if dropdown_value == None:
            dropdown_value = df['group_id'][0]

        return options, "Select a group", dropdown_value
    

@dash.callback(
    Output(component_id='line_graph', component_property='figure'),
    Input(component_id='radio_buttons', component_property='value'), 
    Input(component_id='line_graph_dropdown', component_property='value'), 
    Input(component_id='line_graph_feature', component_property='value'), 
    Input(component_id='jsonified_user_id', component_property='data'),
)
def populate_line_table(radio_value, selected_id, selected_feat, jsonified_user_id):
    """
    Populates the line graph

    :param radio_value: The selected radio button value ("group" or "speaker")
    :param selected_id: The speaker or conversation ID
    :param selected_feat: The linguistic feature
    :param jsonified_user_id: The user session ID
    :return: A line graph
    """
    if selected_id is None or selected_feat is None:
        return go.Figure()

    df = get_df(jsonified_user_id, radio_value, True)
    id_header = df.columns[1] # Either Group_ID or Speaker_ID
    selected_feat = selected_feat.replace(" ", "_")
    feat_df = df[[id_header, 'time', selected_feat]]
    line_graph = go.Figure()

    if type(selected_id) is list: # Multiple IDs selected
        for index, id in enumerate(selected_id):
            subset_df = feat_df[feat_df[id_header] == selected_id[index]]
            line_graph.add_trace(
                go.Scatter(
                    x=subset_df['time'], 
                    y=subset_df[selected_feat],
                    mode='lines+markers',
                    name=selected_id[index]
                )
            )
    else: # Single ID selected
        subset_df = feat_df[feat_df[id_header] == selected_id]
        line_graph.add_trace(
            go.Scatter(
                x=subset_df['time'], 
                y=subset_df[selected_feat],
                mode='lines+markers',
                name=selected_id
            )
        )

    line_graph.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Time (Turns)",
        yaxis_title=selected_feat.replace("_", " ").capitalize(),
    )

    return line_graph


@dash.callback(
    Output(component_id='conversation_timeline_dropdown', component_property='options'),
    Output(component_id='conversation_timeline_dropdown', component_property='value'),
    Input(component_id='jsonified_user_id', component_property='data'),
    Input(component_id='conversation_timeline_dropdown', component_property='value'),
)
def populate_timeline_dropdown(jsonified_user_id, dropdown_value):
    """
    Populates the options for the timeline dropdown

    :param jsonified_user_id: The user session ID
    :return: A list of conversation ids
    """
    df = get_df(jsonified_user_id, 'group', True)
    options = list(set(df['group_id']))
    options.sort()

    if dropdown_value == None:
        dropdown_value = df['group_id'][0]

    return options, dropdown_value


@dash.callback(
    Output(component_id='conversation_timeline_graph', component_property='figure'),
    Input(component_id='conversation_timeline_dropdown', component_property='value'), 
    Input(component_id='jsonified_user_id', component_property='data'),
)
def populate_timeline(selected_convo, jsonified_user_id):
    """
    Populates the timeline graph

    :param jsonified_user_id: The user session ID
    :param selected_convo: The conversation ID
    :return: A Gantt chart
    """
    if selected_convo is None:
        return go.Figure()
    
    df = pd.DataFrame()

    if jsonified_user_id is not None:
        user_id = json.loads(jsonified_user_id)
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_utt_df"))) 
    else: # Default dataset
        df = pd.read_csv('default_datasets/default_utt.csv', index_col=False)
        df['timestamp'] = pd.to_timedelta(df['timestamp'])


    df = df[df['conversation_id'] == selected_convo]

    time_df = pd.DataFrame(columns=["Speaker", "Start", "Finish"])
    curr_speaker = df['speaker'].iloc[0]
    curr_start = df['timestamp'].iloc[0]
    base_time = pd.Timestamp("2000-01-01")
    index = 0
    
    for row in df.itertuples():
        if row.speaker != curr_speaker:
            curr_speaker = row.speaker 
            curr_start = row.timestamp
            finish = row.timestamp + timedelta(seconds=2)
            index += 1
            data = dict(Speaker=row.speaker , Start=base_time + curr_start, Finish=base_time + finish)
            time_df = pd.concat([time_df, pd.DataFrame([data])], ignore_index=True)
        else:
            data = dict(Speaker=row.speaker , Start=base_time + curr_start, Finish=base_time + row.timestamp)
            time_df.loc[index, ["Task", "Start", "Finish"]] = pd.Series(data)

    
    fig = px.timeline(time_df, x_start="Start", x_end="Finish", y="Speaker", color="Speaker")
    fig.update_yaxes(
            autorange="reversed",
        )
    fig.update_layout(
        xaxis=dict(
            title_text="Time",
            tickformat="%H:%M:%S.%L"    
        )
    )

    return fig



