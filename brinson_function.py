# -*- coding: utf8 -*-
# author: Xu Huanrong

import seaborn as sns
from WindPy import w
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xlrd

plt.rcParams['font.sans-serif'] = ['SimHei']  # display Chinese Character
plt.rcParams['axes.unicode_minus'] = False  # display positive/negative mathematical symbols

    
def std_bench(dFrame, str_date):
    """processing daily bench_df"""
    dFrame['stock_weight'] = dFrame['stock_weight'] * 0.5 / 100
    dFrame['stock_yield'] = dFrame['stock_yield'] / 100
    new_rows = [str_date, 'Cash','现金', 0.5, "现金", 0.00] # cash weights 50% in benchmark
    dFrame.loc[dFrame.shape[0]] = new_rows
    return dFrame
    
def std_fund(dFrame, str_date):
    """processing daily fund_df"""
    dFrame['stock_weight'] = dFrame['stock_weight'] / 100
    dFrame['stock_yield'] = dFrame['stock_yield'] / 100
    cash_weight = 1 - dFrame.stock_weight.sum()
    new_rows = [str_date, 'Cash','现金', cash_weight, "现金", 0.00] # cash weights 50% in benchmark
    dFrame.loc[dFrame.shape[0]] = new_rows
    return dFrame
    
def process_df(dframe):    
    "Return fund weight and yield."
    dframe['yield'] = dframe['stock_weight'] * dframe['stock_yield']
    weight_df = dframe.groupby('stock_industry')['stock_weight'].sum()
    yield_df = dframe.groupby('stock_industry')['yield'].sum()
    weight_df = weight_df.to_frame()
    weight_df.columns = ['weight']
    yield_df = yield_df.to_frame()
    weight_df['industry'] = weight_df.index
    yield_df['industry'] = weight_df.index
    weight_df = weight_df.reset_index(drop=True)
    yield_df = yield_df.reset_index(drop=True)
    yield_df['yield'] = yield_df['yield'] / weight_df['weight']
    return weight_df, yield_df

    
def to_all_key(df_1, df_2, key):
    "change industry numbers of fund as benchmark's "

    df = df_1.copy()
    df.loc[:, key] = np.array([0.0] * len(df.industry))
    new_df = df_2.append(df, ignore_index=True)
    new_df = new_df.drop_duplicates(subset='industry')
    return new_df
    
def re_index(df):
    "Reindex the df passed"
    df = df.sort_values(by=['industry'])
    df = df.set_index(['industry'])
    return df

    
def brinson_analysis(fund_weight_df, fund_yield_df, bench_weight_df, bench_yield_df, str_date):
    "Produce three elements of brinson."
    
    bench_weight_df = re_index(bench_weight_df)
    bench_yield_df = re_index(bench_yield_df)
    fund_weight_df = re_index(fund_weight_df)
    fund_yield_df = re_index(fund_yield_df)
        
        
    allocation_result =  (fund_weight_df['weight'] - bench_weight_df['weight']) * bench_yield_df['yield']
    allocation_df =  allocation_result.to_frame(name='result') + 1
    
    selection_result = (fund_yield_df['yield'] - bench_yield_df['yield']) * bench_weight_df['weight']
    selection_df = selection_result.to_frame(name='result') + 1

    interaction_result = (fund_weight_df['weight'] - bench_weight_df['weight']) * (fund_yield_df['yield'] - bench_yield_df['yield'])
    interaction_df = interaction_result.to_frame(name='result') + 1
    
    return allocation_df, selection_df, interaction_df

def get_results(allocation_df, selection_df, interaction_df, fund_nav_df, bench_price_df, str_date):
    "Produce result and graph."
    
    industry_allocation = (allocation_df - 1).sum()[0]
    stock_selection = (selection_df - 1).sum()[0]
    interaction = (interaction_df - 1).sum()[0]
    
    fund_yield = float(fund_nav_df[fund_nav_df.date == str_date]['fund_yield'])
    bench_yield = float(bench_price_df[bench_price_df.date == str_date]['bench_yield'])
    residual = fund_yield - industry_allocation - stock_selection - interaction - bench_yield

    result_division = [str_date, fund_yield, industry_allocation, stock_selection, interaction, residual ,bench_yield]
    
    return result_division
    
    
if __name__ == '__main__':
    
    str_date = "2017-12-01"
    bench_df_1 = bench_df[bench_df['date'] == str_date]
    fund_df_1 = fund_df[fund_df['date'] == str_date]
    std_bench_df_1 = std_bench(bench_df_1, str_date)
    std_fund_df_1 = std_fund(fund_df_1, str_date)
    bench_weight_df, bench_yield_df = process_df(std_bench_df_1)
    fund_weight_df, fund_yield_df = process_df(std_fund_df_1)
    fund_weight_df = to_all_key(bench_weight_df, fund_weight_df, 'weight')
    fund_yield_df = to_all_key(bench_yield_df, fund_yield_df, 'yield')
    allocation_df, selection_df, interaction_df = brinson_analysis(fund_weight_df, fund_yield_df, bench_weight_df, bench_yield_df, str_date)
    result_division = get_results(allocation_df, selection_df, interaction_df, fund_nav_df, bench_price_df, str_date) 
    print(result_division)