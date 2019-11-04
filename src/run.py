import sys
import os
import json
import numpy as np

from flask import Flask, render_template, url_for, request, jsonify
from flask_reverse_proxy_fix.middleware import ReverseProxyPrefixFix

sys.path.append('../')

### Initialize Modules ###
from src.common.database import Database
from src.config import SECRETKEY
from src.config import SIMCOLLECTION
from src.config import DESIGNSCOLLECTION
from src.config import LOGCOLLECTION

### Initialize Flask ###
app = Flask(__name__)
app.secret_key = SECRETKEY

#app.config['REVERSE_PROXY_PATH'] = '/modular-dashboard/app'
#ReverseProxyPrefixFix(app)

### Init DB ###
@app.before_first_request
def init_db():
    tables = {SIMCOLLECTION:  {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "directory": "TEXT",
                                "alpha1": "FLOAT", "alpha2": "FLOAT", "U1": "FLOAT", "U2": "FLOAT",
                                "R0": "FLOAT", "a0": "FLOAT", "beta0": "FLOAT", "created":"TIMESTAMP"},

              LOGCOLLECTION:  {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "user":"TEXT", "caseid": "INT" ,"created":"TIMESTAMP",
                               "message": "TEXT"},

              DESIGNSCOLLECTION:  {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "caseid": "INT",
                                   "clop1": "FLOAT", "cdop1": "FLOAT", "lop1": "FLOAT", "dop1": "FLOAT",
                                   "clop2": "FLOAT", "cdop2": "FLOAT", "lop2": "FLOAT", "dop2": "FLOAT",
                                   "R": "FLOAT", "a": "FLOAT", "beta": "FLOAT"} 
              }

    for table, columns in tables.items():
        #Database.delete_table(table)
        Database.create_table(table, columns)
        pass

### Home HTML ###
@app.route('/')
def home():
    return render_template('home.html', baseurl=request.base_url)

### Add blueprints ###
from src.models.simulation.views import dt_blueprint
app.register_blueprint(dt_blueprint, url_prefix="/simulation")


### Start app ###
if __name__ == '__main__':
    app.run() # host='0.0.0.0', port=5000
