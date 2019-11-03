from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify
import numpy as np
import json
from src.models.simulation.digitaltwin import DigitalTwin
from src.common.flask_redirect import redirect_url

dt_blueprint = Blueprint('simulation', __name__)


### Run the digital twin ###
@dt_blueprint.route('/')
def start():
    return render_template('simulation/overview.html', cases=DigitalTwin.retrieveAll())


### Create simulation case ###
@dt_blueprint.route('/create')
def create():
    dt = DigitalTwin()
    dt.store()
    return "Case created"


### Remove Data item ###
@dt_blueprint.route('/remove')
def remove():
    DigitalTwin.remove_from_DB(request.args.get('dataid'))
    return "DataItem deleted successfully!"

### Update Data item ###
@dt_blueprint.route('/receive/<string:caseid>')
def receive(caseid):
    try:
        dt = DigitalTwin.find_by_id(caseid)
        dt.U1 = float(request.args.get('U1value'))
        dt.U2 = float(request.args.get('U2value'))
        dt.alpha1 = float(request.args.get('alpha1value'))
        dt.alpha2 = float(request.args.get('alpha2value'))
        dt.update()
        return "Successfull" #redirect(redirect_url())
    except:
        return "Update not successfull!"

### Run Simulation ###
@dt_blueprint.route('/simulate/<string:caseid>', methods=['GET', 'POST'])
def simulate(caseid):

    dt = DigitalTwin.find_by_id(caseid)
    res = dt.simulate()

    print(json.dumps(res))
    return json.dumps(res)


### Run the digital twin ###
@dt_blueprint.route('/run/<string:caseid>')
def run(caseid):

    dt = DigitalTwin.find_by_id(caseid)

    ### For tables ###
    return render_template('simulation/analysis/main.html', caseid=caseid, digitaltwin=dt)