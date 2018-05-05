# -*- coding: utf8 -*-
# author: Xu Huanrong
# run one time

from WindPy import w
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime

w.start()

date_start = "2017-09-01"
date_end = "2017-12-31"

def trade_days(date_start, date_end):
    """制作正确日期"""
    trade_days = w.tdays(date_start, date_end)
    trade_days_list = []
    
    for day in trade_days.Data[0]:
        strday = datetime.datetime.strftime(day,'%Y-%m-%d')
        #print(strday)
        trade_days_list.append([strday])
    
    return trade_days_list
        
    
def trade_days_df(trade_days_list, bench_df):
    """save trade_days_lists as csv_file"""
    trade_days_lists = trade_days_list * 300
    #print(len(trade_days_lists))

    trade_days_df = pd.DataFrame(trade_days_lists, columns=['date'])
    trade_days_df = trade_days_df.sort_values(by='date')
    trade_days_df.index = bench_df.index
    trade_days_df.to_csv('data_produce/trade_days.csv')
    
    return trade_days_df
    
    
def bench_df(trade_days_list):
    #筛选出沪深300每个交易日的成分股的代码、名字和权重，已保存csv防止wind quota exceed
    #存在一个bug，wind数据中指数调整没有及时体现，函数取得值跟实际不符
    bench_df = pd.DataFrame(columns= ['date','stock_code', 'stock_name','stock_weight'])
    for day in trade_days_list:
        strday = day[0]
        bench_data = w.wset("indexconstituent","date="+ strday , "windcode=000300.SH")
        temps_df = pd.DataFrame(bench_data.Data).T
        temps_df.columns = ['date','stock_code', 'stock_name','stock_weight']
        bench_df = pd.concat([bench_df, temps_df])

    # 将日期格式转化为文本
    bench_df['date'] = bench_df['date'].map(lambda x: datetime.datetime.strftime(x,'%Y-%m-%d'))
    
    #取每个股票的行业信息
    bench_stocks = bench_df['stock_code'].drop_duplicates()
    stocks_list = list(bench_stocks)
    #print(len(stocks_list))
    stocks_code = ','.join(stocks_list)
    data = w.wss(stocks_code,  "industry_sw","tradeDate=20170901;cycle=D;industryType=1")
    stock_industry = pd.DataFrame([data.Codes, data.Data[0]]).T
    stock_industry.columns = ['stock_code', 'stock_industry']
    bench_df = pd.merge(bench_df, stock_industry, on='stock_code')
    
    # 取出沪深300成分股每天的涨跌幅
    bench_yield_df = pd.DataFrame(columns= ['date','stock_code','stock_yield'])    

    for stock in stocks_list:
        bench_data = w.wsd(stock, "pct_chg,windcode", "2017-09-01", "2017-12-31", "")
        temps_df = pd.DataFrame([bench_data.Times, bench_data.Data[0], bench_data.Data[1]]).T
        temps_df.columns = ['date','stock_yield','stock_code']
        bench_yield_df = pd.concat([bench_yield_df, temps_df])
    
    bench_yield_df['date'] = bench_yield_df['date'].map(lambda x: datetime.datetime.strftime(x,'%Y-%m-%d'))
    bench_yield_df.to_csv('data_produce/yield.csv')
    bench_df = pd.merge(bench_df, bench_yield_df, on=['date','stock_code'])
    bench_df = bench_df.sort_values(by=['date', 'stock_code'])
    
    return bench_df


if __name__ == '__main__':
    trade_days_list = trade_days(date_start, date_end)
    bench_df = bench_df(trade_days_list)
    trade_days_df = trade_days_df(trade_days_list, bench_df)
    #bench_df['date'] = trade_days_df['date']
    bench_df.to_csv('data_produce/hs300_info.csv')#注意保存后以utf-8编码保存