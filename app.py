import os
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from core.schemas import ProblemInput, SolutionOutput, DatasetInfo
from core.solver import PyVRPSolver
from core.datasets import BENCHMARK_DATASETS, DatasetInfo, generate_random_vrp

app = FastAPI(
    title="PyVRP Vehicle Routing Problem API",
    description="REST API for solving Vehicle Routing Problems using PyVRP algorithm solver.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

solver = PyVRPSolver()

# Base static dir path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def get_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"status": "PyVRP API Service Running", "docs": "/docs"})


@app.get("/api/datasets", response_model=List[DatasetInfo])
def list_datasets():
    """List all pre-loaded benchmark VRP datasets."""
    return [item["info"] for item in BENCHMARK_DATASETS.values()]


@app.get("/api/datasets/{key}", response_model=ProblemInput)
def get_dataset(key: str):
    """Retrieve full problem JSON input for a given benchmark dataset key."""
    key_lower = key.lower()
    if key_lower not in BENCHMARK_DATASETS:
        raise HTTPException(status_code=404, detail=f"Dataset '{key}' not found. Available: {list(BENCHMARK_DATASETS.keys())}")
    return BENCHMARK_DATASETS[key_lower]["generator"]()


@app.post("/api/solve", response_model=SolutionOutput)
def solve_vrp(problem: ProblemInput):
    """Run PyVRP solver on the given VRP problem instance."""
    try:
        solution = solver.solve(problem)
        return solution
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PyVRP Solver Error: {str(e)}")


@app.post("/api/generate_random", response_model=ProblemInput)
def generate_random(num_clients: int = 15, num_vehicles: int = 3, include_time_windows: bool = True):
    """Generate a random VRP problem payload."""
    return generate_random_vrp(num_clients=num_clients, num_vehicles=num_vehicles, include_time_windows=include_time_windows)
