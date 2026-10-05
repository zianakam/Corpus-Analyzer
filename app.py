from dash import html, dcc, CeleryManager, DiskcacheManager
from celery import Celery

import dash
import dash_bootstrap_components as dbc  
import os

if 'REDIS_URL' in os.environ:
    # For production environment
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    celery_app = Celery(__name__, broker=redis_url, backend=redis_url)

    bcm = CeleryManager(celery_app)
else:
    # For local deployment
    import diskcache
    cache = diskcache.Cache("./cache")
    bcm = DiskcacheManager(cache)


app = dash.Dash(__name__, use_pages=True, 
                    assets_folder='assets', background_callback_manager=bcm, 
                    external_stylesheets=[dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True,
                    )

server = app.server

app.layout = html.Div([

        html.Div(
            children=[
                html.A(
                    children=[
                        html.Div(
                            'Corpus Analyzer', 
                            style={
                                'float': 'left', 
                                'color': 'white', 
                                'marginLeft': '25px',
                                'fontWeight': '350'
                            }
                        )

                    ],
                    href='/'
                ),
                
                html.Div(
                    children=[
                        html.A(
                            html.Div('About', style={'fontSize': '13px'}),
                            href='/'
                        ),
        
                        html.A(
                            html.Div('Preview with a Sample Dataset', style={'fontSize': '13px'}),
                            href='/overview?corpus_id=sample'
                        ),
        
                        html.A(
                            html.Img(
                                src='assets/images/GitHub_Invertocat_White_Clearspace.svg',
                                style={
                                    'width': '20px',
                                    'marginRight': '50px',
                                    'marginTop': '-6px'
                                }
                            ),
                            href='https://github.com/zianakam/Corpus-Analyzer'
                        ),    
                    ],
                    className='header_nav'
                ),
                
                html.Hr(
                    style={
                        "border": "1px solid rgba(116, 150, 175, 0.35)",
                        "borderTop": "1px solid #333",
                    }
                ),
            ],
            id='nav'
        ),
 
        dcc.Store(id='jsonified_user_id', storage_type='session'), # saved until cleared/browser closed
        dcc.Store(id='corpus_name', storage_type='session'),

        dash.page_container,

        dcc.Location(id='url', refresh='callback-nav'),
    ])


if __name__ == '__main__':    
    app.run(debug=True, use_reloader=True)  
    # use_reloader=False