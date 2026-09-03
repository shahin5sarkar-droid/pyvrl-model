#!/usr/bin/env python3
"""
PyVRP Optimization Model CLI Interface.
Command-line runner for PyVRP vehicle routing solver.
"""
import sys
import json
import argparse
from core.datasets import BENCHMARK_DATASETS, generate_random_vrp
from core.solver import PyVRPSolver


def main():
    parser = argparse.ArgumentParser(description="PyVRP Vehicle Routing Optimization Solver CLI")
    parser.add_argument(
        "--dataset",
        type=str,
        default="vrptw",
        choices=list(BENCHMARK_DATASETS.keys()),
        help="Pre-loaded benchmark dataset to solve (default: vrptw)",
    )
    parser.add_argument(
        "--random",
        action="store_true",
        help="Generate and solve a random VRP instance",
    )
    parser.add_argument(
        "--clients",
        type=int,
        default=15,
        help="Number of clients for random instance (default: 15)",
    )
    parser.add_argument(
        "--vehicles",
        type=int,
        default=3,
        help="Number of vehicles for random instance (default: 3)",
    )
    parser.add_argument(
        "--runtime",
        type=float,
        default=3.0,
        help="Maximum solver runtime in seconds (default: 3.0)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=2000,
        help="Maximum solver iterations",
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Save solution JSON output to specified file path",
    )

    args = parser.parse_args()

    if args.random:
        print(f"\n🎲 Generating random VRP instance with {args.clients} clients and {args.vehicles} vehicles...")
        problem = generate_random_vrp(num_clients=args.clients, num_vehicles=args.vehicles)
    else:
        print(f"\n📂 Loading benchmark dataset: '{args.dataset}' ({BENCHMARK_DATASETS[args.dataset]['info'].name})...")
        problem = BENCHMARK_DATASETS[args.dataset]["generator"]()

    # Override solver config if specified
    if args.runtime:
        problem.config.max_runtime_seconds = args.runtime
    if args.iterations:
        problem.config.max_iterations = args.iterations

    print(f"🚀 Running PyVRP Solver ({problem.config.max_runtime_seconds}s limit, seed {problem.config.seed})...\n")

    solver = PyVRPSolver()
    solution = solver.solve(problem)

    # Display Terminal Summary
    print("=" * 70)
    print(f"  PyVRP SOLUTION SUMMARY: {solution.problem_name}")
    print("=" * 70)
    print(f" Status:             {'FEASIBLE ✅' if solution.is_feasible else 'INFEASIBLE ❌'}")
    print(f" Total Objective Cost: {solution.total_cost:,}")
    print(f" Total Distance:     {solution.total_distance:,} units")
    print(f" Total Duration:     {solution.total_duration:,} time units")
    print(f" Vehicles Used:      {solution.vehicles_used} / {solution.total_vehicles_available} ({solution.fleet_utilization_pct}% utilization)")
    print(f" Clients Visited:    {solution.clients_visited} / {solution.total_clients}")
    if solution.total_optional_clients > 0:
        print(f" Optional Clients:   {solution.optional_clients_visited} / {solution.total_optional_clients} visited (Prizes: {solution.prizes_collected})")
    if solution.total_shipments > 0:
        print(f" Shipments Delivered:{solution.shipments_delivered} / {solution.total_shipments}")
    print(f" Solver Runtime:     {solution.solve_runtime_seconds} seconds ({solution.iterations_run:,} iterations)")
    print(f" PyVRP Engine:       v{solution.pyvrp_version}")
    print("-" * 70)

    # Route breakdown
    print("\n📦 ROUTE DETAILS:")
    for r in solution.routes:
        print(f"\n 🚚 Route #{r.route_id} [{r.vehicle_type_name}] ({r.start_depot_name} ➔ {r.end_depot_name})")
        print(f"    Stops: {r.num_stops} | Distance: {r.distance} | Duration: {r.duration} | Max Load: {r.max_load}/{r.capacity} ({r.capacity_utilization_pct}%)")
        print("    Sequence:")
        for act in r.activities:
            type_tag = f"[{act.activity_type}]"
            time_str = f"Time {act.start_time}->{act.end_time}"
            load_str = f"Load {act.current_load}"
            print(f"      {act.sequence_index}. {type_tag:<10} {act.location_name:<25} ({time_str}, {load_str})")

    # Constraint Audit
    violations = solution.constraint_violations
    print("\n🔍 CONSTRAINT AUDIT:")
    if solution.is_feasible and not violations.details:
        print("  ✅ All constraints satisfied cleanly (Capacity, Distance, Time Windows, Mandatory Clients).")
    else:
        print(f"  ⚠️ Capacity Violations:     {violations.capacity_violations}")
        print(f"  ⚠️ Time Window Violations:  {violations.time_window_violations}")
        print(f"  ⚠️ Duration Violations:     {violations.duration_violations}")
        for det in violations.details:
            print(f"     - {det}")

    print("=" * 70)

    # Save to JSON file if requested
    if args.export:
        with open(args.export, "w") as f:
            f.write(solution.model_dump_json(indent=2))
        print(f"\n💾 Solution output successfully exported to: {args.export}")


if __name__ == "__main__":
    main()
