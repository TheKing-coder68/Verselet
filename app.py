from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_login import LoginManager, current_user, UserMixin
import pandas as pd
from PIL import Image
from ExtraStuff import decoder, encoder, resize
from Models import Room, db
from websockets import socketio
# from werkzeug import secure_filename
import json
import os
import string
import random
from compling import *

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rooms.db'
# location for profile pics
db.init_app(app)
db.create_all(app=app)

socketio.init_app(app)


UPLOAD_FOLDER = "static/"
login_manager = LoginManager()
app.secret_key = 'ec52e5ead3899e4a0717b9806e1125de8af3bad84ca7f511'
login_manager.init_app(app)

def create_app():
    app = Flask(__name__)
    db.init_app(app)
    return app



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@login_manager.user_loader
@app.route('/')
def front():
    if 'user' in session:
        return render_template('homepage.html')
    else: return render_template('front.html')


@login_manager.user_loader
@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == "POST":
        df = pd.read_csv('User.csv')
        user = request.form.get("uname")
        password = request.form.get("psw")
        try:
            if decoder(df[df['User'] == user]['Pass'].values[0]) == password:
                session['user'] = user
                return redirect(url_for('user_profile'))
            else:
                flash('Incorrect username or password')
                return render_template("login.html")
        except:
            flash('Incorrect username or password')
            return redirect(url_for('login'))
    return render_template('login.html')


@login_manager.user_loader
@app.route("/create",methods=["POST","GET"])
def create_room():
    if request.method == "POST":

        room = Room()
        link =  ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(8))
        room.link=link
        room.users= json.dumps({"users": session["user"].split(" ")})
        print(room.users)
        db.session.add(room)
        db.session.commit()
        return redirect(f"/rooms/{room.link}")

    elif request.method == "GET" :
        # return website with button to
        return "<form method=POST><button>Make room</button></form>"

@login_manager.user_loader
@app.route("/rooms/<link>", methods=["POST","GET"])
def rooom(link):
    room = Room.query.filter(Room.link == link).first()
    print(room)
    # check if room exists
    if Room is None:
        return abort(404)
    users= json.loads(room.users)
    print(session["user"])
    if session["user"] not in users["users"]:
        users["users"].append(session["user"])
    room.users = json.dumps(users)
    print(room.users)
    db.session.commit()
    return render_template("room.html", link=room.link)


@login_manager.user_loader
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        df = pd.read_csv('User.csv')
        email = request.form.get('email')
        user = request.form.get("uname")
        password = encoder(request.form.get("psw"))
        dob = request.form.get('dob')
        if user in df.User.values:
            flash(f'An account with that username already exists.')
            return redirect(url_for('register'))
        elif email in df.Email.values:
            flash(f'An account with that email address already exists.')
            return redirect(url_for('register'))
        else:
            df2 = pd.read_csv('db.csv')
            df = df.append({'User': user, 'Pass': password, 'Email': email, 'Id': len(df) + 1, 'DOB': dob},
                           ignore_index=True)
            df2 = df2.append({'Wins': 0, 'Games': 0, 'Avr. Time': 0, 'Username': user}, ignore_index=True)
            df2.to_csv('db.csv', index=False)
            df.to_csv('User.csv', index=False)
            session['user'] = user
            im1 = Image.open('static/base.png')
            im1.save(f'static/{user}.png')
            return redirect(url_for('front'))
    return render_template('register.html')


@login_manager.user_loader
@app.route('/profile')
def user_profile():
    try:
        dob = ''; e_mail = ''; inx = 0
        month = ['empty', 'January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']
        df2 = pd.read_csv('db.csv')
        pfp = f'static/{session["user"]}.png'
        udb = pd.read_csv('User.csv')
        wins = df2[df2['Username'] == session['user']]['Wins'].values[0]
        games = df2[df2['Username'] == session['user']]['Games'].values[0]
        for i in udb['User']:
            if udb['User'].values[inx] == session['user']:
                e_mail = udb['Email'][inx]; dob = udb['DOB'][inx]
            else: inx += 1
        doby = dob.split('/')[2]
        dobd = dob.split('/')[1]
        dobm = month[int(dob.split('/')[0])]
        return render_template('profile.html', w=wins, pfp=pfp, g=games, u=session['user'], e=e_mail, d=dobd, m=dobm, y=doby)
    except:
        flash("Please login or create an account first")
        return redirect(url_for('login'))
@app.route('/code', methods=['GET', 'POST'])
def code():
    if request.method == "POST":
        in_code = request.form.get('code')
        lang = request.form.get('lang')
        print(lang)
        print(compiler(in_code, lang))
        print(in_code)
        result,errors = compiler(in_code, lang)
        result = result.replace("\n", '\n')
    return render_template('compiling.html', r=result, e=errors, c=in_code)


@login_manager.user_loader
@app.route('/about', methods=['POST', 'GET'])
def aboutus():
    return render_template('about.html')


@login_manager.user_loader
@app.route('/settings', methods=['POST', 'GET'])
def settings_page():
    if 'user' in session:
        try:

            # PASSING ALL INFO TO DISPLAY

            dob = ''; e_mail = ''; inx = 0
            month = ['empty', 'January', 'February', 'March', 'April', 'May', 'June',
                     'July', 'August', 'September', 'October', 'November', 'December']
            df2 = pd.read_csv('db.csv')
            udb = pd.read_csv('User.csv')
            wins = df2[df2['Username'] == session['user']]['Wins'].values[0]
            games = df2[df2['Username'] == session['user']]['Games'].values[0]
            for i in udb['User']:
                if udb['User'].values[inx] == session['user']: e_mail = udb['Email'][inx];dob = udb['DOB'][inx]
                else: inx += 1

            # DOING THE ACTUAL CHANGES

            if request.method == 'POST':

                df = pd.read_csv('User.csv'); ud = pd.read_csv('db.csv'); inx = 0
                for i in df.User:
                    if i == session['user']:
                        # CHECKING IF ANY CHANGES ARE REQUESTED
                        uploaded_file = request.files["file"]
                        if request.form.get('unameedit') != "" or request.form.get(
                                'emailedit') != "" or request.form.get('dob') != "" or request.form.get(
                                'passedit') != "" or uploaded_file.filename != "":
                            # CHECK IF PASSWORD IS CORRECT
                            if request.form.get('p') == decoder(df.Pass[inx]):
                                index = 0
                                # USERNAME EDIT
                                if request.form.get('unameedit') != "":
                                    if request.form.get('unameedit') in list(df.User):
                                        flash("Username already taken")
                                        settings_page()
                                        return render_template('settingspage.html')
                                    else:
                                        df.replace(to_replace=df.User[inx], value=request.form.get('unameedit'),
                                                   inplace=True)
                                        df.to_csv('User.csv', index=False)
                                        for j in ud.Username:
                                            if j == session['user']:
                                                ud.replace(to_replace=ud.Username[inx],
                                                           value=request.form.get('unameedit'),
                                                           inplace=True)
                                                ud.to_csv('db.csv', index=False)
                                                os.rename('static/' + session['user'] + '.png',
                                                          'static/' + request.form.get('unameedit') + '.png')
                                                session['user'] = request.form.get('unameedit')
                                            else:
                                                index += 1
                                # EMAIL EDIT
                                if request.form.get('emailedit') != "":
                                    if request.form.get('emailedit') in list(df.Email):
                                        flash("An account with this email address already exists")
                                        settings_page()
                                        return render_template('settingspage.html')
                                    else:
                                        df.replace(to_replace=df.Email[inx], value=request.form.get('emailedit'),
                                                   inplace=True)
                                        df.to_csv('User.csv', index=False)
                                # PROFILE PICTURE EDIT
                                if uploaded_file.filename != " ":
                                    os.remove(UPLOAD_FOLDER + session['user'] + '.png')
                                    uploaded_file.save(os.path.join(UPLOAD_FOLDER, i + '.png'))
                                    # Resize profile pic to 64x64
                                    resize(os.path.join(UPLOAD_FOLDER, i + '.png'))
                                # PASSWORD EDIT
                                if request.form.get('passedit') != "":
                                    df.replace(to_replace=df.Pass[inx], value=encoder(request.form.get('passedit')),
                                               inplace=True)
                                    df.to_csv('User.csv', index=False)
                                return render_template('homepage.html')
                            else:
                                flash('Incorrect password')
                                return render_template('settingspage.html')
                    else:
                        inx += 1
                return render_template('homepage.html')
            return render_template('settingspage.html', w=wins, g=games, u=session['user'], e=e_mail, d=dob)
        except Exception as e:
            print(e)
            return render_template('login.html')
    else:
        flash('hi User, you might wanna login first')
        return redirect(url_for('login'))


@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


if __name__ == '__main__':
    #app.run(debug=True)
    socketio.run(app, debug=True)