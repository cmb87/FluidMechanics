import sys
import os
import shutil
import time
import numpy as np
import uuid
import datetime
from bokeh.io import output_file, show
from bokeh.models import HoverTool
from bokeh.plotting import figure
from bokeh.embed import components

from src.common.database import Database
from src.config import SIMCOLLECTION
from src.config import DESIGNSCOLLECTION
from src.models.simulation.joukowski import JoukowskiAirfoil



class Simulation(JoukowskiAirfoil):
    def __init__(self, id=None, Uinf=1, R=1.3, a=1.0, alpha=0.0, beta=1.0, rho=1.0, cl=None, cd=None, L=None, D=None, opid=0, analysisid=0):
        super().__init__(Uinf=Uinf, R=R, a=a, alpha=alpha, beta=beta, rho=rho)
        self.id = None if id is None else id
        self.cl = None if cl is None else cl
        self.cd = None if cd is None else cd
        self.L = None if L is None else L
        self.D = None if D is None else D
        self.analysisid = analysisid
        self.opid = opid

    ### JSON ###
    def json(self):
        return {"id": self.id, "R":self.R, "a": self.a, "Uinf": self.Uinf, "alpha": self.alpha,
                "beta": self.beta, "rho": self.rho, "cl":self.lift_coefficient, "cd": self.drag_coefficient,
                "L": self.lift, "D": self.drag, "analysisid":self.analysisid, "opid": opid}

    ### Store it ###
    def store(self):
        return Database.insert(DESIGNSCOLLECTION, [self.json()])


class DigitalTwin(object):
    ### Constructor ###
    def __init__(self, id=None, created=None, directory=None, U1=None, U2=None, alpha1=None, alpha2=None):

        self.id = None if id is None else id
        self.directory = uuid.uuid4().hex if directory is None else directory
        self.created = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if created is None else created
        self.alpha1 = 0 if alpha1 is None else alpha1
        self.alpha2 = 0 if alpha1 is None else alpha2
        self.U1 = 1 if U1 is None else U1
        self.U2 = 1 if U2 is None else U2

    ### Convert to JSON ###
    def json(self):
        return {"id": self.id,
                "directory":self.directory,
                "created": self.created,
                "alpha1": self.alpha1,
                "alpha2": self.alpha2,
                "U1": self.U1,
                "U2": self.U2,
                }

    ### Store it ###
    def store(self):
        return Database.insert(SIMCOLLECTION, [self.json()])

    ### Update it ###
    def update(self):
        return Database.update(SIMCOLLECTION, self.json(), query={"id":["=", self.id]})

    ### Retrieve from DB ###
    @classmethod
    def retrieveAll(cls):
        return [cls(**case) for case in  Database.find(SIMCOLLECTION)]

    ### Retrieve from DB ###
    @classmethod
    def find_by_id(cls, caseid):
        return cls(**Database.find(SIMCOLLECTION, query={"id":["=", caseid]}, one=True))


    ### Start the simulation ###
    def simulate(self):
        sim1 = Simulation(Uinf=self.U1, alpha=self.alpha1)
        sim2 = Simulation(Uinf=self.U2, alpha=self.alpha2)

        sim1.calculateFlowField()
        sim2.calculateFlowField()
        sim1.plot_flowfield(store=True, name="static/img/flowfield1.png")
        sim2.plot_flowfield(store=True, name="static/img/flowfield2.png")

    ### Remove from DB ###
    @staticmethod
    def remove_from_DB(caseid):
        return Database.remove(SIMCOLLECTION, query={"id":["=", caseid]})

    ### Setup ###
    def setup(self, axes=[5,30,-60], amp=1e+3):
        pass
  
    ### Runs the code ####
    def solve(self):
        pass

    ### Create the plots ###
    def postprocess(self):
        pass