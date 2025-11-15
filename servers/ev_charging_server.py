"""
EV Charging & Fuel Map Server

This module implements a map server focused on electric-vehicle charging stations
and gas stations, following the Model Context Protocol (MCP) approach.
"""

import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Any


class EVChargingServer:
    """Server providing EV charging and fuel comparison operations."""

    def __init__(self):
        """Initialize the EV Charging Server with mock data."""
        self.data_dir = Path(__file__).parent.parent / "data"
        self.charging_stations = self._load_charging_stations()

        # Pricing constants (can be configured)
        self.electricity_price_per_kwh = 0.15  # USD per kWh (average)
        self.gas_price_per_liter = 1.20  # USD per liter (average)

    def _load_charging_stations(self) -> List[Dict[str, Any]]:
        """Load charging stations from JSON file."""
        stations_file = self.data_dir / "charging_stations.json"
        with open(stations_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def _parse_location(location: str) -> tuple[float, float]:
        """
        Parse location string in 'lat,lon' format.

        Args:
            location: String in format "latitude,longitude"

        Returns:
            Tuple of (latitude, longitude)

        Raises:
            ValueError: If location format is invalid
        """
        try:
            parts = location.split(',')
            if len(parts) != 2:
                raise ValueError("Location must be in 'lat,lon' format")
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())

            if not (-90 <= lat <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= lon <= 180):
                raise ValueError("Longitude must be between -180 and 180")

            return lat, lon
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid location format: {e}")

    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates

        Returns:
            Distance in kilometers
        """
        # Radius of Earth in kilometers
        R = 6371.0

        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def nearby_charging_stations(
        self,
        location: str,
        connector_type: Optional[str] = None,
        radius_km: float = 5.0
    ) -> Dict[str, Any]:
        """
        Find nearby EV charging stations.

        Args:
            location: Coordinates in "lat,lon" format
            connector_type: Optional filter for connector type (Type2, CCS, CHAdeMO, etc.)
            radius_km: Search radius in kilometers (default: 5 km)

        Returns:
            Dictionary containing:
                - search_location: The search coordinates
                - radius_km: Search radius used
                - connector_filter: Connector type filter applied (if any)
                - stations_found: Number of stations found
                - stations: List of matching charging stations
        """
        try:
            lat, lon = self._parse_location(location)
        except ValueError as e:
            return {
                "error": str(e),
                "search_location": location,
                "radius_km": radius_km,
                "stations_found": 0,
                "stations": []
            }

        matching_stations = []

        for station in self.charging_stations:
            # Calculate distance
            station_lat = station['location']['lat']
            station_lon = station['location']['lon']
            distance = self._calculate_distance(lat, lon, station_lat, station_lon)

            # Check if within radius
            if distance > radius_km:
                continue

            # Check connector type filter
            if connector_type and connector_type not in station['connector_types']:
                continue

            # Add distance to station info
            station_info = {
                "id": station['id'],
                "name": station['name'],
                "address": station['address'],
                "distance_km": round(distance, 2),
                "location": station['location'],
                "connector_types": station['connector_types'],
                "power_ratings_kw": station['power_ratings_kw'],
                "available_connectors": station['available_connectors'],
                "total_connectors": station['total_connectors'],
                "pricing_per_kwh": station['pricing_per_kwh'],
                "operator": station['operator'],
                "is_operational": station['is_operational']
            }

            matching_stations.append(station_info)

        # Sort by distance
        matching_stations.sort(key=lambda x: x['distance_km'])

        return {
            "search_location": {"lat": lat, "lon": lon},
            "radius_km": radius_km,
            "connector_filter": connector_type,
            "stations_found": len(matching_stations),
            "stations": matching_stations
        }

    def plan_charging_route(
        self,
        origin: str,
        destination: str,
        battery_range_km: float
    ) -> Dict[str, Any]:
        """
        Plan a route with necessary charging stops.

        Args:
            origin: Starting point in "lat,lon" format
            destination: End point in "lat,lon" format
            battery_range_km: Current vehicle range on existing charge

        Returns:
            Dictionary containing:
                - origin: Starting location
                - destination: End location
                - total_distance_km: Total trip distance
                - charging_stops_needed: Number of charging stops required
                - route_plan: List of route legs with charging information
                - estimated_total_time_hours: Total estimated trip time
        """
        try:
            origin_lat, origin_lon = self._parse_location(origin)
            dest_lat, dest_lon = self._parse_location(destination)
        except ValueError as e:
            return {"error": str(e)}

        # Calculate total distance
        total_distance = self._calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)

        # If within battery range, no charging needed
        if total_distance <= battery_range_km:
            return {
                "origin": {"lat": origin_lat, "lon": origin_lon},
                "destination": {"lat": dest_lat, "lon": dest_lon},
                "total_distance_km": round(total_distance, 2),
                "charging_stops_needed": 0,
                "route_plan": [{
                    "leg": 1,
                    "from": "Origin",
                    "to": "Destination",
                    "distance_km": round(total_distance, 2),
                    "charging_stop": None,
                    "estimated_driving_time_hours": round(total_distance / 80, 2)  # Assume 80 km/h average
                }],
                "estimated_total_time_hours": round(total_distance / 80, 2)
            }

        # Plan charging stops
        route_plan = []
        current_lat, current_lon = origin_lat, origin_lon
        remaining_distance = total_distance
        current_range = battery_range_km
        leg_number = 1
        total_time = 0

        while remaining_distance > 0:
            # Calculate how far we can go with current charge (leaving 20% safety buffer)
            safe_range = current_range * 0.8

            if safe_range >= remaining_distance:
                # Can reach destination
                leg_distance = remaining_distance
                driving_time = leg_distance / 80  # 80 km/h average

                route_plan.append({
                    "leg": leg_number,
                    "from": "Charging Station" if leg_number > 1 else "Origin",
                    "to": "Destination",
                    "distance_km": round(leg_distance, 2),
                    "charging_stop": None,
                    "estimated_driving_time_hours": round(driving_time, 2)
                })

                total_time += driving_time
                remaining_distance = 0
            else:
                # Need a charging stop
                # Find direction towards destination
                progress_ratio = safe_range / total_distance
                next_lat = current_lat + (dest_lat - origin_lat) * progress_ratio
                next_lon = current_lon + (dest_lon - origin_lon) * progress_ratio

                # Find nearest charging station to this point
                nearest_station = None
                min_distance = float('inf')

                for station in self.charging_stations:
                    if not station['is_operational']:
                        continue

                    station_lat = station['location']['lat']
                    station_lon = station['location']['lon']
                    distance_to_station = self._calculate_distance(
                        next_lat, next_lon, station_lat, station_lon
                    )

                    # Check if station is roughly on the way
                    distance_from_current = self._calculate_distance(
                        current_lat, current_lon, station_lat, station_lon
                    )

                    if distance_from_current <= safe_range and distance_to_station < min_distance:
                        min_distance = distance_to_station
                        nearest_station = station

                if nearest_station:
                    station_lat = nearest_station['location']['lat']
                    station_lon = nearest_station['location']['lon']
                    leg_distance = self._calculate_distance(
                        current_lat, current_lon, station_lat, station_lon
                    )

                    # Estimate charging time based on power rating (assume 150 kW fast charger)
                    max_power = max(nearest_station['power_ratings_kw'].values())
                    charging_time = (battery_range_km * 0.15) / max_power  # Rough estimate

                    driving_time = leg_distance / 80

                    route_plan.append({
                        "leg": leg_number,
                        "from": "Charging Station" if leg_number > 1 else "Origin",
                        "to": nearest_station['name'],
                        "distance_km": round(leg_distance, 2),
                        "charging_stop": {
                            "station_id": nearest_station['id'],
                            "station_name": nearest_station['name'],
                            "address": nearest_station['address'],
                            "location": nearest_station['location'],
                            "estimated_charging_time_hours": round(charging_time, 2),
                            "available_connectors": nearest_station['connector_types'],
                            "max_power_kw": max_power,
                            "pricing_per_kwh": nearest_station['pricing_per_kwh']
                        },
                        "estimated_driving_time_hours": round(driving_time, 2)
                    })

                    total_time += driving_time + charging_time
                    current_lat, current_lon = station_lat, station_lon
                    remaining_distance -= leg_distance
                    current_range = battery_range_km  # Fully charged
                    leg_number += 1
                else:
                    # No suitable station found
                    return {
                        "error": "No suitable charging stations found along the route",
                        "origin": {"lat": origin_lat, "lon": origin_lon},
                        "destination": {"lat": dest_lat, "lon": dest_lon},
                        "total_distance_km": round(total_distance, 2)
                    }

        return {
            "origin": {"lat": origin_lat, "lon": origin_lon},
            "destination": {"lat": dest_lat, "lon": dest_lon},
            "total_distance_km": round(total_distance, 2),
            "charging_stops_needed": len([leg for leg in route_plan if leg['charging_stop']]),
            "route_plan": route_plan,
            "estimated_total_time_hours": round(total_time, 2)
        }

    def compare_energy_costs(
        self,
        origin: str,
        destination: str,
        vehicle_type: str,
        consumption_per_100km: float
    ) -> Dict[str, Any]:
        """
        Compare energy costs between EV and gas vehicles.

        Args:
            origin: Starting point in "lat,lon" format
            destination: End point in "lat,lon" format
            vehicle_type: Either "ev" or "gas"
            consumption_per_100km: Energy consumption (kWh for EV, liters for gas)

        Returns:
            Dictionary containing cost comparison including:
                - total_distance_km: Route distance
                - vehicle_type: Type of vehicle
                - consumption_per_100km: Consumption rate
                - energy_required: Total energy/fuel needed
                - cost_estimate: Total cost in USD
                - cost_breakdown: Detailed breakdown
                - comparison: Comparison with other vehicle type
        """
        try:
            origin_lat, origin_lon = self._parse_location(origin)
            dest_lat, dest_lon = self._parse_location(destination)
        except ValueError as e:
            return {"error": str(e)}

        # Calculate distance
        distance = self._calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)

        # Validate vehicle type
        if vehicle_type not in ["ev", "gas"]:
            return {"error": "vehicle_type must be 'ev' or 'gas'"}

        # Calculate energy/fuel required
        energy_required = (distance / 100) * consumption_per_100km

        if vehicle_type == "ev":
            # EV cost calculation
            cost = energy_required * self.electricity_price_per_kwh
            unit = "kWh"
            price_per_unit = self.electricity_price_per_kwh

            # Compare with gas vehicle
            typical_gas_consumption = 7.0  # liters per 100km
            gas_required = (distance / 100) * typical_gas_consumption
            gas_cost = gas_required * self.gas_price_per_liter

            comparison = {
                "alternative_vehicle": "gas",
                "alternative_consumption_per_100km": typical_gas_consumption,
                "alternative_unit": "liters",
                "alternative_energy_required": round(gas_required, 2),
                "alternative_cost_usd": round(gas_cost, 2),
                "savings_usd": round(gas_cost - cost, 2),
                "savings_percentage": round(((gas_cost - cost) / gas_cost * 100), 1) if gas_cost > 0 else 0
            }
        else:
            # Gas vehicle cost calculation
            cost = energy_required * self.gas_price_per_liter
            unit = "liters"
            price_per_unit = self.gas_price_per_liter

            # Compare with EV
            typical_ev_consumption = 15.0  # kWh per 100km
            ev_energy_required = (distance / 100) * typical_ev_consumption
            ev_cost = ev_energy_required * self.electricity_price_per_kwh

            comparison = {
                "alternative_vehicle": "ev",
                "alternative_consumption_per_100km": typical_ev_consumption,
                "alternative_unit": "kWh",
                "alternative_energy_required": round(ev_energy_required, 2),
                "alternative_cost_usd": round(ev_cost, 2),
                "extra_cost_usd": round(cost - ev_cost, 2),
                "extra_cost_percentage": round(((cost - ev_cost) / ev_cost * 100), 1) if ev_cost > 0 else 0
            }

        return {
            "origin": {"lat": origin_lat, "lon": origin_lon},
            "destination": {"lat": dest_lat, "lon": dest_lon},
            "total_distance_km": round(distance, 2),
            "vehicle_type": vehicle_type,
            "consumption_per_100km": consumption_per_100km,
            "unit": unit,
            "energy_required": round(energy_required, 2),
            "price_per_unit_usd": price_per_unit,
            "cost_estimate_usd": round(cost, 2),
            "cost_breakdown": {
                "distance_km": round(distance, 2),
                "consumption_rate": f"{consumption_per_100km} {unit}/100km",
                "total_energy": f"{round(energy_required, 2)} {unit}",
                "unit_price": f"${price_per_unit} per {unit}",
                "total_cost": f"${round(cost, 2)}"
            },
            "comparison": comparison
        }


# Tool definitions for OpenAI Agents SDK
def get_ev_charging_tools():
    """
    Get tool definitions for the EV Charging Server.

    Returns:
        List of tool definitions compatible with OpenAI Agents SDK
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "nearby_charging_stations",
                "description": "Find EV charging stations near a location with optional filtering by connector type",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location coordinates in 'lat,lon' format (e.g., '33.8938,35.5018')"
                        },
                        "connector_type": {
                            "type": "string",
                            "description": "Optional filter for connector type: Type2, CCS, or CHAdeMO",
                            "enum": ["Type2", "CCS", "CHAdeMO"]
                        },
                        "radius_km": {
                            "type": "number",
                            "description": "Search radius in kilometers (default: 5)",
                            "default": 5.0
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "plan_charging_route",
                "description": "Plan a route with necessary EV charging stops for long-distance travel",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting location in 'lat,lon' format"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination location in 'lat,lon' format"
                        },
                        "battery_range_km": {
                            "type": "number",
                            "description": "Current vehicle range on existing charge in kilometers"
                        }
                    },
                    "required": ["origin", "destination", "battery_range_km"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "compare_energy_costs",
                "description": "Compare energy costs between electric and gas vehicles for a trip",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting location in 'lat,lon' format"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination location in 'lat,lon' format"
                        },
                        "vehicle_type": {
                            "type": "string",
                            "description": "Type of vehicle: 'ev' for electric or 'gas' for gasoline",
                            "enum": ["ev", "gas"]
                        },
                        "consumption_per_100km": {
                            "type": "number",
                            "description": "Energy consumption per 100km (kWh for EV, liters for gas)"
                        }
                    },
                    "required": ["origin", "destination", "vehicle_type", "consumption_per_100km"]
                }
            }
        }
    ]
