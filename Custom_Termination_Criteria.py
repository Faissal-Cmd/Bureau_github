from functools import partial

import gurobipy as gp
from gurobipy import GRB


class CallbackData:
    def __init__(self):
        self.last_gap_change_time = -GRB.INFINITY
        self.last_gap = GRB.INFINITY


def callback(model, where, *, cbdata):
    if where != GRB.Callback.MIP:
        return
    if model.cbGet(GRB.Callback.MIP_SOLCNT) == 0:
        return

    # Use model.terminate() to end the search when required...
    # ...


with gp.read("data/mkp.mps.bz2") as model:
    # Global variables used in the callback function
    time_from_best = 15
    epsilon_to_compare_gap = 1e-4

    # Initialize data passed to the callback function
    callback_data = CallbackData()
    callback_func = partial(callback, cbdata=callback_data)

    model.optimize(callback_func)