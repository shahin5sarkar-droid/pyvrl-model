import math
import time
from typing import Dict, List, Tuple, Optional
import pyvrp

from core.schemas import (
    ProblemInput,
    SolutionOutput,
    RouteOutput,
    ActivityOutput,
    ConstraintViolations,
    ConvergencePoint,
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Great Circle Distance in kilometers between two lat/lon points."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(max(0.0, a)), math.sqrt(max(0.0, 1.0 - a)))
    return R * c


class PyVRPSolver:
    """
    Wrapper around PyVRP optimization engine.
    Converts ProblemInput pydantic model to PyVRP Model, executes the ILS/local search solver,
    and formats the result into detailed SolutionOutput metrics.
    """

    def solve(self, problem: ProblemInput) -> SolutionOutput:
        start_wall_time = time.time()

        # 1. Initialize PyVRP Model
        m = pyvrp.Model()

        # Keep track of location objects and ID mappings
        location_objs: List[pyvrp.Location] = []

        # 2. Add Depot Locations & Depots
        depot_objs: List[pyvrp.Depot] = []
        depot_id_map: Dict[str, pyvrp.Depot] = {}

        if not problem.depots:
            # Fallback default depot at (0, 0)
            loc_d = m.add_location(x=0.0, y=0.0, name="Depot")
            d_obj = m.add_depot(location=loc_d, tw_early=0, tw_late=86400, service_duration=0, name="Depot")
            depot_objs.append(d_obj)
        else:
            for d_spec in problem.depots:
                loc = m.add_location(x=d_spec.x, y=d_spec.y, name=d_spec.name)
                depot_obj = m.add_depot(
                    location=loc,
                    tw_early=d_spec.tw_early,
                    tw_late=d_spec.tw_late,
                    service_duration=d_spec.service_duration,
                    name=d_spec.name,
                )
                location_objs.append(loc)
                depot_objs.append(depot_obj)
                depot_id_map[d_spec.id] = depot_obj

        # 3. Add Client Locations & Clients
        client_objs: List[pyvrp.Client] = []
        client_id_map: Dict[str, pyvrp.Client] = {}
        required_client_ids: set = set()

        for c_spec in problem.clients:
            loc = m.add_location(x=c_spec.x, y=c_spec.y, name=c_spec.name)
            client_obj = m.add_client(
                location=loc,
                delivery=c_spec.delivery,
                pickup=c_spec.pickup,
                service_duration=c_spec.service_duration,
                tw_early=c_spec.tw_early,
                tw_late=c_spec.tw_late,
                release_time=c_spec.release_time,
                prize=c_spec.prize,
                required=c_spec.required,
                name=c_spec.name,
            )
            location_objs.append(loc)
            client_objs.append(client_obj)
            client_id_map[c_spec.id] = client_obj
            if c_spec.required:
                required_client_ids.add(c_spec.id)

        # 4. Add Shipment Locations & Shipments (Pickups and Deliveries)
        shipment_objs: List[pyvrp.Shipment] = []

        for s_spec in problem.shipments:
            loc_p = m.add_location(x=s_spec.pickup_x, y=s_spec.pickup_y, name=s_spec.pickup_name or f"Pickup {s_spec.id}")
            loc_d = m.add_location(x=s_spec.delivery_x, y=s_spec.delivery_y, name=s_spec.delivery_name or f"Delivery {s_spec.id}")

            shipment_obj = m.add_shipment(
                pickup_location=loc_p,
                delivery_location=loc_d,
                amount=s_spec.amount,
                pickup_tw_early=s_spec.pickup_tw_early,
                pickup_tw_late=s_spec.pickup_tw_late,
                pickup_service_duration=s_spec.pickup_service_duration,
                delivery_tw_early=s_spec.delivery_tw_early,
                delivery_tw_late=s_spec.delivery_tw_late,
                delivery_service_duration=s_spec.delivery_service_duration,
                prize=s_spec.prize,
                required=s_spec.required,
                name=s_spec.name or f"Shipment {s_spec.id}",
            )
            location_objs.append(loc_p)
            location_objs.append(loc_d)
            shipment_objs.append(shipment_obj)

        # 5. Add Vehicle Types
        vehicle_type_objs: List[pyvrp.VehicleType] = []
        total_vehicles_available = 0

        if not problem.vehicle_types:
            default_v = m.add_vehicle_type(
                num_available=5,
                capacity=100,
                start_depot=depot_objs[0],
                end_depot=depot_objs[0],
                name="Standard Fleet",
            )
            vehicle_type_objs.append(default_v)
            total_vehicles_available = 5
        else:
            for v_spec in problem.vehicle_types:
                start_dep = depot_objs[0]
                end_dep = depot_objs[0]

                v_obj = m.add_vehicle_type(
                    num_available=v_spec.num_available,
                    capacity=v_spec.capacity,
                    start_depot=start_dep,
                    end_depot=end_dep,
                    fixed_cost=v_spec.fixed_cost,
                    shift_duration=v_spec.max_duration,
                    max_distance=v_spec.max_distance,
                    unit_distance_cost=v_spec.unit_distance_cost,
                    unit_duration_cost=v_spec.unit_duration_cost,
                    name=v_spec.name,
                )
                vehicle_type_objs.append(v_obj)
                total_vehicles_available += v_spec.num_available

        # 6. Add Edges (Distance & Duration Matrices)
        all_locations = list(m.locations)
        num_locs = len(all_locations)

        matrix_spec = problem.matrix
        speed_factor = max(0.001, matrix_spec.speed_factor)
        scale_factor = matrix_spec.scale_factor

        has_custom_dist = matrix_spec.distance_matrix is not None and len(matrix_spec.distance_matrix) == num_locs
        has_custom_dur = matrix_spec.duration_matrix is not None and len(matrix_spec.duration_matrix) == num_locs

        # Detect geographic Lat/Lon coordinates
        is_geo_coords = True
        for loc in all_locations:
            if not (-180.0 <= loc.x <= 180.0 and -90.0 <= loc.y <= 90.0):
                is_geo_coords = False
                break

        for i, frm_loc in enumerate(all_locations):
            for j, to_loc in enumerate(all_locations):
                if has_custom_dist and has_custom_dur:
                    dist = int(matrix_spec.distance_matrix[i][j])
                    dur = int(matrix_spec.duration_matrix[i][j])
                elif has_custom_dist:
                    dist = int(matrix_spec.distance_matrix[i][j])
                    dur = int(dist / speed_factor)
                elif is_geo_coords and scale_factor == 1.0:
                    # Calculate real Haversine distance in Kilometers (km)
                    dist_km = haversine_km(frm_loc.y, frm_loc.x, to_loc.y, to_loc.x)
                    dist = int(round(dist_km))
                    # Assuming average driving speed 45 km/h in seconds
                    dur = int(round((dist_km / max(5.0, 45.0 * speed_factor)) * 3600))
                else:
                    # Calculate Euclidean distance
                    dx = frm_loc.x - to_loc.x
                    dy = frm_loc.y - to_loc.y
                    euc_dist = math.hypot(dx, dy)
                    dist = int(round(euc_dist * scale_factor))
                    dur = int(round(dist / speed_factor))

                m.add_edge(frm_loc, to_loc, distance=dist, duration=dur)

        # 7. Configure Solver Stopping Criterion
        cfg = problem.config
        stop_criterion = None

        if cfg.max_runtime_seconds and cfg.max_runtime_seconds > 0:
            stop_criterion = pyvrp.stop.MaxRuntime(cfg.max_runtime_seconds)
        elif cfg.max_iterations and cfg.max_iterations > 0:
            stop_criterion = pyvrp.stop.MaxIterations(cfg.max_iterations)
        else:
            stop_criterion = pyvrp.stop.MaxRuntime(3.0)

        # Execute PyVRP ILS Solver
        pyvrp_result = m.solve(stop=stop_criterion, seed=cfg.seed)
        elapsed_time = round(time.time() - start_wall_time, 4)

        # 8. Extract Solution Outputs & Metrics
        best_sol = pyvrp_result.best
        data = m.data()

        routes_output: List[RouteOutput] = []
        total_distance = 0
        total_duration = 0
        total_cost = pyvrp_result.cost() if pyvrp_result.cost() != float("inf") else 0

        visited_client_ids: set = set()
        visited_optional_clients = 0
        prizes_collected = 0
        shipments_delivered_count = 0

        capacity_violations = 0
        time_window_violations = 0
        duration_violations = 0
        distance_violations = 0
        violation_details: List[str] = []

        active_routes_count = len(best_sol.routes())

        for r_idx, route in enumerate(best_sol.routes()):
            r_dist = route.distance()
            r_dur = route.duration()
            r_travel_dur = route.travel_duration()
            r_serv_dur = route.service_duration()
            r_wait_dur = route.wait_duration()
            r_time_warp = route.time_warp()
            r_prizes = route.prizes()

            r_del_list = route.delivery()
            r_del_amount = r_del_list[0] if isinstance(r_del_list, list) else r_del_list

            total_distance += r_dist
            total_duration += r_dur
            prizes_collected += r_prizes

            # Check route-level violations
            if route.has_excess_load():
                capacity_violations += 1
                violation_details.append(f"Route {r_idx + 1}: Excess load of {route.excess_load()} units.")

            if route.has_excess_distance():
                distance_violations += 1
                violation_details.append(f"Route {r_idx + 1}: Distance limit exceeded.")

            if route.has_time_warp():
                time_window_violations += 1
                violation_details.append(f"Route {r_idx + 1}: Time window violation (time warp = {r_time_warp}).")

            # Extract stop activities
            activities_output: List[ActivityOutput] = []
            curr_load = r_del_amount  # Start with total initial delivery load
            route_pickup = 0
            route_delivery = 0
            max_load_on_route = curr_load

            for seq_idx, act in enumerate(route):
                loc_idx = act.idx
                act_type_str = str(act.type).replace("ActivityType.", "")

                loc_name = ""
                loc_id = f"loc_{loc_idx}"
                x_coord, y_coord = 0.0, 0.0

                load_change = 0

                if act.is_depot():
                    dep_obj = data.depot(loc_idx)
                    loc_obj = data.location(dep_obj.location)
                    loc_name = dep_obj.name or loc_obj.name or f"Depot {loc_idx}"
                    loc_id = f"depot_{loc_idx}"
                    x_coord, y_coord = loc_obj.x, loc_obj.y
                elif act.is_client():
                    cli_obj = data.client(loc_idx)
                    loc_obj = data.location(cli_obj.location)
                    loc_name = cli_obj.name or loc_obj.name or f"Client {loc_idx}"
                    loc_id = f"client_{loc_idx}"
                    x_coord, y_coord = loc_obj.x, loc_obj.y

                    c_del = cli_obj.delivery[0] if isinstance(cli_obj.delivery, list) else cli_obj.delivery
                    c_pic = cli_obj.pickup[0] if isinstance(cli_obj.pickup, list) else cli_obj.pickup

                    load_change = c_pic - c_del
                    route_delivery += c_del
                    route_pickup += c_pic

                    if loc_idx < len(problem.clients):
                        c_spec = problem.clients[loc_idx]
                        loc_id = c_spec.id
                        visited_client_ids.add(c_spec.id)
                        if not c_spec.required:
                            visited_optional_clients += 1

                elif act.is_shipment():
                    shipment_idx = act.idx
                    ship_obj = data.shipment(shipment_idx)
                    ship_amt = ship_obj.amount[0] if isinstance(ship_obj.amount, list) else ship_obj.amount
                    if act.is_pickup():
                        loc_obj = data.location(ship_obj.pickup.location)
                        loc_name = loc_obj.name or f"Pickup {shipment_idx}"
                        loc_id = f"pickup_{shipment_idx}"
                        x_coord, y_coord = loc_obj.x, loc_obj.y
                        load_change = ship_amt
                        route_pickup += ship_amt
                    else:
                        loc_obj = data.location(ship_obj.delivery.location)
                        loc_name = loc_obj.name or f"Delivery {shipment_idx}"
                        loc_id = f"delivery_{shipment_idx}"
                        x_coord, y_coord = loc_obj.x, loc_obj.y
                        load_change = -ship_amt
                        route_delivery += ship_amt
                        shipments_delivered_count += 1

                if not act.is_depot() or seq_idx > 0:
                    curr_load += load_change

                if curr_load > max_load_on_route:
                    max_load_on_route = curr_load

                start_dep_loc = data.location(data.depot(route.start_depot()).location)
                end_dep_loc = data.location(data.depot(route.end_depot()).location)

                start_dep_name = data.depot(route.start_depot()).name or start_dep_loc.name or "Depot"
                end_dep_name = data.depot(route.end_depot()).name or end_dep_loc.name or "Depot"

                activities_output.append(
                    ActivityOutput(
                        sequence_index=seq_idx,
                        activity_type=act_type_str,
                        location_id=loc_id,
                        location_name=loc_name,
                        x=x_coord,
                        y=y_coord,
                        start_time=act.start_time,
                        end_time=act.end_time,
                        service_duration=act.duration,
                        wait_duration=act.wait_duration,
                        time_warp=act.time_warp,
                        load_change=load_change,
                        current_load=max(0, curr_load),
                    )
                )

            # Get capacity of vehicle type
            v_type = route.vehicle_type()
            v_capacity = data.vehicle_type(v_type).capacity[0] if isinstance(data.vehicle_type(v_type).capacity, list) else data.vehicle_type(v_type).capacity
            v_utilization = round((max_load_on_route / max(1, v_capacity)) * 100, 1)

            routes_output.append(
                RouteOutput(
                    route_id=r_idx + 1,
                    vehicle_type_name=f"Vehicle Type {v_type + 1}",
                    start_depot_name=start_dep_name,
                    end_depot_name=end_dep_name,
                    num_stops=len(route) - 2 if len(route) >= 2 else 0,
                    distance=r_dist,
                    duration=r_dur,
                    travel_duration=r_travel_dur,
                    service_duration=r_serv_dur,
                    wait_duration=r_wait_dur,
                    time_warp=r_time_warp,
                    total_pickup=route_pickup,
                    total_delivery=route_delivery,
                    max_load=max_load_on_route,
                    capacity=v_capacity,
                    capacity_utilization_pct=v_utilization,
                    cost=route.distance_cost() + route.duration_cost() + route.fixed_vehicle_cost(),
                    activities=activities_output,
                )
            )

        # Unvisited clients logic
        unvisited_client_ids = [c.id for c in problem.clients if c.id not in visited_client_ids]
        unvisited_required = [c.id for c in problem.clients if c.required and c.id not in visited_client_ids]
        if unvisited_required:
            unvisited_required_clients_cnt = len(unvisited_required)
            violation_details.append(f"Unvisited required clients ({unvisited_required_clients_cnt}): {', '.join(unvisited_required)}")
        else:
            unvisited_required_clients_cnt = 0

        # Fleet utilization
        fleet_util_pct = round((active_routes_count / max(1, total_vehicles_available)) * 100, 1)

        # Convergence points sample
        convergence_points: List[ConvergencePoint] = []
        if hasattr(pyvrp_result.stats, "runtimes") and pyvrp_result.stats.runtimes:
            cum_time = 0.0
            best_c = pyvrp_result.cost() if pyvrp_result.cost() != float("inf") else 0
            for it, rt in enumerate(pyvrp_result.stats.runtimes[:50]):
                cum_time += rt
                convergence_points.append(
                    ConvergencePoint(
                        iteration=(it + 1) * max(1, pyvrp_result.stats.num_iterations // 50),
                        time_seconds=round(cum_time, 5),
                        best_cost=best_c,
                    )
                )

        violations = ConstraintViolations(
            capacity_violations=capacity_violations,
            time_window_violations=time_window_violations,
            duration_violations=duration_violations,
            distance_violations=distance_violations,
            unvisited_required_clients=unvisited_required_clients_cnt,
            details=violation_details,
        )

        total_optional = len([c for c in problem.clients if not c.required])

        return SolutionOutput(
            problem_name=problem.name,
            is_feasible=pyvrp_result.is_feasible(),
            total_cost=int(total_cost),
            total_distance=total_distance,
            total_duration=total_duration,
            vehicles_used=active_routes_count,
            total_vehicles_available=total_vehicles_available,
            fleet_utilization_pct=fleet_util_pct,
            clients_visited=len(visited_client_ids),
            total_clients=len(problem.clients),
            optional_clients_visited=visited_optional_clients,
            total_optional_clients=total_optional,
            shipments_delivered=shipments_delivered_count,
            total_shipments=len(problem.shipments),
            prizes_collected=prizes_collected,
            solve_runtime_seconds=elapsed_time,
            iterations_run=pyvrp_result.stats.num_iterations if hasattr(pyvrp_result.stats, "num_iterations") else 0,
            constraint_violations=violations,
            routes=routes_output,
            unvisited_client_ids=unvisited_client_ids,
            convergence=convergence_points,
            pyvrp_version=getattr(pyvrp, "__version__", "0.14.0"),
        )
