"""
Interactive Demo Script for Map Servers

This script demonstrates all capabilities of the EV Charging and Transit/POI map servers.
It can run in interactive mode with the OpenAI agent or in demo mode to showcase features.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from servers.ev_charging_server import EVChargingServer
from servers.transit_poi_server import TransitPOIServer


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_json(data: dict, indent: int = 2):
    """Print formatted JSON data."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def demo_ev_charging_server():
    """Demonstrate EV Charging Server capabilities."""
    print_section("EV CHARGING & FUEL MAP SERVER DEMO")

    server = EVChargingServer()

    # Demo 1: Find nearby charging stations
    print("\n1. FINDING NEARBY CHARGING STATIONS")
    print("-" * 70)
    print("Scenario: Looking for charging stations near AUB Beirut")
    print("Location: 33.9018,35.4787 (AUB)")
    print("Filter: CCS connectors only")
    print("Radius: 10 km\n")

    result = server.nearby_charging_stations(
        location="33.9018,35.4787",
        connector_type="CCS",
        radius_km=10
    )
    print_json(result)

    # Demo 2: Plan charging route
    print("\n\n2. PLANNING CHARGING ROUTE")
    print("-" * 70)
    print("Scenario: EV road trip from Beirut to Tripoli")
    print("Origin: 33.8938,35.5018 (Beirut)")
    print("Destination: 34.4364,35.8211 (Tripoli)")
    print("Battery Range: 50 km (to demonstrate charging stops)\n")

    result = server.plan_charging_route(
        origin="33.8938,35.5018",
        destination="34.4364,35.8211",
        battery_range_km=50
    )
    print_json(result)

    # Demo 3: Compare energy costs
    print("\n\n3. COMPARING ENERGY COSTS (EV vs GAS)")
    print("-" * 70)
    print("Scenario: Cost comparison for Beirut to Sidon trip")
    print("Origin: 33.8938,35.5018 (Beirut)")
    print("Destination: 33.5631,35.3708 (Sidon)")
    print("\nEV Vehicle (15 kWh/100km):")

    result_ev = server.compare_energy_costs(
        origin="33.8938,35.5018",
        destination="33.5631,35.3708",
        vehicle_type="ev",
        consumption_per_100km=15
    )
    print_json(result_ev)

    print("\n\nGas Vehicle (7 L/100km):")
    result_gas = server.compare_energy_costs(
        origin="33.8938,35.5018",
        destination="33.5631,35.3708",
        vehicle_type="gas",
        consumption_per_100km=7
    )
    print_json(result_gas)


def demo_transit_poi_server():
    """Demonstrate Transit & POI Server capabilities."""
    print_section("PUBLIC TRANSIT & POI MAP SERVER DEMO")

    server = TransitPOIServer()

    # Demo 1: Find nearby transit stops
    print("\n1. FINDING NEARBY TRANSIT STOPS")
    print("-" * 70)
    print("Scenario: Looking for bus stops near Downtown Beirut")
    print("Location: 33.8938,35.5018 (Beirut Central)")
    print("Filter: Bus stops only")
    print("Radius: 3 km\n")

    result = server.nearby_transit_stops(
        location="33.8938,35.5018",
        transit_type="bus",
        radius_km=3
    )
    print_json(result)

    # Demo 2: Plan transit route
    print("\n\n2. PLANNING PUBLIC TRANSIT ROUTE")
    print("-" * 70)
    print("Scenario: Transit trip from AUB to Tripoli")
    print("Origin: 33.9018,35.4787 (AUB)")
    print("Destination: 34.4364,35.8211 (Tripoli)\n")

    result = server.plan_transit_route(
        origin="33.9018,35.4787",
        destination="34.4364,35.8211"
    )
    print_json(result)

    # Demo 3: Find nearby POIs
    print("\n\n3. FINDING NEARBY POINTS OF INTEREST")
    print("-" * 70)
    print("Scenario: Looking for restaurants near Mar Mikhael")
    print("Location: 33.8987,35.5201 (Mar Mikhael)")
    print("Category: Restaurants")
    print("Radius: 5 km")
    print("Minimum Rating: 4.0\n")

    result = server.find_nearby_pois(
        location="33.8987,35.5201",
        category="restaurant",
        radius_km=5,
        min_rating=4.0
    )
    print_json(result)

    print("\n\n4. FINDING HOSPITALS")
    print("-" * 70)
    print("Scenario: Finding all hospitals within 3 km of Downtown")
    print("Location: 33.8938,35.5018\n")

    result = server.find_nearby_pois(
        location="33.8938,35.5018",
        category="hospital",
        radius_km=3
    )
    print_json(result)


def demo_integrated_scenarios():
    """Demonstrate integrated usage scenarios."""
    print_section("INTEGRATED USAGE SCENARIOS")

    ev_server = EVChargingServer()
    transit_server = TransitPOIServer()

    print("\nSCENARIO 1: Planning a Day Trip")
    print("-" * 70)
    print("Goal: Visit Byblos from Beirut, find landmarks, plan return trip\n")

    print("Step 1: Find EV charging in Byblos")
    charging = ev_server.nearby_charging_stations(
        location="34.1209,35.6478",
        radius_km=1
    )
    print(f"Found {charging['stations_found']} charging stations")

    print("\nStep 2: Find landmarks near Byblos Harbor")
    landmarks = transit_server.find_nearby_pois(
        location="34.1209,35.6478",
        category="landmark",
        radius_km=1
    )
    print(f"Found {landmarks['pois_found']} landmarks")

    print("\nStep 3: Calculate round trip energy cost")
    cost = ev_server.compare_energy_costs(
        origin="33.8938,35.5018",
        destination="34.1209,35.6478",
        vehicle_type="ev",
        consumption_per_100km=15
    )
    print(f"Round trip distance: {cost['total_distance_km'] * 2} km")
    print(f"Energy cost (round trip): ${cost['cost_estimate_usd'] * 2:.2f}")

    print("\n\nSCENARIO 2: Multi-Modal Transportation")
    print("-" * 70)
    print("Goal: Use public transit to work, find nearby amenities\n")

    print("Step 1: Plan transit route to workplace")
    route = transit_server.plan_transit_route(
        origin="33.9018,35.4787",  # Home (AUB area)
        destination="33.8938,35.5018"  # Work (Downtown)
    )
    print(f"Total time: {route['estimated_total_time_minutes']} minutes")
    print(f"Transfers: {route['transfers']}")

    print("\nStep 2: Find nearby shopping at work")
    shopping = transit_server.find_nearby_pois(
        location="33.8938,35.5018",
        category="shopping",
        radius_km=1
    )
    print(f"Found {shopping['pois_found']} shopping centers within walking distance")

    print("\nStep 3: Find nearby banks for errands")
    banks = transit_server.find_nearby_pois(
        location="33.8938,35.5018",
        category="bank",
        radius_km=1
    )
    print(f"Found {banks['pois_found']} banks nearby")


def interactive_mode():
    """Run interactive agent mode."""
    print_section("INTERACTIVE AGENT MODE")

    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("\nWarning: OPENAI_API_KEY environment variable not set.")
        print("Interactive agent mode requires an OpenAI API key.")
        print("\nTo use interactive mode:")
        print("1. Get an API key from https://platform.openai.com/")
        print("2. Set it: export OPENAI_API_KEY='your-key-here'")
        print("3. Run this script again\n")
        return

    try:
        from agents.map_agent import MapAgent

        agent = MapAgent()
        agent.interactive_session()

    except ImportError as e:
        print(f"\nError importing MapAgent: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"\nError: {e}")


def main():
    """Main demo function."""
    print("\n" + "=" * 70)
    print("  MAP SERVERS DEMONSTRATION")
    print("  Model Context Protocol (MCP) Implementation")
    print("=" * 70)

    print("\nChoose demo mode:")
    print("  1. EV Charging & Fuel Server Demo")
    print("  2. Transit & POI Server Demo")
    print("  3. Integrated Scenarios Demo")
    print("  4. All Demos (1-3)")
    print("  5. Interactive Agent Mode (requires OpenAI API key)")
    print("  0. Exit")

    while True:
        try:
            choice = input("\nEnter your choice (0-5): ").strip()

            if choice == "0":
                print("\nGoodbye!")
                break
            elif choice == "1":
                demo_ev_charging_server()
            elif choice == "2":
                demo_transit_poi_server()
            elif choice == "3":
                demo_integrated_scenarios()
            elif choice == "4":
                demo_ev_charging_server()
                demo_transit_poi_server()
                demo_integrated_scenarios()
            elif choice == "5":
                interactive_mode()
            else:
                print("Invalid choice. Please enter 0-5.")

            if choice in ["1", "2", "3", "4"]:
                print("\n" + "=" * 70)
                print("  Demo completed! Choose another option or 0 to exit.")
                print("=" * 70)

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main()
