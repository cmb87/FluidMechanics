import sys
import os
import shutil
import time
import numpy as np
import uuid
import datetime


from ...common.database import Database
from .joukowski import JoukowskiAirfoil
from ..optimizer.swarm import Swarm


SIMCOLLECTION = "simulations"
LOGCOLLECTION = "logs"
DESIGNSCOLLECTION = "designs"

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


### Log file for manual transactions ###
class DesignLogMessage():
    def __init__(self, id=None, user=None, caseid=None, created=None, message=None):
        self.id = None if id is None else id
        self.user = None if user is None else user
        self.caseid = None if caseid is None else caseid
        self.message = None if message is None else message
        self.created = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if created is None else created

    ### TO json ###
    def json(self):
        return {"id":self.id,
                "user": self.user,
                "caseid": self.caseid,
                "message": self.message,
                "created": self.created}

    ### Store transaction ###
    def store(self):
        return Database.insert(LOGCOLLECTION, [self.json()])

    ### Store transaction ###
    @staticmethod
    def delete(caseid):
        return Database.remove(LOGCOLLECTION, query={"caseid":["=", caseid]})

    ### Get all transactions ###
    @classmethod
    def retrieveAll(cls, caseid):

        cases = Database.find(LOGCOLLECTION, query={"caseid":["=", caseid]})

        if cases:
            return [cls(**data) for data in cases]
        else:
            return []



class DigitalTwin(object):
    ### Constructor ###
    def __init__(self, id=None, created=None, directory=None, U1=None, U2=None, alpha1=None, alpha2=None, a0=1.0, R0=1.05, beta0=0.0):

        self.id = None if id is None else id
        self.directory = uuid.uuid4().hex if directory is None else directory
        self.created = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if created is None else created
        self.alpha1 = 0 if alpha1 is None else alpha1
        self.alpha2 = 0 if alpha1 is None else alpha2
        self.U1 = 1 if U1 is None else U1
        self.U2 = 1 if U2 is None else U2
        self.a0, self.R0, self.beta0 = a0, R0, beta0

        if os.path.isdir("./application/static/res/{}".format(self.directory)):
            pass
        else:
            os.mkdir("./application/static/res/{}".format(self.directory))

    ### Convert to JSON ###
    def json(self):
        return {"id": self.id,
                "directory":self.directory,
                "created": self.created,
                "alpha1": self.alpha1,
                "alpha2": self.alpha2,
                "U1": self.U1,
                "U2": self.U2,
                "a0": self.a0, 
                "R0": self.R0, 
                "beta0": self.beta0
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

        cases =  Database.find(SIMCOLLECTION)
        if cases:
            return [cls(**data) for data in cases]
        else:
            return []
        

    ### Retrieve from DB ###
    @classmethod
    def find_by_id(cls, caseid):
        return cls(**Database.find(SIMCOLLECTION, query={"id":["=", caseid]}, one=True))


    ### Start the simulation ###
    def simulate(self, plot=True):
        sim1 = Simulation(Uinf=self.U1, alpha=self.alpha1, beta=self.beta0, a=self.a0, R=self.R0)
        sim2 = Simulation(Uinf=self.U2, alpha=self.alpha2, beta=self.beta0, a=self.a0, R=self.R0)

        sim1.calculateFlowField()
        sim2.calculateFlowField()

        if plot:
            sim1.plot_flowfield(store=True, name="./application/static/res/{}/{}".format(self.directory, "flowfield1.png"))
            sim2.plot_flowfield(store=True, name="./application/static/res/{}/{}".format(self.directory, "flowfield2.png"))

            sim1.plot_cp(store=True, name="./application/static/res/{}/{}".format(self.directory, "profile1.png"))
            sim2.plot_cp(store=True, name="./application/static/res/{}/{}".format(self.directory, "profile2.png"))

        return {'LiftOp1': np.around(sim1.lift,6), "ClOp1": np.around(sim1.lift_coefficient,6),
                "DragOp1": np.around(sim1.drag,6), "CdOp1": np.around(sim1.drag_coefficient,6),
                "LiftOp2": np.around(sim2.lift,6), "ClOp2": np.around(sim2.lift_coefficient,6),
                "DragOp2": np.around(sim2.drag,6), "CdOp2": np.around(sim2.drag_coefficient,6)}

    ### Remove from DB ###
    @staticmethod
    def remove_from_DB(caseid):
        return Database.remove(SIMCOLLECTION, query={"id":["=", caseid]})

    ### Setup ###
    @staticmethod
    def optimize(caseid, xbounds, itermax, swarmsize, targets, constraints):
        ### Get Case ###
        dt = DigitalTwin.find_by_id(caseid)

        ### Fitness function ###
        def fitness(x, dt, constraints, targets, caseid):
            y, c = [], []

            for n in range(x.shape[0]):
                dt.R0, dt.beta0, dt.a0 = x[n,0], x[n,1], x[n,2]

                if dt.a0>=dt.R0:
                    y.append(len(targets)*[10]) 
                    c.append(len(constraints)*[10])
                    continue

                ### Run simulation ###
                res = dt.simulate(plot=False)

                ### Separate between targets and constraints ###
                yd, cd = [],[]
                for name in sorted(list(res.keys())):
                    if name in list(constraints.keys()):
                        cd.append(res[name])
                    elif name in list(targets.keys()):
                        yd.append(targets[name]["optidir"]*res[name])

                y.append(yd)
                c.append(cd)

                ### Insert design into DB ###

                print([{"id":None, "caseid":caseid, 
                                                     "clop1": res["ClOp1"], "cdop1": res["CdOp1"], "lop1": res["LiftOp1"], "dop1": res["DragOp1"],
                                                     "clop2": res["ClOp2"], "cdop2": res["CdOp2"], "lop2": res["LiftOp2"], "dop2": res["DragOp2"],
                                                     "R": dt.R0, "a": dt.a0, "beta":dt.beta0,
                                                   }])

                Database.insert(DESIGNSCOLLECTION, [{"id":None, "caseid":caseid, 
                                                     "clop1": res["ClOp1"], "cdop1": res["CdOp1"], "lop1": res["LiftOp1"], "dop1": res["DragOp1"],
                                                     "clop2": res["ClOp2"], "cdop2": res["CdOp2"], "lop2": res["LiftOp2"], "dop2": res["DragOp2"],
                                                     "R": dt.R0, "a": dt.a0, "beta":dt.beta0,
                                                   }])

            return np.asarray(y), np.asarray(c)
        
        ### Bounds ###
        ybounds, cbounds = [], []

        for name in sorted(['LiftOp1', 'LiftOp1', "DragOp1", "DragOp2"]):
            if name in list(constraints.keys()):
                cbounds.append(constraints[name]["bounds"])
            elif name in list(targets.keys()):
                ybounds.append(targets[name]["bounds"])


        ### Bokeh plot ###


        ### Start Optimization ##
        swarm = Swarm(fitness, xbounds, ybounds, cbounds, nparticles=swarmsize, dt=dt, constraints=constraints, targets=targets, caseid=caseid)
        swarm.initialize()
        swarm.iterate(itermax)
  


    ### AJAX plot ####
    @staticmethod
    def get_opti_data(caseid):
        return Database.find(DESIGNSCOLLECTION, query={"caseid":["=", caseid]})