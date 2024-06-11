#!/usr/bin/python

# author: Stéphane Péneau
# source: https://github.com/Stefal/rtkbase

# Reverse proxy server to acces a Gnss receiver integrated Web Server (Mosaic-X5 or other)

import os
from gevent import monkey
monkey.patch_all()
import requests

from RTKBaseConfigManager import RTKBaseConfigManager
#from dotenv import load_dotenv  # pip package python-dotenv

from flask_bootstrap import Bootstrap4
from flask import Flask, render_template, session, request, flash, url_for, Response
from flask import redirect, abort
from flask import g
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from wtforms.validators import ValidationError, DataRequired, EqualTo
import urllib
import gunicorn.app.base

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.utils import safe_join


app = Flask(__name__)
app.debug = False
app.config["SECRET_KEY"] = "secret!"
app.config["LOGIN_DISABLED"] = False

rtkbase_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

login=LoginManager(app)
login.login_view = 'login_page'
bootstrap = Bootstrap4(app)

#Get settings from settings.conf.default and settings.conf
rtkbaseconfig = RTKBaseConfigManager(os.path.join(rtkbase_path, "settings.conf.default"), os.path.join(rtkbase_path, "settings.conf"))
GNSS_RCV_WEB_URL = str("{}{}".format("http://", rtkbaseconfig.get("main", "gnss_rcv_web_ip")))

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

class User(UserMixin):
    """ Class for user authentification """
    def __init__(self, username):
        self.id=username
        self.password_hash = rtkbaseconfig.get("general", "web_password_hash")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LoginForm(FlaskForm):
    """ Class for the loginform"""
    #username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Please enter the RTKBase password:', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

@app.before_request
def inject_release():
    """
        Insert the RTKBase release number as a global variable for Flask/Jinja
    """
    g.version = rtkbaseconfig.get("general", "version")
    
@login.user_loader
def load_user(id):
    return User(id)

#proxy code from https://stackoverflow.com/a/36601467
@app.route('/', defaults={'path': ''}, methods=["GET", "POST"])  # ref. https://medium.com/@zwork101/making-a-flask-proxy-server-online-in-10-lines-of-code-44b8721bca6
@app.route('/<path>', methods=["GET", "POST"])  # NOTE: better to specify which methods to be accepted. Otherwise, only GET will be accepted. Ref: 
@login_required
def redirect_to_API_HOST(path):  #NOTE var :path will be unused as all path we need will be read from :request ie from flask import request
    res = requests.request(  # ref. https://stackoverflow.com/a/36601467/248616
        method          = request.method,
        url             = request.url.replace(request.host_url, f'{GNSS_RCV_WEB_URL}/'),
        headers         = {k:v for k,v in request.headers if k.lower() != 'host'}, # exclude 'host' header
        data            = request.get_data(),
        cookies         = request.cookies,
        allow_redirects = False,
    )
    """ print("method: ", request.method)
    print("request posturl: ", request.url)
    print("request host: ", request.host_url)
    print("url: ", request.url.replace(request.host_url, f'{GNSS_RCV_WEB_URL}/'))
    print("header: ", {k:v for k,v in request.headers if k.lower() != 'host'})
    print("data: ", request.get_data())
    print("cookies: ", request.cookies)
    print("host url split", urllib.parse.urlsplit(request.host_url))
    print("host url split2", urllib.parse.urlsplit(request.base_url).hostname)
    old = urllib.parse.urlparse(request.host_url)
    new = urllib.parse.ParseResult(scheme=old.scheme, netloc="{}:{}".format(old.hostname, 9090),
                  path=old.path, params=old.params, query=old.query, fragment=old.fragment)
    print("new_url: ", new.geturl()) """
    #region exlcude some keys in :res response
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']  #NOTE we here exclude all "hop-by-hop headers" defined by RFC 2616 section 13.5.1 ref. https://www.rfc-editor.org/rfc/rfc2616#section-13.5.1
    headers          = [
        (k,v) for k,v in res.raw.headers.items()
        if k.lower() not in excluded_headers
    ]
    #endregion exlcude some keys in :res response

    response = Response(res.content, res.status_code, headers)
    return response


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    loginform = LoginForm()
    if loginform.validate_on_submit():
        user = User('admin')
        password = loginform.password.data
        if not user.check_password(password):
            return abort(401)
        
        login_user(user, remember=loginform.remember_me.data)
        next_page = request.args.get('redirect_to_API_HOST')
        if not next_page or urllib.parse.urlsplit(next_page).netloc != '':
            next_page = url_for('redirect_to_API_HOST')

        return redirect(next_page)
        
    return render_template('proxy_login.html', title='Sign In', form=loginform)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    try:
        #check if authentification is required
        if not rtkbaseconfig.get_web_authentification():
            app.config["LOGIN_DISABLED"] = True

        app.secret_key = rtkbaseconfig.get_secret_key()
        #socketio.run(app, host = "::", port = args.port or rtkbaseconfig.get("general", "web_port", fallback=80), debug=args.debug) # IPv6 "::" is mapped to IPv4
        #wsgi.server(eventlet.listen(("0.0.0.0", int(rtkbaseconfig.get("main", "gnss_rcv_web_proxy_port", fallback=9090)))), app, log_output=False)

        gunicorn_options = {
        'bind': ['%s:%s' % ('0.0.0.0', rtkbaseconfig.get("main", "gnss_rcv_web_proxy_port", fallback=9090)),
                    '%s:%s' % ('[::1]', rtkbaseconfig.get("main", "gnss_rcv_web_proxy_port", fallback=9090)) ],
        'workers': 1,
        'worker_class': 'gevent',
        'loglevel': 'warning',
        }
        #start gunicorn
        StandaloneApplication(app, gunicorn_options).run()

    except KeyboardInterrupt:
        print("Server interrupted by user!!")

