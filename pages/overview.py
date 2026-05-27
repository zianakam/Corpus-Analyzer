from dash import dcc, html, Input, Output, dash_table
from datafarm import *

import dash_bootstrap_components as dbc
import json
import sys
import dash
import plotly.express as px
import pandas as pd
import redis
import pickle
import zlib
import os

sys.path.append('..') # for relative import of datafarm.py

dash.register_page(__name__, path='/overview')

if 'REDIS_URL' in os.environ:
    r = redis.from_url(os.environ.get("REDIS_URL")) # Production environment
else:
    r = redis.Redis(host='localhost', port=6379, db=0) # Local deployment


feature_list = ["age of acquisition", "concreteness", "familiarity", "imageability",
                "please", "please start", "has hedge", "indirect (btw)", "hedges", "factuality",
                "deference", "gratitude", "apologizing", "1st person please", "1st person", 
                "1st person start", "2nd person", "2nd person start", "indirect (greeting)",
                "direct question", "direct start", "has positive", "has negative", "subjunctive", "indicative"]

# App Layout

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
                html.Button(
                    children="Overview",
                    className="overview_button",
                ),
                dcc.Link(
                    html.Button(
                        children="Timeline",
                        className="timeline_button"
                    ),
                    href="/timeline"
                ),
                dcc.Link(
                    html.Button(
                        children="Comparison",
                        className="comparison_button"
                    ),
                    href='/comparison'
                ),
            ],
            className="nav"
        ),
        # Selected Corpus
        html.Div(
            children=[
                html.Div(
                    children=[
                        "Corpus: ",
                    ],
                    id='corpus_annotation'
                ),

                html.Div(
                    children=[
                        html.Div(
                            children=[""],
                            id='selected_corpus'
                        ),
                        html.Span(
                            "article",
                            className='material-symbols-outlined article',
                            id='article_icon'
                        ),
                    ],
                    id='corpus_input'
                ),

                dcc.Link(
                    html.Button(
                        "Change datasets",
                        id='change_dataset_button'
                    ),
                    href='/'    
                )

            ],
            id="corpus_view"
        ),
        # Summary Stats
        html.Div(
            children=[
                html.Div(
                    children=["Number of Speakers"],
                ),
                html.Div(
                    children=["Number of Utterances"],
                ),
                html.Div(
                    children=["Number of Conversations (Groups)"],
                ),

                html.Div(
                    id='no_of_speakers',
                    className='summary_value'
                ),
                html.Div(
                    id='no_of_utts',
                    className='summary_value'
                ),
                html.Div(
                    id='no_of_convos',
                    className='summary_value'
                ),
            ],
            id="summary_stats"
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
                                            id='page_view_info'
                                        ),
                                        dbc.Tooltip(
                                            "View the page & visualizations according to either the speaker or group dataset",
                                            target="page_view_info",
                                            placement="top"
                                        ),
                                        ],
                                    className="page_view_header",
                                ),

                                html.Div(
                                    children=[
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

                                        dcc.Checklist(
                                            options=[
                                                {'label': 'View corpus metadata', 'value': 'VCM'}
                                            ],
                                            value=[],
                                            id='metadata_check'
                                        ),
                                        html.Span(
                                            "info",
                                            className="material-symbols-outlined info",
                                            id='metadata_info'
                                        ),
                                        dbc.Tooltip(
                                            "View the default metadata features associated with a Corpus. " \
                                            "Prepended with the text 'meta.'.",
                                            target="metadata_info",
                                            placement="top"
                                        ),

                                    ],
                                    className='page_view_selection'
                                ),
                            ],
                            className="page_view"
                        ),    
                        # Box plot
                        html.Div(
                            children=[
                                html.Div(
                                    children=[
                                        "Feature Distributions",
                                        html.Span(
                                            "info",
                                            className="material-symbols-outlined info",
                                            id='box_plot_info'
                                        ),
                                        dbc.Tooltip(
                                            "Select a feature to view its dataset distribution through a box plot",
                                            target="box_plot_info",
                                            placement="top"
                                        ),
                                        ],
                                    className="page_view_header",
                                ),

                                html.Div(
                                    children=[                                
                                    html.Div(
                                        children=[
                                            html.Div("Feature:"),

                                            dcc.Dropdown(
                                                placeholder='Select a feature',
                                                multi=False,
                                                id='box_plot_dropdown',
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

                        dcc.Graph(id="box_plot")

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
                                            'border': '1px solid rgb(180, 180, 180)',
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
                    # Feature Definitions
                    html.Div(
                        children=[
                            html.Div(
                                children=[
                                    "Feature Definitions",
                                    html.Span(
                                        "info",
                                        className="material-symbols-outlined info",
                                        id='definitions_view_info'
                                    ),
                                    dbc.Tooltip(
                                        "View the definitions of the features extracted from your dataset. " \
                                        "Select a category first.",
                                        target="definitions_view_info",
                                        placement="top"
                                    ),
                                ],
                                id='definitions_info_subheader'
                            ),

                            html.Div("Feature Category: "),

                            dcc.Dropdown(
                                placeholder='Select a feature category',
                                value='politeness strategies features',
                                options=["psycholinguistic features", "politeness strategies features", "coordination features"],
                                multi=False,
                                className='definitions_dropdown',
                                id='definitions_category_list',
                                searchable=True
                            ),

                            html.Div(
                                "Category Definition ",
                                className='definitions_subheader',
                                id='definitions_subheader_category'
                            ),

                            html.Div(id='definitions_text_category'),

                            html.Div(
                                children=[
                                    html.Hr(),
                                    
                                    html.Div("Feature: "),

                                    dcc.Dropdown(
                                        placeholder='Select a feature',
                                        options=[],
                                        multi=False,
                                        className='definitions_dropdown',
                                        id='definitions_feature_list',
                                        searchable=True
                                    ),

                                    html.Div(
                                        "Feature Definition ",
                                        className='definitions_subheader',
                                    ),

                                    html.Div(id='definitions_text_feature'),

                                ],
                                id="definitions_feature_section"
                            )
                            
                        ],
                        id='feature_definitions',
                    )

                    ],
                    className='column_b'
                ),
            
            ],  
            className='row'
        )

    ],
    className='overview_page'
    )

# Functions

def get_default(radio_value, time, metadata):
    """
    Returns the default DataFrame if no user corpus was input.

    :param radio_value: The selected radio button value ("group" or "speaker")
    :param time: Whether or not the DataFrame includes time values (True or False)
    :param metadata: Whether or not the DataFrame includes metadata values (True or False)
    :return: Selected DataFrame
    """
    df = pd.DataFrame()

    if radio_value == 'group' and not time and not metadata:
        df = pd.read_csv('default_datasets/default_group.csv', index_col=False)
    elif radio_value == 'speaker' and not time and not metadata: 
        df = pd.read_csv('default_datasets/default_speaker.csv', index_col=False)
    elif radio_value == 'group' and time:
        df = pd.read_csv('default_datasets/default_group_time.csv', index_col=False)
    elif radio_value == 'speaker' and time:
        df = pd.read_csv('default_datasets/default_speaker_time.csv', index_col=False)
    elif radio_value == 'group' and metadata:
        df = pd.read_csv('default_datasets/default_group_meta.csv', index_col=False)
    elif radio_value == 'speaker' and metadata:
        df = pd.read_csv('default_datasets/default_speaker_meta.csv', index_col=False)

    return df


def get_df(jsonified_user_id, radio_value, time, metadata):
    """
    Loads and returns the correct DataFrame according to the input values

    :param jsonified_user_id: The user session ID
    :param radio_value: The selected radio button value ("group" or "speaker")
    :param time: Whether or not the DataFrame includes time values (True or False)
    :param metadata: Whether or not the DataFrame includes metadata values (True or False)
    :return: Selected DataFrame
    """
    df = pd.DataFrame()
    user_id = None

    if jsonified_user_id is not None:
        user_id = json.loads(jsonified_user_id)
    
    if user_id is None: 
        # Default dataset
        df = get_default(radio_value, time, metadata)
    elif radio_value == 'group' and not time and not metadata:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_group_df")))
    elif radio_value == 'speaker' and not time and not metadata: 
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_speaker_df")))
    elif radio_value == 'group' and time:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_group_time_df")))
    elif radio_value == 'speaker' and time:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_speaker_time_df")))
    elif radio_value == 'group' and metadata:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_group_meta_df")))
    elif radio_value == 'speaker' and metadata:
        df = pickle.loads(zlib.decompress(r.get(f"{user_id}_speaker_meta_df")))
    
    return df

# Callbacks

@dash.callback(
    Output(component_id='selected_corpus', component_property='children'),
    Input(component_id='corpus_name', component_property='data')
)
def populate_corpus_view(corpus_name):
    if corpus_name is None:
        # Default dataset
        return 'Group Affect and Performance (GAP) Corpus' 
    else:
        return corpus_name.strip('"')

    
@dash.callback(
    Output(component_id='data_table', component_property='data'),
    Input(component_id='jsonified_user_id', component_property='data'),
    Input(component_id='radio_buttons', component_property='value'),
    Input(component_id='_pages_location', component_property="pathname"),
    Input(component_id='metadata_check', component_property='value')
)
def populate_table(jsonified_user_id, radio_value, pathname, metadata):
    """
    Populates the table component

    :param jsonified_user_id: The user session ID
    :param radio_value: The selected radio value ("group" or "speaker")
    :param pathname: The current page path
    :return: Dictionary of the selected value
    """
    df = pd.DataFrame()

    if pathname == "/timeline": # Return Time DataFrame
        df = get_df(jsonified_user_id, radio_value, True, False)
    elif not metadata: # Return normal DataFrame
        df = get_df(jsonified_user_id, radio_value, False, False)
    else: # Return normal DataFrame + metadata
        df = get_df(jsonified_user_id, radio_value, False, True)

    return df.to_dict('records')
    

@dash.callback(
    Output(component_id='no_of_speakers', component_property='children'),
    Output(component_id='no_of_utts', component_property='children'),
    Output(component_id='no_of_convos', component_property='children'),
    Input(component_id='jsonified_user_id', component_property='data'),
)
def populate_stat_values(jsonified_user_id):
    """
    Populates the statistic values
    :param jsonified_user_id: The user session ID
    :return: Summary statistic values
    """
    speaker_df = pd.DataFrame()
    group_df = pd.DataFrame()
    utt_df = pd.DataFrame()

    if jsonified_user_id is not None:
        user_id = json.loads(jsonified_user_id)

        speaker_df = pickle.loads(zlib.decompress(r.get(f"{user_id}_speaker_df")))
        utt_df = pickle.loads(zlib.decompress(r.get(f"{user_id}_utt_df")))
        group_df = pickle.loads(zlib.decompress(r.get(f"{user_id}_group_df")))
    else: # Default dataset
        speaker_df = pd.read_csv('default_datasets/default_speaker.csv')
        group_df = pd.read_csv('default_datasets/default_group.csv')
        utt_df = pd.read_csv('default_datasets/default_utt.csv')

    return speaker_df['speaker_id'].nunique(), utt_df.index.nunique(), group_df['group_id'].nunique()


@dash.callback(
    Output(component_id='box_plot_dropdown', component_property='options'),
    Output(component_id='box_plot_dropdown', component_property='value'),
    Input(component_id='jsonified_user_id', component_property='data'),
    Input(component_id='radio_buttons', component_property='value'),
    Input(component_id='metadata_check', component_property='value')
)
def populate_box_plot_dropdown(jsonified_user_id, radio_value, metadata):
    """
    Populate the dropdown of feature listings for the box plot

    :param jsonified_user_id: The user session ID
    :param radio_value: The selected radio button value ("group" or "speaker")
    :param metadata: Whether or not the DataFrame includes metadata values (True or False)
    :return: A list of features from the selected DataFrame
    """
    meta_df = get_df(jsonified_user_id, radio_value, False, True)
    meta_df = meta_df.iloc[:, 1:] # Remove ID column
    meta_df = meta_df.convert_dtypes()
    numerical_cols = meta_df.select_dtypes(include=['int', 'float']).columns.tolist() 

    feature_list.extend(numerical_cols)

    return feature_list, 'age of acquisition'


@dash.callback(
    Output(component_id='box_plot', component_property='figure'),
    Input(component_id='radio_buttons', component_property='value'), 
    Input(component_id='box_plot_dropdown', component_property='value'), 
    Input(component_id='jsonified_user_id', component_property='data'),
    Input(component_id='metadata_check', component_property='value')
)
def populate_box_plot(radio_value, selected_feat, jsonified_user_id, metadata):
    """
    Populates the box plot 

    :param radio_value: The selected radio button value ("group" or "speaker")
    :param selected_feat: The selected linguistic feature
    :param jsonified_user_id: The user session ID
    :param metadata: Whether or not the DataFrame includes metadata values (True or False)
    :return: A box plot figure
    """
    if selected_feat is None:
        return px.box()
    
    df = get_df(jsonified_user_id, radio_value, False, False)
    metadata = get_df(jsonified_user_id, radio_value, False, True)
    metadata = metadata.iloc[:, 1:] # Remove the ID column
    metadata = metadata.convert_dtypes()
    
    df = pd.concat([df, metadata], axis=1)
    metadata_list = metadata.columns.tolist()

    if selected_feat not in metadata_list:
        selected_feat = selected_feat.replace(" ", "_")

    box_plot = px.box(df, y=selected_feat, points='all')

    return box_plot


@dash.callback(
    Output(component_id='definitions_feature_list', component_property='options'),
    Output(component_id='definitions_feature_list', component_property='value'),
    Input(component_id='definitions_category_list', component_property='value'),
    Input(component_id='definitions_feature_list', component_property='value'),
)
def populate_definitions_dropdown(category_value, feature_value):
    """
    Populates the definitions dropdown list
    
    :param value: The selected category of linguistic features
    :return: The list of features that fall under the selected category
    """
    # PS features populated by default
    default_options = ['please', 'please start', 'has hedge', 'indirect (btw)', 'hedges', 
                   'factuality', 'deference', 'gratitude', 'apologizing', '1st person plural', 
                   '1st person', '1st person start', '2nd person', '2nd person start', 
                   'indirect (greeting)', 'direct question', 'direct start', 'has positive', 
                   'has negative', 'subjunctive', 'indicative']

    if category_value == 'politeness strategies features' and feature_value is None:
        return default_options, 'please'
    
    options = []
    
    if category_value == 'politeness strategies features':
        options = default_options
    elif category_value == 'coordination features':
        options = ['article', 'auxiliary verb', 'conjunction', 'adverb', 'personal pronoun', 
                   'impersonal pronoun', 'preposition', 'quantifier']
    elif category_value == 'psycholinguistic features':
        options = ['age of acquisition', 'concreteness', 'familiarity', 'imageability']

    return options, feature_value


@dash.callback(
    Output(component_id='definitions_text_category', component_property='children'),
    Input(component_id='definitions_category_list', component_property='value'),
)
def populate_text_category(value):
    """
    Populates the definitions text
    
    :param value: The selected category of linguistic features
    :return: The definition of that linguistic feature category
    """
    text = ''

    if value is None:
        return text

    if value == 'politeness strategies features':
        text = 'A linguistic strategy to measure the rates of conversational politeness ' \
            'or impoliteness, according to certain conversational features. Extracted with the use ' \
            'of the ConvoKit toolkit.'
    elif value == 'coordination features':
        text = 'A linguistic strategy to measure the rates at which a speaker tends to echo the ' \
        'language of another speaker in a conversation. ' \
        'Extracted with the use of the ConvoKit toolkit and averaged across all of each speaker\'s interactions. '
    elif value == 'psycholinguistic features':
        text = 'A linguistic strategy to measure the the interrelation between linguistic factors and ' \
        'psychological aspects. Extracted with the use of the MRC Psycholinguistics Database.'

    return text


@dash.callback(
    Output(component_id='definitions_text_feature', component_property='children'),
    Input(component_id='definitions_feature_list', component_property='value'),
)
def populate_text_feature(value):
    """
    Populates the definitions text
    
    :param value: The selected linguistic feature
    :return: The definition of that linguistic feature
    """
    text = html.Div(children=[])

    if value is None: 
        return text

    # Politeness Strategies
    if value == 'please':
        text.children.append('Utterances that utilize the word please. Example: "Could you ') 
        text.children.append(html.Span('please', className='markers'))
        text.children.append(' say more.."')
    elif value == 'please start':
        text.children.append('Utterances that begin with the word please. Example: "')
        text.children.append(html.Span('Please', className='markers'))
        text.children.append(' do not remove.."')
    elif value == 'has hedge':
        text.children.append('Utterances that utilize hedge words or phrases. ')
        text.children.append('Hedges represent cautious or vague language intended to soften statements or express uncertainty. ')
        text.children.append('Example: "I ')
        text.children.append(html.Span('suggest', className='markers'))
        text.children.append(' we start with.."')
    elif value == 'indirect (btw)':
        text.children.append('Utterances that utilize tentative language to soften requests, criticism, or demands. ')
        text.children.append('Example: "')
        text.children.append(html.Span('By the way', className='markers'))
        text.children.append(', where do you find.."')
    elif value == 'hedges':
        text.children.append('Utterances that utilize hedge words in conjunction with nominal subjects. ')
        text.children.append('Hedges represent cautious or vague language intended to soften statements or express uncertainty. ')
        text.children.append('Example: "I ')
        text.children.append(html.Span('suggest', className='markers'))
        text.children.append(' we start with.."')
    elif value == 'factuality':
        text.children.append('Utterances that utilize statements that refer to truth value, certainty, or directedness. ')
        text.children.append('Example: "')
        text.children.append(html.Span('In fact', className='markers'))
        text.children.append(' you did link.."')
    elif value == 'deference':
        text.children.append('Utterances that utilize phrases that signal social distance or respect. ')
        text.children.append('Example: "')
        text.children.append(html.Span('Nice work', className='markers'))
        text.children.append(' so far.."')
    elif value == 'gratitude':
        text.children.append('Utterances that express gratitude or thankfulness. ')
        text.children.append('Example: "I really ')
        text.children.append(html.Span('appreciate', className='markers'))
        text.children.append(' that you\'ve done them."')
    elif value == 'apologizing':
        text.children.append('Utterances that contain apologies. ')
        text.children.append('Example: "')
        text.children.append(html.Span('Sorry', className='markers'))
        text.children.append(' to bother you.."')
    elif value == '1st person plural':
        text.children.append('Utterances that utilize 1st person plural pronouns. ')
        text.children.append('Example: "Could ')
        text.children.append(html.Span('we', className='markers'))
        text.children.append(' find a less complex.."')
    elif value == '1st person':
        text.children.append('Utterances that utilize 1st person pronouns. ')
        text.children.append('Example: "It is ')
        text.children.append(html.Span('my', className='markers'))
        text.children.append(' view that.."')
    elif value == '1st person start':
        text.children.append('Utterances that start with a 1st person prounoun. ')
        text.children.append('Example: "')
        text.children.append(html.Span('I', className='markers'))
        text.children.append(' have just put the article.."')
    elif value == '2nd person':
        text.children.append('Utterances that utilize 2nd person pronouns. ')
        text.children.append('Example: "But what\'s the source ')
        text.children.append(html.Span('you', className='markers'))
        text.children.append(' have in mind?"')
    elif value == '2nd person start':
        text.children.append('Utterances that start with a 2nd person prounoun. ')
        text.children.append('Example: "')
        text.children.append(html.Span('You\'ve', className='markers'))
        text.children.append(' reverted yourself.."')
    elif value == 'indirect (greeting)':
        text.children.append('Utterances that begin with a greeting. ')
        text.children.append('Example: "')
        text.children.append(html.Span('Hey', className='markers'))
        text.children.append(', how can I.."')
    elif value == 'direct question':
        text.children.append('Utterances that are posed as a question. ')
        text.children.append('Example: "')
        text.children.append(html.Span('What', className='markers'))
        text.children.append(' is your native language?"')
    elif value == 'direct start':
        text.children.append('Utterances that begin with a conjunction. ')
        text.children.append('Example: "')
        text.children.append(html.Span('So', className='markers'))
        text.children.append(' can you retrieve.."')
    elif value == 'has positive':
        text.children.append('Utterances that utilize positive words. ')
        text.children.append('Example: "What an ')
        text.children.append(html.Span('accomplishment', className='markers'))
        text.children.append('".')
    elif value == 'has negative':
        text.children.append('Utterances that utilize negative words. ')
        text.children.append('Example: "That\'s ')
        text.children.append(html.Span('annoying', className='markers'))
        text.children.append('.."')
    elif value == 'subjunctive':
        text.children.append('Utterances that utilize subjunctive phrasing. ')
        text.children.append('Example: "Could ')
        text.children.append(html.Span('you', className='markers'))
        text.children.append(' try.."')
    elif value == 'indicative':
        text.children.append('Utterances that utilize indicative phrasing. ') 
        text.children.append('Example: "Will ')
        text.children.append(html.Span('you', className='markers'))
        text.children.append(' have to.."')

    # Coordination
    if value == 'article':
        text.children.append('Words that appear before nouns to indicate whether the noun is specific or general. ')
        text.children.append('Example: "I saw ')
        text.children.append(html.Span('an', className='markers'))
        text.children.append(' error at.."')
    elif value == 'auxiliary verb':
        text.children.append('A type of verb that, used alongside a main verb, express tense, mood, or voice. ')
        text.children.append('Example: "It ')
        text.children.append(html.Span('was', className='markers'))
        text.children.append(' a bit.."')
    elif value == 'conjunction':
        text.children.append('A word that links other words, phrases, or clauses together. ')
        text.children.append('Example: "We could, ')
        text.children.append(html.Span('but', className='markers'))
        text.children.append(' what if.."')
    elif value == 'adverb':
        text.children.append('A word that modifies a verb, adjective, or another adverb. ')
        text.children.append('Example: "She did it quite ')
        text.children.append(html.Span('quickly', className='markers'))
        text.children.append('.."')
    elif value == 'personal pronoun':
        text.children.append('A word that is used as a simple substitute for the proper name of a person. ')
        text.children.append('Example: ')
        text.children.append(html.Span('"She', className='markers'))
        text.children.append(' thought maybe.."')
    elif value == 'impersonal pronoun':
        text.children.append('A word that does not refer to a specific person, thing, or entity, but is used to ')
        text.children.append('make general statements, express facts, or describe actions. ')
        text.children.append('Example: ')
        text.children.append(html.Span('"It', className='markers'))
        text.children.append(' does seem that way.."')
    elif value == 'preposition':
        text.children.append('Words that describe relationships with other words in a sentence. ')
        text.children.append('Example: "I checked ')
        text.children.append(html.Span('under', className='markers'))
        text.children.append(' there.."')
    elif value == 'quantifier':
        text.children.append('Words used before nouns to indicate the quantity or amount. ')
        text.children.append('Example: "I have ')
        text.children.append(html.Span('some', className='markers'))
        text.children.append(' you can use."')

    # Psycholinguistic
    if value == 'age of acquisition':
        text.children.append('The age at which a word is typically learned. ' \
        'Example (low AoA): "Mom", "dog", "ball" (learned in early childhood). ' \
        'Example (high AoA): "photosynthesis", "democracy" (learned in later life). ')
    elif value == 'concreteness':
        text.children.append('The degree to which a word’s referent can be experienced directly through the senses ' \
        '(seeing, hearing, touching, etc.). ' \
        'Example (low conc): "justice", "truth" (abstract concepts). ' \
        'Example (high conc): "apple", "table".')
    elif value == 'familiarity':
        text.children.append('How common/familiar a word feels to speakers. ' \
        'Example (low fam): "house", "school" (commonly used words). ' \
        'Example (high fam): "diathesis", "pulchritude" (rare/uncommon words). ')
    elif value == 'imageability':
        text.children.append('Measures how easily a word evokes a mental image or sensory experience. ' \
        'Example (low img): "blue", "dog" (easy to picture). ' \
        'Example (high img): "however", "democracy" (abstract concepts). ')
    
    return text
