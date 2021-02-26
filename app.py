from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, current_user, UserMixin
import pandas as pd
from ExtraStuff import decoder, encoder

app = Flask(__name__)

login_manager = LoginManager()
app.secret_key = 'ec52e5ead3899e4a0717b9806e1125de8af3bad84ca7f511'
login_manager.init_app(app)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@login_manager.user_loader
@app.route('/')
def front():
    if 'user' in session:
        return render_template('homepage.html')
    else:
        return render_template('front.html')


@login_manager.user_loader
@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == "POST":
        df = pd.read_csv('user.csv')
        user = request.form.get("uname")

        password = request.form.get("psw")
        if df[df['User'] == user]['Pass'].values[0] == encoder(password):
            session['user'] = user
            flash(f'Welcome, {user}')
            return redirect(url_for('user_profile'))
        else:
            flash('Incorrect username or password')
            return redirect(url_for('login'))
    return render_template('login.html')


@login_manager.user_loader
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        df = pd.read_csv('user.csv')
        email = request.form.get('email')
        user = request.form.get("uname")
        password = encoder(request.form.get("psw"))
        if user in df.User.values:
            flash(f'Username {user} is already taken')
            return redirect(url_for('register'))
        else:
            df2 = pd.read_csv('db.csv')
            df = df.append({'User': user, 'Pass': password, 'Email': email, 'Id': len(df) + 1}, ignore_index=True)
            df2 = df2.append({'Wins': 0, 'Games': 0, 'Avr. Time': 0, 'Username': user}, ignore_index=True)
            df2.to_csv('db.csv', index=False)
            df.to_csv('user.csv', index=False)
            return redirect(url_for('front'))
    return render_template('register.html')


@login_manager.user_loader
@app.route('/profile')
def user_profile():
    try:
        df2 = pd.read_csv('db.csv')
        wins = df2[df2['Username'] == session['user']]['Wins'].values[0]
        games = df2[df2['Username'] == session['user']]['Games'].values[0]
        return render_template('profile.html', w=wins, g=games, u=session['user'])
    except:
       flash('Login First')
       return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
    print(session['user'])
