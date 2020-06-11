#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import japanize_matplotlib
import openpyxl
import re
from pathlib import Path
import os
import locale
locale.setlocale(locale.LC_CTYPE, "Japanese_Japan.932")

class SurfaceData:
    def __init__(self,site_name):
        self.site_name=site_name
        self.dir_path = os.path.dirname(os.path.abspath(__file__))
        self.df = pd.read_excel(os.path.join(self.dir_path,self.site_name + ".xlsx") )

    # 新たなDFのヘッダーを作成。
    def setNewHeader(self):
        # 「poc_25」や「p_po4_5」の末尾数字をre.sub()と正規表現で削除。
        # dict.fromkeys()で順場保持したまま、末尾数字削除後の重複要素を削除。
        header = list(self.df.columns)
        header = [re.sub(r'(.*)_[0-9]{,2}',r'\1',col) for col in header]
        self.new_header = list(dict.fromkeys(header))

    # 表層ブロック番号のユニークリストをセット。これをsetSurceData()で使用。
    def setUniSurfaceBlock(self):
        self.sur_unilist= list(self.df['surface_block'].unique())
    
    # 表層データをデータフレームにセット 
    def setSurfaceData(self):
        # 空のnumpy2次元配列用意
        # 表層ブロック番号でDF絞り込み　→　表層ブロック含むカラム名をbooleanで抽出　→　numpy配列に追加
        # numpy配列をデータフレームにする。
        append_arry = np.empty([0,len(self.new_header)])
        for sur_number in self.sur_unilist:
            temp_df = self.df[self.df['surface_block']==sur_number]
            column_bool = temp_df.columns.str.endswith(str(sur_number))
            column_bool[0:2]=True#１、２列目は手動でTrueにして残す（dateと表層ブロック番号）。
            temp_df = temp_df.loc[:,column_bool]
            append_arry = np.concatenate([append_arry,temp_df.values])
        self.df_new = pd.DataFrame(data=append_arry,columns = self.new_header)
        self.df_new.set_index('date',inplace=True)
        self.df_new['chla'] = self.df_new['chla01']+self.df_new['chla02']+self.df_new['chla03']
        self.df_new = self.df_new.sort_index()
        self.df_new = self.df_new.astype('float16')

    # 表層日平均データをデータフレームにセット
    def setDailyData(self):
        self.df_new_daily = self.df_new.resample('D').mean()

    # 縦長データフレームをセット。表層より上の不要な行削除。日付で抽出可能なようにインデックス設定。
    def setLongData(self):
        self.long_df = pd.wide_to_long(self.df,stubnames=self.new_header[2:],i='date',j='block',sep='_')
        self.long_df.sort_index(level=0,inplace=True)# これを挟まないと日付抽出できない
        self.long_df = self.long_df.reset_index(level='block')#「ブロック」はインデックス解除
        self.long_df = self.long_df[self.long_df['block']<=self.long_df['surface_block']]#表層ブロックより上のブロックのデータは削除
        self.long_df['chla']= self.long_df['chla01']+self.long_df['chla02']+self.long_df['chla03']

# %%
# インスタンス作成し、リストとする。ここで地点名.xlsxを読み込み。
site_file_list = ["siteA_","siteB_","siteC_","siteD_"]#,"siteE_","siteF_"
cal_obj_list = []

for idx, site_file in enumerate(site_file_list):
    cal_obj_list.append(SurfaceData(site_file))
    cal_obj_list[idx].setNewHeader()
    cal_obj_list[idx].setUniSurfaceBlock()
    cal_obj_list[idx].setSurfaceData()
    cal_obj_list[idx].setLongData()

# %%
from datetime import time
from datetime import datetime
from datetime import timedelta


# グラフを描きたい期間のリスト作成
# グラフが大きくなりすぎるのでとりあえず1週間
date_list = [datetime(2019,8,1,12)]
count_day = 0
while count_day < 8:
    date_list.append(date_list[-1]+timedelta(days=1))
    count_day += 1

# インスタンス変数long_dfを日付リストで抽出し、置換。
for idx, obj in enumerate(cal_obj_list):
    obj.long_df = obj.long_df[obj.long_df.index.isin(date_list)]


# %%
# 描きたい項目
cal_items = ['tt','dox','chla','cod','no3','nh4','po4']

# 出力したい日数（行）×出力したい項目（列数）
rows_graph = len(date_list)
columns_graph = len(cal_items)

# 描画領域figureとグラフ領域axesを作成
fig, ax = plt.subplots(rows_graph,columns_graph,figsize=(20,30))

# 出力したい日数（行）×出力したい項目（列数）のグラフをaxesに描写
for i_day,day in enumerate(date_list):
    for j_item,item in enumerate(cal_items):

# 各地点のインスタンス変数long_dfをaxesに描写
        for idx, obj in enumerate(cal_obj_list):
            ax[i_day,j_item].plot(obj.long_df.loc[day,item],obj.long_df.loc[day,'depth'],linewidth=2.0)

        ax[i_day,j_item].set_ylim(280,330)
        ax[i_day,j_item].set_ylabel('標高(E.L.m)')
        ax[i_day,j_item].grid()
        ax[i_day,j_item].legend([site[:-1] for site in site_file_list])#ファイル名リストから凡例作成

        if item=='tt':
            ax[i_day,j_item].set_title(day.strftime('%Y年%m月%d日'))
            ax[i_day,j_item].set_xlim(0,30)
            ax[i_day,j_item].set_xlabel('水温(℃)')
        elif item=='chla':
            ax[i_day,j_item].set_xlim(0,50)
            ax[i_day,j_item].set_xlabel('chl-a(μg/L)')
        elif item=='T-N':
            ax[i_day,j_item].set_xlim(0,2)
            ax[i_day,j_item].set_xlabel('T-N(mg/L)')
        elif item=='dox':
            ax[i_day,j_item].set_xlim(0,15)
            ax[i_day,j_item].set_xlabel('DO(mg/L)')
        elif item=='cod':
            ax[i_day,j_item].set_xlim(0,10)
            ax[i_day,j_item].set_xlabel('COD(mg/L)')
        elif item=='po4':
            ax[i_day,j_item].set_xlim(0,0.05)
            ax[i_day,j_item].set_xlabel('P-PO4-P(mg/L)')
        elif item=='nh4':
            ax[i_day,j_item].set_xlim(0,4)
            ax[i_day,j_item].set_xlabel('NH4(mg/L)')
        elif item == 'no3':
            ax[i_day,j_item].set_xlim(0,2)
            ax[i_day,j_item].set_xlabel('NO3(mg/L)')        

        
plt.tight_layout()       
plt.savefig("sample.png",format = 'png', dpi=400)



# %%
