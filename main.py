import pandas as pd
import ast
from tqdm import tqdm
import sqlite3
from pathlib import Path
import os
from plotly import graph_objects as go
from plotly.graph_objs import *

from pathlib import Path
import sys
import os
from collections import namedtuple
from multiprocessing import freeze_support
import traceback
import plotly.express as px

import pkg_resources

IS_FROZEN = hasattr(sys, '_MEIPASS')
_true_get_distribution = pkg_resources.get_distribution
_Dist = namedtuple('_Dist', ['version'])


def _get_distribution(dist):
    if IS_FROZEN and dist == 'flask-compress':
        return _Dist('1.5.0')
    else:
        return _true_get_distribution(dist)


pkg_resources.get_distribution = _get_distribution
import dash
import dash_table
import dash_html_components as html
from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import numpy as np
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, suppress_callback_exceptions=True, prevent_initial_callbacks=True,
                external_stylesheets=[dbc.themes.MATERIA], assets_url_path='configurations/assets')
input_files = Path('./input')

button_styles = {'background-color': 'hsl(120,50%,55%)',
                 'border-radius': '5px',
                 'color': '#fff',
                 'border-color': 'hsl(120,50%,55%)'
                 }

inline_style = {
    'display': 'inline-block'}
products = ['7D9A98C6E8BF033613B74252D9D24B33',
            '9EC302050B63C90533F9FFBCAC489DD8',
            'AC688D3B8E8D812E2B49496BE59286E3',
            '0F49D92CEA8C80166B0605ED3D1A8E5D',
            '6050B6B1F05ABDB4B33DA4BCEB46DE9B',
            '5D199BE9EFD733A097DF8E08C9B85924'

            ]

month_dict = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: 'July', 8: 'August',
              9: 'September', 10: 'October', 11: 'November', 12: 'December'}

reco_promo = 'Рекомендуем  заказать продвижение места в поиске за Х рублей (ссылка на заказ)'
reco_guideline = 'Рекомендуем поработать с описанием и контентом (ссылка на страницу с гайдлайнами)'

df_total = pd.read_csv(f'{input_files}/df_short.csv')
df = pd.read_csv(f'{input_files}/df_seller.csv')
for_funnel = df.groupby(['city_name', 'ecom_event_action', 'ecom_id', 'month']).agg(
    {'user_id': 'nunique'}).reset_index()
fig_city = go.Figure()
for city in for_funnel['city_name'].unique():
    values_city = for_funnel[for_funnel.city_name == city].groupby('ecom_event_action').agg(
        {'user_id': 'sum'}).reset_index().sort_values('user_id', ascending=False)
    fig_city.add_trace(go.Funnel(
        name=city,
        y=values_city['ecom_event_action'],
        x=values_city['user_id'],
        textinfo="value+percent initial"))
fig_product = go.Figure()
for product in products:
    values_product = for_funnel[for_funnel.ecom_id == product].groupby('ecom_event_action').agg(
        {'user_id': 'sum'}).reset_index().sort_values('user_id', ascending=False)
    fig_product.add_trace(go.Funnel(
        name=product,
        y=values_product['ecom_event_action'],
        x=values_product['user_id'],
        textinfo="value+percent initial"),
    )

fig_month = go.Figure()
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
                options=get_labels(products),
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
def start_check(submit, prod_list):
    if not submit:
        return []
    alerts = list()
    for prod in products:
        # view_item
        product_cluster = df_total[df_total.ecom_id == prod]['cluster'].unique().min()
        df_1 = df_total[(df_total.cluster == product_cluster) & (df_total.ecom_id != prod)]
        df1_gr = df_1.groupby(['ecom_event_action', 'ecom_id']).agg({'user_id': 'nunique'}).reset_index().sort_values(
            'user_id', ascending=False)
        df1_gr = df1_gr[df1_gr['ecom_event_action'] == 'view_item']
        upper_bownd = np.quantile(np.array(df1_gr['user_id']), 0.95, axis=None, out=None, overwrite_input=False,
                                  interpolation='linear', keepdims=False)
        lower_bownd = np.quantile(np.array(df1_gr['user_id']), 0.05, axis=None, out=None, overwrite_input=False,
                                  interpolation='linear', keepdims=False)
        mean_m = df1_gr[(df1_gr.user_id > lower_bownd) & (df1_gr.user_id < upper_bownd)]['user_id'].mean()
        seller_prod_view = df[(df.ecom_id == prod) & (df.ecom_event_action == 'view_item')][
            'user_id'].nunique()
        if abs(seller_prod_view - mean_m) / mean_m > 0.2 and abs(seller_prod_view - mean_m) / mean_m < 1:
            alert = (
                f'Ваш товар {prod} покупатель просматривает на {round(abs(seller_prod_view - mean_m) / mean_m * 100)}% реже чем у Ваших конкурентов')
            alerts.append({'Алерт': alert,
                           'Рекомендация': reco_promo})

        seller_prod_view_by_month_1 = \
            df[(df.ecom_id == prod) & (df.ecom_event_action == 'view_item') & (df.month == 9)][
                'user_id'].nunique()
        seller_prod_view_by_month_2 = \
            df[(df.ecom_id == prod) & (df.ecom_event_action == 'view_item') & (df.month == 10)][
                'user_id'].nunique()
        if seller_prod_view_by_month_2 < seller_prod_view_by_month_1:
            alert_month = f'Просмотры вашего товара {prod} в октябре сократились на {(seller_prod_view_by_month_2 - seller_prod_view_by_month_2) / seller_prod_view_by_month_2 * 100}% по сравнению с сентябрем'
            alerts.append({'Алерт': alert_month,
                           'Рекомендация': reco_promo})

        # add_to_cart

        prod_funnel = df[df['ecom_id'] == prod].groupby('ecom_event_action').agg({'user_id': 'nunique'}).sort_values(
            'user_id', ascending=False).reset_index()
        conversion_prod = prod_funnel['user_id'][1] / prod_funnel['user_id'][0]
        df1_gr = df_1.groupby(['ecom_event_action']).agg({'user_id': 'nunique'}).reset_index().sort_values(
            'user_id', ascending=False)
        conversion_total = df1_gr['user_id'][1] / df1_gr['user_id'][0]
        if conversion_prod < conversion_total:
            alert_conv_cart = f'Конверсия из просмотров в добавление в корзину - у Вашего товара {prod} меньше на {round(abs(conversion_prod - conversion_total) / conversion_total * 100)}% чем у конкурентов'
            alerts.append({'Алерт': alert_conv_cart,
                           'Рекомендация': reco_guideline})
        prod_funnel_m = df[df['ecom_id'] == prod].groupby('ecom_event_action').agg({'user_id': 'nunique'}).sort_values(
            'user_id', ascending=False).reset_index()
    final_output = html.Div([
        dash_table.DataTable(
            id='date_table',
            columns=[{"name": i, "id": i} for i in pd.DataFrame(alerts).columns],
            data=pd.DataFrame(alerts).to_dict(orient='records')
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
