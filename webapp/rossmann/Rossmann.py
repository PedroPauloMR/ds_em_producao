import joblib
import inflection
import pandas as pd
import numpy as np
import math
import datetime

class Rossmann( object ):
    def __init__( self ):
        self.home_path = r'C:\\repos\\portfolio_projetos\\ds_em_producao\\'
        self.competition_distance_scaler = joblib.load(self.home_path + 'parameter\\competition_distance_scaler.pkl')
        self.store_type_scaler = joblib.load(self.home_path + 'parameter\\store_type_scaler.pkl')
        self.competition_time_month_scaler = joblib.load(self.home_path + 'parameter\\competition_time_month_scaler.pkl')
        self.promo_time_week_scaler = joblib.load(self.home_path + 'parameter\\promo_time_week_scaler.pkl')
        self.year_scaler = joblib.load(self.home_path + 'parameter\\year_scaler.pkl')
        
        
        
    def data_cleaning(self, df1 ):
        # 1.1 rename columns
        cols_old = ['Store', 'DayOfWeek', 'Date', 'Open', 'Promo',
                'StateHoliday', 'SchoolHoliday', 'StoreType', 'Assortment',
               'CompetitionDistance', 'CompetitionOpenSinceMonth',
               'CompetitionOpenSinceYear', 'Promo2', 'Promo2SinceWeek',
               'Promo2SinceYear', 'PromoInterval']

        snakecase = lambda x: inflection.underscore(x)
        cols_new = list( map( snakecase, cols_old))

        # rename
        df1.columns = cols_new
        
        ## 1.3 data types
        df1['date'] = pd.to_datetime(df1['date'])

        ## 1.5 fillout N/As
        # competition_distance              2642
        df1['competition_distance'] = df1['competition_distance'].apply(lambda x: 200000.0 
                                                                        if math.isnan(x) else x)

        # competition_open_since_month    323348
        df1['competition_open_since_month'] = df1.apply(lambda x: x['date'].month 
                                                        if math.isnan(x['competition_open_since_month']) 
                                                        else x['competition_open_since_month'], axis = 1)

        # competition_open_since_year     323348
        df1['competition_open_since_year'] = df1.apply(lambda x: x['date'].year 
                                                       if math.isnan(x['competition_open_since_year']) 
                                                       else x['competition_open_since_year'], axis = 1)

        # promo2_since_week               508031
        df1['promo2_since_week'] = df1.apply(lambda x: x['date'].week 
                                             if math.isnan(x['promo2_since_week']) 
                                             else x['promo2_since_week'], axis = 1)

        # promo2_since_year               508031
        df1['promo2_since_year'] = df1.apply(lambda x: x['date'].year 
                                             if math.isnan(x['promo2_since_year']) 
                                             else x['promo2_since_year'], axis = 1)

        # promo_interval                  508031
        month_map = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',
                     8:'Aug', 9:'Sept',10:'Oct',11:'Nov',12:'Dec'}

        df1['promo_interval'].fillna(0, inplace = True)

        df1['month_map'] = df1['date'].dt.month.map(month_map)

        df1['is_promo'] = df1[['promo_interval','month_map']].apply(lambda x: 0 
                                                                    if x['promo_interval'] == 0 
                                                                    else 1 if x['month_map'] 
                                                                    in x['promo_interval'].split(',') 
                                                                    else 0, axis = 1)

        ## 1.6 change data types
        change_int = ['competition_open_since_month','competition_open_since_year',
                      'promo2_since_week','promo2_since_year']
        for i in change_int:
            df1[i] = df1[i].astype('int64')
            
        return df1
    


    def feature_engineering( self, df1 ):
        ##3.4  2.3 Feature Engineering
        # year
        df1['year'] = df1['date'].dt.year

        # month
        df1['month'] = df1['date'].dt.month

        #day
        df1['day'] = df1['date'].dt.day

        # week of year
        df1['week_of_year'] = df1['date'].dt.weekofyear

        # year week
        df1['year_week'] = df1['date'].dt.strftime('%Y-%W')

        # competition since
        df1['competition_since'] = df1.apply(lambda x: datetime.datetime(
                                year = x['competition_open_since_year'], 
                                month =  x['competition_open_since_month'], 
                                    day = 1), axis = 1)

        df1['competition_time_month'] = ((df1['date'] - df1['competition_since']) / 30).apply(lambda x: x.days).astype('int64')


        # promo since
        df1['promo_since'] = df1['promo2_since_year'].astype(str) + '-' + df1['promo2_since_week'].astype(str)
        df1['promo_since'] = df1['promo_since'].apply(lambda x: datetime.datetime.strptime(
                                        x + '-1', '%Y-%W-%w') - datetime.timedelta(days = 7))

        df1['promo_time_week'] = ((df1['date'] - df1['promo_since']) / 7).apply(lambda x: x.days).astype('int64')


        #assortment
        df1['assortment'] = df1['assortment'].apply(lambda x: 'basic' 
                                                    if x == 'a' 
                                                    else 'extra' if x == 'b' else 'extended')

        #state holiday
        df1['state_holiday'] = df1['state_holiday'].apply(lambda x: 'public_holiday' if x == 'a' else 
                                                                    'easter_holiday' if x == 'b' else 
                                                                    'christmas' if x == 'c' else
                                                                    'regular_day')

        df1['week_of_year'] = df1['date'].dt.weekofyear


        ##4.1  3.1 Filtragem das linhas
        df1 = df1.loc[ (df1['open'] != 0) ]

        ##4.2  3.2 Seleção das colunas
        cols_drop = ['open','promo_interval','month_map']
        df1.drop(cols_drop, axis = 1, inplace = True)
        return df1
    
    

    def data_preparation( self, df2 ):
        ## encoding
        # competition distance
        df2['competition_distance'] = self.competition_distance_scaler.transform( df2[['competition_distance']].values )
#         joblib.dump(rs, 'parameter\\competition_distance_scaler.pkl')


        # competition time month
        df2['competition_time_month'] = self.competition_time_month_scaler.transform( df2[['competition_time_month']].values )
#         joblib.dump(rs, 'parameter\\competition_time_month_scaler.pkl')


        # promo time week
        df2['promo_time_week'] = self.promo_time_week_scaler.transform( df2[['promo_time_week']].values )
#         joblib.dump(mms, 'parameter\\promo_time_week_scaler.pkl')


        # year
        df2['year'] = self.year_scaler.transform( df2[['year']].values )
#         joblib.dump(mms, 'parameter\\year_scaler.pkl')


        ## response variable transformation
        # state_holiday - one_hot_encoding
        df2 = pd.get_dummies(df2, prefix = ['state_holiday'], columns = ['state_holiday'])

        # store_type - label_encoding
        df2['store_type'] = self.store_type_scaler.transform(df2['store_type'])
#         joblib.dump(le, 'parameter\\store_type_scaler.pkl')


        # assortment - ordinal_encoding
        assortment_dict = {'basic': 1, 'extra': 2, 'extended': 3}
        df2['assortment'] = df2['assortment'].map(assortment_dict)


        ## nature transformation
        # day of week
        df2['day_of_week_sin'] = df2['day_of_week'].apply( lambda x: np.sin( x * (2 * np.pi / 7 ) ) )
        df2['day_of_week_cos'] = df2['day_of_week'].apply( lambda x: np.cos( x * (2 * np.pi / 7 ) ) )

        # month
        df2['month_sin'] = df2['month'].apply( lambda x: np.sin( x * (2 * np.pi / 12 ) ) )
        df2['month_cos'] = df2['month'].apply( lambda x: np.cos( x * (2 * np.pi / 12 ) ) )

        # day
        df2['day_sin'] = df2['day'].apply( lambda x: np.sin( x * (2 * np.pi / 30 ) ) )
        df2['day_cos'] = df2['day'].apply( lambda x: np.cos( x * (2 * np.pi / 30 ) ) )

        # week of year
        df2['week_of_year_sin'] = df2['week_of_year'].apply( lambda x: np.sin( x * (2 * np.pi / 52 ) ) )
        df2['week_of_year_cos'] = df2['week_of_year'].apply( lambda x: np.cos( x * (2 * np.pi / 52 ) ) )
        
        # columns selection
        cols_selected = ['store','promo','store_type','assortment',
                                'competition_distance','competition_open_since_month',
                                'competition_open_since_year','promo2','promo2_since_week',
                                'promo2_since_year','competition_time_month','promo_time_week',
                                'day_of_week_sin','day_of_week_cos','month_cos','month_sin',
                                'day_sin','day_cos','week_of_year_sin','week_of_year_cos']
        df2 = df2[cols_selected]
        return df2
    
    

    def get_prediction(self, model, original_data, test_data):
        # prediction
        pred = model.predict(test_data)
        
        # join pred with original data
        original_data['prediction'] = np.expm1(pred)
        return original_data.to_json( orient = 'records', date_format = 'iso')