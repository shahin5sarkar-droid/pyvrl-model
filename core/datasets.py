import json
import os
import random
from typing import Dict, List
from core.schemas import (
    ProblemInput,
    DepotSpec,
    ClientSpec,
    ShipmentSpec,
    VehicleTypeSpec,
    MatrixSpec,
    SolverConfig,
    DatasetInfo,
)


def get_cvrp_sample() -> ProblemInput:
    """Capacitated Vehicle Routing Problem (CVRP) Sample."""
    depot = DepotSpec(id="depot_0", x=50.0, y=50.0, name="Central Logistics Hub")

    clients = [
        ClientSpec(id="c1", x=20.0, y=80.0, name="Customer Alpha", delivery=15),
        ClientSpec(id="c2", x=30.0, y=70.0, name="Customer Beta", delivery=20),
        ClientSpec(id="c3", x=70.0, y=85.0, name="Customer Gamma", delivery=25),
        ClientSpec(id="c4", x=80.0, y=60.0, name="Customer Delta", delivery=10),
        ClientSpec(id="c5", x=90.0, y=40.0, name="Customer Epsilon", delivery=30),
        ClientSpec(id="c6", x=85.0, y=20.0, name="Customer Zeta", delivery=15),
        ClientSpec(id="c7", x=60.0, y=10.0, name="Customer Eta", delivery=10),
        ClientSpec(id="c8", x=40.0, y=15.0, name="Customer Theta", delivery=22),
        ClientSpec(id="c9", x=15.0, y=30.0, name="Customer Iota", delivery=18),
        ClientSpec(id="c10", x=10.0, y=55.0, name="Customer Kappa", delivery=12),
        ClientSpec(id="c11", x=45.0, y=65.0, name="Customer Lambda", delivery=14),
        ClientSpec(id="c12", x=65.0, y=45.0, name="Customer Mu", delivery=28),
    ]

    vehicles = [
        VehicleTypeSpec(
            id="v1",
            name="Standard Delivery Truck",
            num_available=4,
            capacity=60,
            fixed_cost=100,
            unit_distance_cost=1,
        )
    ]

    return ProblemInput(
        name="Solomon CVRP-12 Instance",
        description="Capacitated Vehicle Routing Problem with 12 clients, 1 central depot, and 4 delivery trucks (Capacity: 60).",
        depots=[depot],
        clients=clients,
        vehicle_types=vehicles,
        matrix=MatrixSpec(speed_factor=1.0, scale_factor=1.0),
        config=SolverConfig(max_runtime_seconds=2.0, max_iterations=2000, seed=42),
    )


def get_vrptw_sample() -> ProblemInput:
    """Vehicle Routing Problem with Time Windows (VRPTW) Sample."""
    depot = DepotSpec(id="depot_0", x=40.0, y=50.0, name="Distribution Hub", tw_early=0, tw_late=500)

    clients = [
        ClientSpec(id="c1", x=22.0, y=75.0, name="Client Apex", delivery=10, service_duration=10, tw_early=30, tw_late=150),
        ClientSpec(id="c2", x=35.0, y=85.0, name="Client Beacon", delivery=15, service_duration=15, tw_early=100, tw_late=250),
        ClientSpec(id="c3", x=65.0, y=75.0, name="Client Crest", delivery=12, service_duration=10, tw_early=80, tw_late=200),
        ClientSpec(id="c4", x=75.0, y=55.0, name="Client Direct", delivery=8, service_duration=10, tw_early=150, tw_late=320),
        ClientSpec(id="c5", x=70.0, y=30.0, name="Client Echo", delivery=20, service_duration=15, tw_early=200, tw_late=400),
        ClientSpec(id="c6", x=50.0, y=20.0, name="Client Focus", delivery=14, service_duration=10, tw_early=120, tw_late=300),
        ClientSpec(id="c7", x=30.0, y=15.0, name="Client Gateway", delivery=18, service_duration=12, tw_early=50, tw_late=180),
        ClientSpec(id="c8", x=15.0, y=40.0, name="Client Horizon", delivery=10, service_duration=10, tw_early=40, tw_late=220),
        ClientSpec(id="c9", x=45.0, y=60.0, name="Client Zenith", delivery=16, service_duration=10, tw_early=60, tw_late=180),
        ClientSpec(id="c10", x=55.0, y=40.0, name="Client Vanguard", delivery=11, service_duration=10, tw_early=140, tw_late=350),
    ]

    vehicles = [
        VehicleTypeSpec(
            id="v1",
            name="Timed Courier Van",
            num_available=3,
            capacity=50,
            fixed_cost=150,
            max_duration=450,
            unit_distance_cost=1,
            unit_duration_cost=1,
        )
    ]

    return ProblemInput(
        name="Solomon VRPTW-10 Instance",
        description="Vehicle Routing Problem with strict Time Windows, service durations, and fleet shift limits.",
        depots=[depot],
        clients=clients,
        vehicle_types=vehicles,
        matrix=MatrixSpec(speed_factor=1.0, scale_factor=1.0),
        config=SolverConfig(max_runtime_seconds=2.0, max_iterations=2000, seed=42),
    )


def get_vrppd_sample() -> ProblemInput:
    """Pickup and Delivery Vehicle Routing Problem (VRPPD) Sample."""
    depot = DepotSpec(id="depot_0", x=50.0, y=50.0, name="Central Depot")

    shipments = [
        ShipmentSpec(
            id="s1",
            pickup_x=20.0,
            pickup_y=80.0,
            pickup_name="Supplier A (Electronics)",
            delivery_x=75.0,
            delivery_y=85.0,
            delivery_name="Retailer A (TechStore)",
            amount=15,
            pickup_service_duration=10,
            delivery_service_duration=10,
        ),
        ShipmentSpec(
            id="s2",
            pickup_x=85.0,
            pickup_y=60.0,
            pickup_name="Supplier B (Apparel)",
            delivery_x=25.0,
            delivery_y=25.0,
            delivery_name="Mall Outlet B",
            amount=20,
            pickup_service_duration=10,
            delivery_service_duration=10,
        ),
        ShipmentSpec(
            id="s3",
            pickup_x=15.0,
            pickup_y=45.0,
            pickup_name="Supplier C (Hardware)",
            delivery_x=80.0,
            delivery_y=20.0,
            delivery_name="Factory C",
            amount=12,
            pickup_service_duration=10,
            delivery_service_duration=10,
        ),
        ShipmentSpec(
            id="s4",
            pickup_x=60.0,
            pickup_y=15.0,
            pickup_name="Warehouse D",
            delivery_x=40.0,
            delivery_y=85.0,
            delivery_name="Distribution Center D",
            amount=18,
            pickup_service_duration=10,
            delivery_service_duration=10,
        ),
    ]

    vehicles = [
        VehicleTypeSpec(
            id="v1",
            name="Freight Truck",
            num_available=2,
            capacity=40,
            fixed_cost=200,
            unit_distance_cost=1,
        )
    ]

    return ProblemInput(
        name="VRPPD Paired Shipments Instance",
        description="Pickup and Delivery problem with 4 paired shipments requiring sequential pickup and delivery on the same vehicle route.",
        depots=[depot],
        shipments=shipments,
        vehicle_types=vehicles,
        matrix=MatrixSpec(speed_factor=1.0, scale_factor=1.0),
        config=SolverConfig(max_runtime_seconds=3.0, max_iterations=2000, seed=42),
    )


def get_pcvrp_sample() -> ProblemInput:
    """Prize Collecting / Optional Customers VRP (PCVRP) Sample."""
    depot = DepotSpec(id="depot_0", x=50.0, y=50.0, name="Central Logistics Hub")

    clients = [
        # Required core clients
        ClientSpec(id="c1", x=40.0, y=60.0, name="Core Client 1", delivery=10, required=True),
        ClientSpec(id="c2", x=60.0, y=60.0, name="Core Client 2", delivery=10, required=True),
        ClientSpec(id="c3", x=50.0, y=35.0, name="Core Client 3", delivery=15, required=True),
        # Optional high-value clients
        ClientSpec(id="c4", x=15.0, y=85.0, name="Optional Outlier North (High Prize)", delivery=5, prize=500, required=False),
        ClientSpec(id="c5", x=85.0, y=85.0, name="Optional Outlier East (Medium Prize)", delivery=5, prize=250, required=False),
        ClientSpec(id="c6", x=90.0, y=15.0, name="Optional Far East (Low Prize)", delivery=5, prize=50, required=False),
        ClientSpec(id="c7", x=10.0, y=15.0, name="Optional Far West (High Prize)", delivery=5, prize=450, required=False),
        ClientSpec(id="c8", x=45.0, y=75.0, name="Optional Nearby North (High Prize)", delivery=5, prize=300, required=False),
        ClientSpec(id="c9", x=55.0, y=25.0, name="Optional Nearby South (High Prize)", delivery=5, prize=350, required=False),
    ]

    vehicles = [
        VehicleTypeSpec(
            id="v1",
            name="Prize Collector Truck",
            num_available=2,
            capacity=35,
            fixed_cost=100,
            unit_distance_cost=2,
        )
    ]

    return ProblemInput(
        name="Prize Collecting VRP (Optional Customers)",
        description="VRP instance with required core customers and optional distant customers offering cash prizes for selection.",
        depots=[depot],
        clients=clients,
        vehicle_types=vehicles,
        matrix=MatrixSpec(speed_factor=1.0, scale_factor=1.0),
        config=SolverConfig(max_runtime_seconds=2.0, max_iterations=2000, seed=42),
    )


def get_multidepot_sample() -> ProblemInput:
    """Multi-Depot Vehicle Routing Problem Sample."""
    depots = [
        DepotSpec(id="depot_north", x=30.0, y=80.0, name="North Logistics Depot"),
        DepotSpec(id="depot_south", x=70.0, y=20.0, name="South Logistics Depot"),
    ]

    clients = [
        ClientSpec(id="c1", x=20.0, y=90.0, name="North Retail A", delivery=10),
        ClientSpec(id="c2", x=40.0, y=85.0, name="North Retail B", delivery=12),
        ClientSpec(id="c3", x=15.0, y=70.0, name="North Retail C", delivery=15),
        ClientSpec(id="c4", x=35.0, y=65.0, name="Central Commercial D", delivery=14),
        ClientSpec(id="c5", x=55.0, y=55.0, name="Central Commercial E", delivery=18),
        ClientSpec(id="c6", x=65.0, y=35.0, name="South Industrial F", delivery=10),
        ClientSpec(id="c7", x=80.0, y=30.0, name="South Industrial G", delivery=16),
        ClientSpec(id="c8", x=85.0, y=10.0, name="South Industrial H", delivery=12),
        ClientSpec(id="c9", x=60.0, y=15.0, name="South Industrial I", delivery=14),
    ]

    vehicles = [
        VehicleTypeSpec(
            id="v_north",
            name="North Fleet Truck",
            num_available=2,
            capacity=40,
            fixed_cost=100,
            unit_distance_cost=1,
        ),
        VehicleTypeSpec(
            id="v_south",
            name="South Fleet Truck",
            num_available=2,
            capacity=40,
            fixed_cost=100,
            unit_distance_cost=1,
        ),
    ]

    return ProblemInput(
        name="Multi-Depot VRP Instance",
        description="Multi-depot problem with 2 distinct regional depots servicing 9 clients across North and South sectors.",
        depots=depots,
        clients=clients,
        vehicle_types=vehicles,
        matrix=MatrixSpec(speed_factor=1.0, scale_factor=1.0),
        config=SolverConfig(max_runtime_seconds=2.0, max_iterations=2000, seed=42),
    )


def get_nyc_sample() -> ProblemInput:
    """Real-World NYC Last-Mile Delivery Instance."""
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "real_life_data_nyc.json")
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            raw = json.load(f)
            return ProblemInput(**raw)
    raise FileNotFoundError(f"NYC data file not found at {data_path}")


def get_northeast_sample() -> ProblemInput:
    """Real-World US Northeast Interstate Freight Instance."""
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "real_life_data_northeast.json")
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            raw = json.load(f)
            return ProblemInput(**raw)
    raise FileNotFoundError(f"Northeast data file not found at {data_path}")


def get_ne_india_sample() -> ProblemInput:
    """Real-World Northeast India Interstate Freight Instance."""
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "real_life_data_northeast_india.json")
    if os.path.exists(data_path):
        with open(data_path, "r") as f:
            raw = json.load(f)
            return ProblemInput(**raw)
    raise FileNotFoundError(f"Northeast India data file not found at {data_path}")


BENCHMARK_DATASETS: Dict[str, dict] = {
    "ne_india_real": {
        "info": DatasetInfo(
            key="ne_india_real",
            name="🇮🇳 Real-Life Northeast India Supply Chain",
            category="Real-World",
            description="Real Northeast India regional distribution across 8 states: Guwahati Hub servicing Shillong, Agartala, Imphal, Aizawl, Kohima, Itanagar, Gangtok, Dibrugarh & Silchar.",
            num_depots=2,
            num_clients=12,
            num_shipments=0,
            num_vehicles=4,
        ),
        "generator": get_ne_india_sample,
    },
    "northeast_real": {
        "info": DatasetInfo(
            key="northeast_real",
            name="🗺️ Real-Life US Northeast Freight Hub",
            category="Real-World",
            description="Real US Northeast regional interstate logistics: Newark NJ & Boston MA hubs servicing 15 major cities (NYC, Philly, Baltimore, DC, Hartford, Providence, Albany).",
            num_depots=2,
            num_clients=15,
            num_shipments=0,
            num_vehicles=5,
        ),
        "generator": get_northeast_sample,
    },
    "nyc_real": {
        "info": DatasetInfo(
            key="nyc_real",
            name="🗽 Real-Life NYC E-Commerce Fleet",
            category="Real-World",
            description="Real-world NYC distribution: 1 LIC Fulfillment Center servicing 12 retail stops across Manhattan & Brooklyn.",
            num_depots=1,
            num_clients=12,
            num_shipments=0,
            num_vehicles=3,
        ),
        "generator": get_nyc_sample,
    },
    "vrptw": {
        "info": DatasetInfo(
            key="vrptw",
            name="VRPTW (Time Windows)",
            category="VRPTW",
            description="Vehicle Routing with strict Time Windows and service durations.",
            num_depots=1,
            num_clients=10,
            num_shipments=0,
            num_vehicles=3,
        ),
        "generator": get_vrptw_sample,
    },
    "cvrp": {
        "info": DatasetInfo(
            key="cvrp",
            name="CVRP (Solomon 12-Client)",
            category="CVRP",
            description="Classic Capacitated Vehicle Routing Problem with demand capacity constraints.",
            num_depots=1,
            num_clients=12,
            num_shipments=0,
            num_vehicles=4,
        ),
        "generator": get_cvrp_sample,
    },
    "vrppd": {
        "info": DatasetInfo(
            key="vrppd",
            name="VRPPD (Pickup & Delivery)",
            category="VRPPD",
            description="Pickup and Delivery VRP with paired shipment pick-ups and drop-offs.",
            num_depots=1,
            num_clients=0,
            num_shipments=4,
            num_vehicles=2,
        ),
        "generator": get_vrppd_sample,
    },
    "pcvrp": {
        "info": DatasetInfo(
            key="pcvrp",
            name="Prize Collecting VRP",
            category="PCVRP",
            description="VRP with mandatory core clients and optional prize-collecting clients.",
            num_depots=1,
            num_clients=9,
            num_shipments=0,
            num_vehicles=2,
        ),
        "generator": get_pcvrp_sample,
    },
    "multidepot": {
        "info": DatasetInfo(
            key="multidepot",
            name="Multi-Depot VRP",
            category="MDVRP",
            description="Multi-depot routing problem across 2 regional logistics hubs.",
            num_depots=2,
            num_clients=9,
            num_shipments=0,
            num_vehicles=4,
        ),
        "generator": get_multidepot_sample,
    },
}


def generate_random_vrp(num_clients: int = 15, num_vehicles: int = 3, include_time_windows: bool = True) -> ProblemInput:
    """Generate a custom random VRP problem payload."""
    rng = random.Random(random.randint(1, 10000))

    depot = DepotSpec(id="depot_0", x=50.0, y=50.0, name="Central Hub", tw_early=0, tw_late=600)

    clients: List[ClientSpec] = []
    for i in range(1, num_clients + 1):
        cx = round(rng.uniform(10.0, 90.0), 1)
        cy = round(rng.uniform(10.0, 90.0), 1)
        deliv = rng.randint(5, 20)
        serv = rng.choice([5, 10, 15])

        if include_time_windows:
            tw_e = rng.randint(20, 250)
            tw_l = tw_e + rng.randint(80, 200)
        else:
            tw_e = 0
            tw_l = 600

        clients.append(
            ClientSpec(
                id=f"c{i}",
                x=cx,
                y=cy,
                name=f"Customer {i}",
                delivery=deliv,
                service_duration=serv,
                tw_early=tw_e,
                tw_late=tw_l,
            )
        )

    vehicles = [
        VehicleTypeSpec(
            id="v1",
            name="Delivery Fleet",
            num_available=num_vehicles,
            capacity=rng.randint(45, 75),
            fixed_cost=100,
            unit_distance_cost=1,
        )
    ]

    return ProblemInput(
        name=f"Random VRP ({num_clients} Clients, {num_vehicles} Vehicles)",
        description=f"Generated random VRP instance with {num_clients} clients.",
        depots=[depot],
        clients=clients,
        vehicle_types=vehicles,
        matrix=MatrixSpec(speed_factor=1.0, scale_factor=1.0),
        config=SolverConfig(max_runtime_seconds=3.0, max_iterations=2000, seed=42),
    )
