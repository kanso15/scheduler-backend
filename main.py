from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
from ortools.sat.python import cp_model

app = FastAPI()


# -------- Input schema --------
class SolveRequest(BaseModel):
    employees: List[str]
    days: List[str]
    shifts: List[str]


# -------- Solver endpoint --------
@app.post("/solve")
def solve_schedule(data: SolveRequest):
    model = cp_model.CpModel()

    # Decision variables
    work = {}
    for e in data.employees:
        for d in data.days:
            for s in data.shifts:
                work[(e, d, s)] = model.NewBoolVar(f"{e}_{d}_{s}")

    # Constraint: one shift per employee per day
    for e in data.employees:
        for d in data.days:
            model.Add(sum(work[(e, d, s)] for s in data.shifts) <= 1)

    # Constraint: every shift must be filled by exactly one employee
    for d in data.days:
        for s in data.shifts:
            model.Add(sum(work[(e, d, s)] for e in data.employees) == 1)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"error": "No feasible solution"}

    # Build result
    schedule = {}
    for e in data.employees:
        schedule[e] = {}
        for d in data.days:
            for s in data.shifts:
                if solver.Value(work[(e, d, s)]) == 1:
                    schedule[e][d] = s

    return {"schedule": schedule}
