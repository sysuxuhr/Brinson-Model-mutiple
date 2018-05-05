# -*- coding: utf8 -*-
# author: Xu Huanrong

import seaborn as sns
from WindPy import w
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from brinson_function import *

plt.rcParams['font.sans-serif'] = ['SimHei']  # display Chinese Character
plt.rcParams['axes.unicode_minus'] = False  # display positive/negative mathematical symbols

def processing(str_date, bench_df, fund_df):
    "processing daily data"
    bench_df_1 = bench_df[bench_df['date'] == str_date]
    fund_df_1 = fund_df[fund_df['date'] == str_date]
    std_bench_df_1 = std_bench(bench_df_1, str_date)
    std_fund_df_1 = std_fund(fund_df_1, str_date) 
    bench_weight_df, bench_yield_df =  process_df(std_bench_df_1)
    fund_weight_df, fund_yield_df =  process_df(std_fund_df_1)
    fund_weight_df = to_all_key(bench_weight_df, fund_weight_df, 'weight')
    fund_yield_df = to_all_key(bench_yield_df, fund_yield_df, 'yield')
    
    return fund_weight_df, fund_yield_df, bench_weight_df, bench_yield_df


def draw_graph(result1, result2, result3):
    sns.set_color_codes("muted")
    result_set = [[result1 - 1, 'allocation', '行业配置收益'], 
                  [result2 - 1, 'selection', '个股选择收益'],
                  [result3 - 1, 'interaction', '综合收益']]
    # drawing
    for result in result_set:
        pd_df = result[0].sort_values("result", ascending=False)
        plt.figure(figsize=(10, 8))
        ax = sns.barplot(pd_df.result, pd_df.index, color="b")
        ax.set(xlabel=result[1], ylabel="industry")
        ax.get_xaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(round(x, 6))))
        ax.set_yticklabels(pd_df.index)
        ax.set(ylabel="", xlabel=result[2])
        plt.tight_layout()
        plt.savefig("brinson_model_" + result[1] + ".png", dpi=120)

if __name__== '__main__':
    # 读取基准数据
    bench_df = pd.read_csv('hs300_info.csv', index_col=0, encoding='utf-8')

    # 读取基准日收益数据并进行处理, 万得下载基准收盘价
    bench_price_df = pd.read_excel('raw_data/沪深300收盘.xlsx')    
    bench_price_df.columns = ['date', 'price']
    bench_price_df['bench_yield'] = (bench_price_df.price / bench_price_df.shift(1).price -1) * 0.5
    bench_price_df = bench_price_df.dropna()

    # 取基金持仓数据, 股票行业数据需手工加工excel
    raw_data = pd.read_excel('raw_data/XX.xlsx')
    fund_df = pd.DataFrame([raw_data.FDATE, raw_data.CODE, raw_data.FKMMC, raw_data.FSZ_JZ_BL, raw_data.IND_SW, raw_data.pct]).T
    fund_df.columns = ['date', 'stock_code', 'stock_name', 'stock_weight', 'stock_industry', 'stock_yield']

    # 取基金净值数据
    fund_nav_df = pd.read_excel('raw_data/XX净值.xlsx')
    fund_nav_df.columns = ['date', 'nav']
    fund_nav_df['fund_yield'] = fund_nav_df.nav / fund_nav_df.shift(1).nav - 1
    fund_nav_df = fund_nav_df.dropna()
    fund_nav_df.head()

    # 将日期格式统一
    fund_nav_df['date'] = fund_nav_df['date'].map(lambda x: datetime.datetime.strptime(str(int(x)),'%Y%m%d'))
    fund_df['date'] = fund_df['date'].map(lambda x: datetime.datetime.strptime(x,'%Y/%m/%d'))
    fund_df['date'] = fund_df['date'].map(lambda x: datetime.datetime.strftime(x,'%Y-%m-%d'))
    fund_nav_df['date'] = fund_nav_df['date'].map(lambda x: datetime.datetime.strftime(x,'%Y-%m-%d'))
    bench_price_df['date'] = bench_price_df['date'].map(lambda x: datetime.datetime.strftime(x,'%Y-%m-%d'))

    # 制作交易日期序列    
    trade_days = w.tdays("2017-11-27","2017-12-31")
    trade_days_list = []
    for day in trade_days.Data[0]:
        strday = datetime.datetime.strftime(day,'%Y-%m-%d')
        #print(strday)
        trade_days_list.append(strday)

    # 处理数据    
    result_division = []

    for str_date in trade_days_list:
        if str_date == '2017-11-27':
            fund_weight_df, fund_yield_df, bench_weight_df, bench_yield_df = processing(str_date, bench_df, fund_df)
            allocation_df, selection_df, interaction_df = brinson_analysis(fund_weight_df, fund_yield_df, bench_weight_df, bench_yield_df, str_date)
            day_result = get_results(allocation_df, selection_df, interaction_df, fund_nav_df, bench_price_df, str_date)
            print(str_date, day_result)
            result_division.append(day_result)
        else:
            fund_weight_df, fund_yield_df, bench_weight_df, bench_yield_df = processing(str_date, bench_df, fund_df)
            temp_df1, temp_df2, temp_df3 = brinson_analysis(fund_weight_df, fund_yield_df, bench_weight_df, bench_yield_df, str_date)
            allocation_df.result = allocation_df.result * temp_df1.result
            selection_df.result = selection_df.result * temp_df2.result
            interaction_df.result = interaction_df.result * temp_df3.result
            day_result = get_results(temp_df1, temp_df2, temp_df3, fund_nav_df, bench_price_df, str_date)
            #print(str_date, day_result)
            result_division.append(day_result)

    # 绘制各个影响因子明细结果        
    draw_graph(allocation_df, selection_df, interaction_df)

    # 汇总结果
    result_df = pd.DataFrame(result_division)
    result_df.columns = ['date', 'fund_yield', 'industry_allocation', 'stock_selection', 'interaction', 'residual' ,'bench_yield']
    result_df = result_df.set_index('date') + 1
    summary_result = [result_df.bench_yield.prod() - 1,
                      result_df.industry_allocation.prod() - 1,
                      result_df.stock_selection.prod() - 1,
                      result_df.interaction.prod() - 1,
                      result_df.residual.prod() - 1]    
    fund_yield =  result_df.fund_yield.prod() - 1

    # 绘制瀑布图的准备
    index = ['bench_yield', 'industry_allocation', 'stock_selection', 'interaction', 'residual']
    summary_df = pd.DataFrame(summary_result, index=index, columns=['result'])
    blank = summary_df.result.cumsum().shift(1).fillna(0)
    summary_df.loc['fund_yield'] =fund_yield
    blank.loc['fund_yield'] = fund_yield

    step = blank.reset_index(drop=True).repeat(3).shift(-1)
    step[1::3] = np.nan
    blank.loc['fund_yield'] = 0

    # 获取颜色序列
    data = list(summary_df.result)
    colors = ''
    for point in data:
        if point < 0:
            colors += 'g'
        else:
            colors += 'r'
            
    y_position = [0.0]
    data2 = list(blank)
    
    # 获取图形文本位置参数
    for i in range(1, len(data2)):
        if data[i] > 0:
            y_position.append(data2[i] + data[i])
        else:
            y_position.append(data2[i])
    
    # 开始绘制        
    my_plot = summary_df.plot(kind='bar', stacked=True, bottom=blank,legend=None, title="Brinson Result", rot=45, alpha=0.9, colors=colors)

    b_v = [0, 0, 0, 0, 0, 0, 0]
    ind = [0, 1, 2, 3, 4, 5]
    for a,b,c in zip(ind, y_position ,summary_df.result):
        if c < 0:
            my_plot.annotate(str(round(c * 100, 2)) + '%', xy=(a, b), horizontalalignment='center', verticalalignment='down', color='g')
        else:
            my_plot.annotate(str(round(c * 100, 2)) + '%', xy=(a, b), horizontalalignment='center', verticalalignment='down', color='r')
    my_plot.plot(step.index, step.values,'k')
    plt.savefig('Brinson_result.png', dpi=120)

        
