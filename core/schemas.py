from typing import List, Optional, Any
from pydantic import BaseModel, Field


class LocationSpec(BaseModel):
    x: float
    y: float
    name: str = ""


class DepotSpec(BaseModel):
    id: str = "depot_0"
    x: float
    y: float
    name: str = "Depot"
    tw_early: int = 0
    tw_late: int = 86400  # Default 24 hours in seconds (or time units)
    service_duration: int = 0


class ClientSpec(BaseModel):
    id: str
    x: float
    y: float
    name: str = ""
    delivery: int = 0
    pickup: int = 0
    service_duration: int = 0
    tw_early: int = 0
    tw_late: int = 86400
    release_time: int = 0
    prize: int = 0
    required: bool = True


class ShipmentSpec(BaseModel):
    id: str
    pickup_x: float
    pickup_y: float
    pickup_name: str = ""
    delivery_x: float
    delivery_y: float
    delivery_name: str = ""
    amount: int = 1
    pickup_tw_early: int = 0
    pickup_tw_late: int = 86400
    pickup_service_duration: int = 0
    delivery_tw_early: int = 0
    delivery_tw_late: int = 86400
    delivery_service_duration: int = 0
    prize: int = 0
    required: bool = True
    name: str = ""


class VehicleTypeSpec(BaseModel):
    id: str = "vehicle_type_0"
    name: str = "Standard Van"
    num_available: int = 3
    capacity: int = 100
    fixed_cost: int = 0
    max_duration: int = 86400
    max_distance: int = 1000000
    unit_distance_cost: int = 1
    unit_duration_cost: int = 0


class MatrixSpec(BaseModel):
    speed_factor: float = 1.0  # Speed in distance units per time unit
    scale_factor: float = 1.0  # Scaling multiplier for distance matrix
    distance_matrix: Optional[List[List[int]]] = None
    duration_matrix: Optional[List[List[int]]] = None


class SolverConfig(BaseModel):
    max_runtime_seconds: Optional[float] = 3.0
    max_iterations: Optional[int] = 2000
    seed: int = 42


class ProblemInput(BaseModel):
    name: str = "VRP Problem Instance"
    description: str = ""
    depots: List[DepotSpec] = Field(default_factory=list)
    clients: List[ClientSpec] = Field(default_factory=list)
    shipments: List[ShipmentSpec] = Field(default_factory=list)
    vehicle_types: List[VehicleTypeSpec] = Field(default_factory=list)
    matrix: MatrixSpec = Field(default_factory=MatrixSpec)
    config: SolverConfig = Field(default_factory=SolverConfig)


class ActivityOutput(BaseModel):
    sequence_index: int
    activity_type: str  # DEPOT, CLIENT, PICKUP, DELIVERY
    location_id: str
    location_name: str
    x: float
    y: float
    start_time: int
    end_time: int
    service_duration: int
    wait_duration: int
    time_warp: int
    load_change: int
    current_load: int


class RouteOutput(BaseModel):
    route_id: int
    vehicle_type_name: str
    start_depot_name: str
    end_depot_name: str
    num_stops: int
    distance: int
    duration: int
    travel_duration: int
    service_duration: int
    wait_duration: int
    time_warp: int
    total_pickup: int
    total_delivery: int
    max_load: int
    capacity: int
    capacity_utilization_pct: float
    cost: int
    activities: List[ActivityOutput]


class ConstraintViolations(BaseModel):
    capacity_violations: int = 0
    time_window_violations: int = 0
    duration_violations: int = 0
    distance_violations: int = 0
    unvisited_required_clients: int = 0
    details: List[str] = Field(default_factory=list)


class ConvergencePoint(BaseModel):
    iteration: int
    time_seconds: float
    best_cost: float


class SolutionOutput(BaseModel):
    problem_name: str
    is_feasible: bool
    total_cost: int
    total_distance: int
    total_duration: int
    vehicles_used: int
    total_vehicles_available: int
    fleet_utilization_pct: float
    clients_visited: int
    total_clients: int
    optional_clients_visited: int
    total_optional_clients: int
    shipments_delivered: int
    total_shipments: int
    prizes_collected: int
    solve_runtime_seconds: float
    iterations_run: int
    constraint_violations: ConstraintViolations
    routes: List[RouteOutput]
    unvisited_client_ids: List[str]
    convergence: List[ConvergencePoint]
    pyvrp_version: str


class DatasetInfo(BaseModel):
    key: str
    name: str
    category: str
    description: str
    num_depots: int
    num_clients: int
    num_shipments: int
    num_vehicles: int
