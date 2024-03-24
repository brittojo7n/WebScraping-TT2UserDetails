from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

def get_user_details(account_name):
    df = pd.read_csv('tt2_players.csv')
    account_name = account_name.lower() 
    df_lower = df['Enkord account full name'].str.lower()  
    if account_name in df_lower.values:
        user_details = df[df_lower == account_name]
        user_id = user_details['User ID'].iloc[0]
        url = f'https://enkord.com/account/{user_id}'
        return user_details.to_html(index=False), url
    else:
        return f'Account name "{account_name}" does not exist.', None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        account_name = request.form['account_name']
        user_details, url = get_user_details(account_name)
        return render_template('index.html', user_details=user_details, url=url, account_name=account_name)
    else:
        return render_template('index.html', user_details=None, url=None, account_name=None)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=80)
