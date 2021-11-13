from plotly import graph_objects as go
from plotly.graph_objs import *

from pathlib import Path
import sys

from collections import namedtuple
from multiprocessing import freeze_support

import pkg_resources

import dash
import dash_table
import dash_html_components as html
from dash.dependencies import Output, Input
import dash_core_components as dcc


import dash_bootstrap_components as dbc
from utils import *

IS_FROZEN = hasattr(sys, '_MEIPASS')
_true_get_distribution = pkg_resources.get_distribution
_Dist = namedtuple('_Dist', ['version'])


def _get_distribution(dist):
    if IS_FROZEN and dist == 'flask-compress':
        return _Dist('1.5.0')
    else:
        return _true_get_distribution(dist)


pkg_resources.get_distribution = _get_distribution


app = dash.Dash(__name__, suppress_callback_exceptions=True, prevent_initial_callbacks=True,
                external_stylesheets=[dbc.themes.LUX], assets_url_path='configurations/assets')
input_files = Path('./input')

df_total = pd.read_csv(f'{input_files}/df_short.csv')
df = pd.read_csv(f'{input_files}/df_seller.csv')
for_funnel = df.groupby(['city_name', 'ecom_event_action', 'ecom_id', 'month']).agg(
    {'user_id': 'nunique'}).reset_index()

layout = Layout(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)
fig_city = go.Figure(layout=layout)
for city in for_funnel['city_name'].unique():
    values_city = for_funnel[for_funnel.city_name == city].groupby('ecom_event_action').agg(
        {'user_id': 'sum'}).reset_index().sort_values('user_id', ascending=False)
    fig_city.add_trace(go.Funnel(
        name=city,
        y=values_city['ecom_event_action'],
        x=values_city['user_id'],
        textinfo="value+percent initial"))
fig_product = go.Figure(layout=layout)
for product in products_seller:
    values_product = for_funnel[for_funnel.ecom_id == product].groupby('ecom_event_action').agg(
        {'user_id': 'sum'}).reset_index().sort_values('user_id', ascending=False)
    fig_product.add_trace(go.Funnel(
        name=product,
        y=values_product['ecom_event_action'],
        x=values_product['user_id'],
        textinfo="value+percent initial"),
    )

fig_month = go.Figure(layout=layout)
for month in for_funnel['month'].unique():
    values_month = for_funnel[for_funnel.month == month].groupby('ecom_event_action').agg(
        {'user_id': 'sum'}).reset_index().sort_values('user_id', ascending=False)
    fig_month.add_trace(go.Funnel(
        name=month_dict[month],
        y=values_month['ecom_event_action'],
        x=values_month['user_id'],
        textinfo="value+percent initial"),
    )


def get_labels(products_list):
    labels = list()
    for i in range(len(products_list)):
        label = {'label': f'Продукт_{i}', 'value': products_list[i]}
        labels.append(label)
    return labels


def get_app_layout():
    return html.Div([
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.H1('SAM SEBE ANALYST'),
        html.H4('Ecom_lab'),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div([
            html.H3('Воронка по городам'),
            dcc.Graph(figure=fig_city),

            html.H3('Воронка по продуктам'),
            dcc.Graph(figure=fig_product),

            html.H3('Воронка по месяцам'),
            dcc.Graph(figure=fig_month)
        ],
        ),
        html.Div([
            html.H5('Выберете товары'),
            dcc.Dropdown(
                id='products',
                options=get_labels(products_seller),
                multi=True
            )
        ]),
        html.Div([
            html.Div([
                dcc.ConfirmDialogProvider(
                    children=html.Button(
                        'Начать проверку',
                        style=button_styles
                    ),
                    id='start_check_input',
                    message='Начинаем?'
                )
            ]),
            html.Div(id='start_check_output'),
            html.Br(),
            dcc.Loading(children=html.Div(id='total_check_output'),
                        loading_state={'data-dash-is-loading': True},
                        fullscreen=True,
                        type='cube', color='darkslateblue')
        ])

    ],
        style={
            'textAlign': 'center'},
    )


@app.callback(Output('total_check_output', 'children'),
              Input('start_check_input', 'submit_n_clicks'),
              Input('products', 'value')

              )
def start_check(submit, products_list):
    if not submit:
        return []
    alerts = get_alerts(products_list, df_total, df)

    final_output = html.Div([
        dash_table.DataTable(
            id='date_table',
            columns=[{"name": i, "id": i} for i in pd.DataFrame(alerts).columns],
            data=pd.DataFrame(alerts).to_dict(orient='records'),
            style_cell={

                'font_size': '20px'
            },
        ),
        html.Br(),
        html.Br(),
        html.Br()

    ])
    return final_output


app.layout = get_app_layout

if __name__ == '__main__':
    freeze_support()
    app.run_server(port=5119, debug=False)
