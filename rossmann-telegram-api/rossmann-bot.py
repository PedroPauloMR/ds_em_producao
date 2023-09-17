import json
import os
import requests
import pandas as pd
from flask import Flask, request, Response

# content API Telegram
TOKEN = '5695669448:AAEYS7XE5eCnEmNTATXYh2Cf8B5irAHZB-o'

# info about BOT
# 'https://api.telegram.org/bot5695669448:AAEYS7XE5eCnEmNTATXYh2Cf8B5irAHZB-o/getMe'

# get updates
# 'https://api.telegram.org/bot5695669448:AAEYS7XE5eCnEmNTATXYh2Cf8B5irAHZB-o/getUpdates'

# webhook
# 'https://api.telegram.org/bot5695669448:AAEYS7XE5eCnEmNTATXYh2Cf8B5irAHZB-o/setWebhook?url='

# send messages
# 'https://api.telegram.org/bot5695669448:AAEYS7XE5eCnEmNTATXYh2Cf8B5irAHZB-o/sendMessage?chat_id=&text=Hi Pedro, I"good thanks!'



def send_message(chat_id, text):
    url = "https://api.telegram.org/bot{}/".format(TOKEN)
    url = url + "sendMessage?chat_id={}".format(TOKEN,chat_id)
    r = requests.post(url , json = {'text': text})
    print('Status code {}'.format(r.status_code))
    return None


def load_dataset(store_id):
    # loading test dataset
    path_data = 'C:/repos/portfolio_projetos/ds_em_producao/'
    path_data = ''
    df10 = pd.read_csv(path_data + 'test.csv')
    df_store_raw = pd.read_csv(path_data + 'store.csv')

    # merge test + store dataset
    df_test = pd.merge(df10, df_store_raw, how = 'left', on = 'Store')

    # choose store for prediction
    df_test = df_test[ df_test['Store'] == store_id]

    if not df_test.empty:
        # remove closed days
        df_test = df_test[ df_test['Open'] != 0 ]
        df_test = df_test[ ~df_test['Open'].isnull() ]
        df_test = df_test.drop(['Id'], axis = 1)

        # convert to JSON
        data = json.dumps(df_test.to_dict( orient = 'records') )
    else:
        data = 'error'
    return data



def predict( data ):
    # API call
    # url = 'http://192.168.0.14:5000/rossmann/predict'
    url = 'https://rossmann-pedro-test-model.herokuapp.com/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post(url, headers = header, data = data)
    print(' status code: {}'.format(r.status_code))

    d1 = pd.DataFrame(r.json(), columns = r.json()[0].keys())
    return d1



def parse_message( message ):
    chat_id = message['message']["chat"]['id']
    store_id = message['message']['text']

    store_id = store_id.replace('/','')

    try:
        store_id = int( store_id )
    except ValueError:
        store_id = 'error'
    return chat_id, store_id


# API initialize
app = Flask( __name__ )


@app.route('/', methods = ['POST','GET'])
def index():
    if request.method == 'POST':
        message = request.get_json()
        chat_id, store_id = parse_message( message)
        
        if store_id != 'error':
            
            # loading data
            data = load_dataset( store_id )
            if data != 'error':
                
                # prediction
                d1 = predict( data )

                # calculation
                d2 = d1[['store','prediction']].groupby('store').sum().reset_index()
                
                # send message
                msg = 'Store number {} will sell R$ {:,.2f} in the next 6 weeks.'.format(d2['store'].values[0], d2['prediction'].values[0])

                send_message(chat_id, msg)
                return Response('Ok', status = 200)
                                



            else:
                send_message(chat_id, 'Store ID is not in the data. Chose another one.')
                return Response('Ok', status = 200)


            

        else:
            send_message(chat_id, 'Store ID is wrong. It need to be a number')
            return Response('Ok', status = 200)


    else:
        return '<h1> Rossmann Telegram BOT </h1>'   



if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host = '0.0.0.0', port = port)