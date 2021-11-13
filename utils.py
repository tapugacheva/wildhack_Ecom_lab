import pandas as pd
import numpy as np
from texts_n_dicts import *


def get_alerts(products, df_total, df):
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
        prod_funnel_m_1 = df[(df['ecom_id'] == prod) & (df['month'] == 9)].groupby('ecom_event_action').agg(
            {'user_id': 'nunique'}).sort_values(
            'user_id', ascending=False).reset_index()
        conv_9 = prod_funnel_m_1['user_id'][1] / prod_funnel_m_1['user_id'][0]
        prod_funnel_m_2 = df[(df['ecom_id'] == prod) & (df['month'] == 10)].groupby('ecom_event_action').agg(
            {'user_id': 'nunique'}).sort_values(
            'user_id', ascending=False).reset_index()
        conv_10 = prod_funnel_m_2['user_id'][1] / prod_funnel_m_2['user_id'][0]
        if conv_9 > conv_10:
            alert_cart_m = f'Конверсия из просмотров в добавление в корзину - у Вашего товара {prod} сократилась в октябре по сравнению с сентябрем на {round(abs(conv_9 - conv_10) / conv_10 * 100)}%'
            alerts.append({'Алерт': alert_cart_m,
                           'Рекомендация': reco_guideline})

        # purchase
        convertion_purchase = prod_funnel['user_id'][2] / prod_funnel['user_id'][1]
        conversion_total = df1_gr['user_id'][2] / df1_gr['user_id'][3]
        if convertion_purchase < conversion_total:
            alert_purchase = f'Конверсия из добавления в корзину в покупку - у Вашего товара- {prod} ниже чем у конкурентов на {round(abs(convertion_purchase - conversion_total) / conversion_total * 100)}%'
            alerts.append({'Алерт': alert_purchase,
                           'Рекомендация': reco_act})
        conv_9 = prod_funnel_m_1['user_id'][2] / prod_funnel_m_1['user_id'][1]
        conv_10 = prod_funnel_m_2['user_id'][2] / prod_funnel_m_2['user_id'][1]
        if conv_9 > conv_10:
            alert_cart_m = f'Конверсия из добавления в корзину в покупку - у Вашего товара {prod} сократилась в октябре по сравнению с сентябрем на {round(abs(conv_9 - conv_10) / conv_10 * 100)}%'
            alerts.append({'Алерт': alert_cart_m,
                           'Рекомендация': reco_act})
        return alerts
