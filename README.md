# PyVRP Vehicle Routing Problem (VRP) Optimization Platform

A production-ready Vehicle Routing Problem (VRP) optimization application powered by **PyVRP** (`pyvrp.Model`), FastAPI, and a premium modern web visualizer with Leaflet maps and Chart.js analytics.

---

## 🌟 Key Features

- **PyVRP Engine**: Solves complex VRP variants using PyVRP's high-performance Iterated Local Search (ILS) and hybrid genetic algorithm.
- **VRP Variants Supported**:
  - **CVRP**: Capacitated Vehicle Routing Problem.
  - **VRPTW**: Vehicle Routing with Time Windows & Service Durations.
  - **VRPPD**: Pickup and Delivery paired shipments.
  - **PCVRP**: Prize Collecting VRP (Optional customers with cash prizes).
  - **MDVRP**: Multi-Depot Vehicle Routing across regional hubs.
- **Constraint Handling**:
  - Vehicle fleet capacity & maximum load tracking.
  - Vehicle shift duration and maximum route distance constraints.
  - Fixed vehicle startup costs and variable distance/duration costs.
  - Time window early arrival waiting and late arrival time-warp penalty tracking.
  - Mandatory client requirements vs optional prize-collecting clients.
  - Sequential pickup and delivery shipment pairs.
- **Interactive Web Visualizer**:
  - **Route Network Map**: Leaflet map displaying depots, client stop numbers, pickup/delivery nodes, and color-coded vehicle polylines.
  - **Schedule Gantt Chart**: Visual timeline of vehicle stop activities, travel times, and wait times.
  - **Convergence Plot**: Objective function cost improvement over solver iterations.
  - **Constraint Audit**: Diagnostic summary of capacity, time window, duration, and distance adherence.
  - **JSON Problem Editor**: Live editable problem specification with instant re-solving.
- **Command Line Utility (`cli.py`)**: Terminal solver for automated runs and solution exporting.

---

## 🏗️ Project Architecture

```
vrp/
├── core/
│   ├── __init__.py
│   ├── schemas.py      # Pydantic input/output schemas & problem specifications
│   ├── solver.py       # PyVRPSolver class wrapping pyvrp.Model
│   └── datasets.py     # Pre-loaded benchmark instances (CVRP, VRPTW, VRPPD, PCVRP, MDVRP)
├── static/
│   ├── index.html      # Responsive visualizer UI
│   ├── css/styles.css  # Dark-mode HSL styling & glassmorphism theme
│   └── js/app.js       # Leaflet map & Chart.js integration
├── app.py              # FastAPI REST service & static web server
├── cli.py              # Command-line interface for running PyVRP
├── requirements.txt    # Python dependencies (pyvrp, fastapi, uvicorn, pydantic, numpy)
└── README.md           # Documentation and setup instructions
```

---

## 🚀 Setup & Installation

### 1. Environment Setup
Ensure Python 3.10+ is installed on your system.

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 💻 How to Run

### Option A: Launch Interactive Web Application

Run the FastAPI backend server with Uvicorn:

```bash
python3 -m uvicorn app:app --reload --port 8000
```

Then open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

### Option B: Run Command-Line Solver (`cli.py`)

Solve benchmark datasets directly from your terminal:

```bash
# Solve Solomon VRPTW benchmark
python3 cli.py --dataset vrptw

# Solve Capacitated VRP benchmark
python3 cli.py --dataset cvrp

# Solve Pickup & Delivery VRP benchmark
python3 cli.py --dataset vrppd

# Generate and solve a random instance with 20 customers and 5 vehicles
python3 cli.py --random --clients 20 --vehicles 5 --runtime 3.0

# Export solution payload to a JSON file
python3 cli.py --dataset vrptw --export solution.json
```

---

## 🔌 REST API Endpoints

FastAPI automatic API documentation is available at **`http://localhost:8000/docs`**.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Web application home page |
| `GET` | `/api/datasets` | List available pre-loaded benchmark datasets |
| `GET` | `/api/datasets/{key}` | Retrieve problem JSON spec for a dataset |
| `POST` | `/api/solve` | Solve custom VRP problem JSON input via PyVRP |
| `POST` | `/api/generate_random` | Generate random VRP problem JSON instance |

---

## 📄 Example Input JSON Format (`ProblemInput`)

```json
{
  "name": "Custom 2-Client VRPTW",
  "depots": [
    {
      "id": "depot_0",
      "x": 0.0,
      "y": 0.0,
      "name": "Main Depot",
      "tw_early": 0,
      "tw_late": 500
    }
  ],
  "clients": [
    {
      "id": "c1",
      "x": 10.0,
      "y": 0.0,
      "name": "Customer A",
      "delivery": 15,
      "tw_early": 20,
      "tw_late": 100,
      "service_duration": 10
    },
    {
      "id": "c2",
      "x": 0.0,
      "y": 10.0,
      "name": "Customer B",
      "delivery": 25,
      "tw_early": 50,
      "tw_late": 200,
      "service_duration": 10
    }
  ],
  "vehicle_types": [
    {
      "id": "v1",
      "name": "Van Fleet",
      "num_available": 2,
      "capacity": 50,
      "fixed_cost": 100
    }
  ],
  "config": {
    "max_runtime_seconds": 2.0,
    "seed": 42
  }
}
```

---

## 🛠️ Built With

- **[PyVRP](https://github.com/PyVRP/PyVRP)** - State-of-the-art vehicle routing problem solver library.
- **[FastAPI](https://fastapi.tiangolo.com/)** & **Uvicorn** - High-performance Python web framework.
- **[Leaflet.js](https://leafletjs.com/)** - Interactive web mapping.
- **[Chart.js](https://www.chartjs.org/)** - Responsive JavaScript charts for timeline and convergence plotting.
