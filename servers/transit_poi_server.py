"""
Public Transportation & Points of Interest Map Server

This module implements a map server for public transportation routing and
discovering points of interest, following the Model Context Protocol (MCP) approach.
"""

import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Any


class TransitPOIServer:
    """Server providing public transportation and POI discovery operations."""

    def __init__(self):
        """Initialize the Transit & POI Server with mock data."""
        self.data_dir = Path(__file__).parent.parent / "data"
        self.transit_stops = self._load_transit_stops()
        self.pois = self._load_pois()

    def _load_transit_stops(self) -> List[Dict[str, Any]]:
        """Load transit stops from JSON file."""
        stops_file = self.data_dir / "transit_stops.json"
        with open(stops_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_pois(self) -> List[Dict[str, Any]]:
        """Load points of interest from JSON file."""
        pois_file = self.data_dir / "pois.json"
        with open(pois_file, 'r', encoding='utf-8') as f:
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
        R = 6371.0  # Radius of Earth in kilometers

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

    def nearby_transit_stops(
        self,
        location: str,
        transit_type: Optional[str] = None,
        radius_km: float = 2.0
    ) -> Dict[str, Any]:
        """
        Find nearby public transportation stops.

        Args:
            location: Coordinates in "lat,lon" format
            transit_type: Optional filter for transit type (bus, metro, tram)
            radius_km: Search radius in kilometers (default: 2 km)

        Returns:
            Dictionary containing:
                - search_location: The search coordinates
                - radius_km: Search radius used
                - transit_type_filter: Transit type filter applied (if any)
                - stops_found: Number of stops found
                - stops: List of matching transit stops
        """
        try:
            lat, lon = self._parse_location(location)
        except ValueError as e:
            return {
                "error": str(e),
                "search_location": location,
                "radius_km": radius_km,
                "stops_found": 0,
                "stops": []
            }

        matching_stops = []

        for stop in self.transit_stops:
            # Calculate distance
            stop_lat = stop['location']['lat']
            stop_lon = stop['location']['lon']
            distance = self._calculate_distance(lat, lon, stop_lat, stop_lon)

            # Check if within radius
            if distance > radius_km:
                continue

            # Check transit type filter
            if transit_type and stop['type'] != transit_type.lower():
                continue

            # Add distance to stop info
            stop_info = {
                "id": stop['id'],
                "name": stop['name'],
                "type": stop['type'],
                "distance_km": round(distance, 2),
                "location": stop['location'],
                "address": stop['address'],
                "routes": stop['routes'],
                "operating_hours": stop['operating_hours'],
                "facilities": stop['facilities']
            }

            matching_stops.append(stop_info)

        # Sort by distance
        matching_stops.sort(key=lambda x: x['distance_km'])

        return {
            "search_location": {"lat": lat, "lon": lon},
            "radius_km": radius_km,
            "transit_type_filter": transit_type,
            "stops_found": len(matching_stops),
            "stops": matching_stops
        }

    def plan_transit_route(
        self,
        origin: str,
        destination: str,
        preferred_transit_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Plan a public transportation route.

        Args:
            origin: Starting point in "lat,lon" format
            destination: End point in "lat,lon" format
            preferred_transit_types: Optional list of preferred transit types (bus, metro, tram)

        Returns:
            Dictionary containing:
                - origin: Starting location
                - destination: End location
                - total_distance_km: Approximate total distance
                - route_segments: List of transit segments
                - estimated_total_time_minutes: Estimated total trip time
                - transfers: Number of transfers required
        """
        try:
            origin_lat, origin_lon = self._parse_location(origin)
            dest_lat, dest_lon = self._parse_location(destination)
        except ValueError as e:
            return {"error": str(e)}

        # Calculate total distance
        total_distance = self._calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)

        # Find nearest stop to origin
        nearest_origin_stop = None
        min_origin_distance = float('inf')

        for stop in self.transit_stops:
            stop_lat = stop['location']['lat']
            stop_lon = stop['location']['lon']
            distance = self._calculate_distance(origin_lat, origin_lon, stop_lat, stop_lon)

            if distance < min_origin_distance:
                min_origin_distance = distance
                nearest_origin_stop = stop

        # Find nearest stop to destination
        nearest_dest_stop = None
        min_dest_distance = float('inf')

        for stop in self.transit_stops:
            stop_lat = stop['location']['lat']
            stop_lon = stop['location']['lon']
            distance = self._calculate_distance(dest_lat, dest_lon, stop_lat, stop_lon)

            if distance < min_dest_distance:
                min_dest_distance = distance
                nearest_dest_stop = stop

        if not nearest_origin_stop or not nearest_dest_stop:
            return {
                "error": "No transit stops found near origin or destination",
                "origin": {"lat": origin_lat, "lon": origin_lon},
                "destination": {"lat": dest_lat, "lon": dest_lon}
            }

        # Build route segments
        route_segments = []
        total_time_minutes = 0

        # Segment 1: Walk to nearest origin stop
        walk_to_stop_distance = min_origin_distance
        walk_to_stop_time = (walk_to_stop_distance / 5) * 60  # 5 km/h walking speed

        route_segments.append({
            "segment": 1,
            "type": "walk",
            "from": "Origin",
            "to": nearest_origin_stop['name'],
            "distance_km": round(walk_to_stop_distance, 2),
            "estimated_time_minutes": round(walk_to_stop_time, 1),
            "instructions": f"Walk to {nearest_origin_stop['name']}"
        })
        total_time_minutes += walk_to_stop_time

        # Segment 2: Transit from origin stop to intermediate/destination stop
        if nearest_origin_stop['id'] != nearest_dest_stop['id']:
            transit_distance = self._calculate_distance(
                nearest_origin_stop['location']['lat'],
                nearest_origin_stop['location']['lon'],
                nearest_dest_stop['location']['lat'],
                nearest_dest_stop['location']['lon']
            )

            # Average transit speed: 30 km/h for bus, 50 km/h for metro/tram
            avg_speed = 30 if nearest_origin_stop['type'] == 'bus' else 50
            transit_time = (transit_distance / avg_speed) * 60
            wait_time = 10  # Average wait time

            # Select a common route if possible
            common_routes = list(set(nearest_origin_stop['routes']) & set(nearest_dest_stop['routes']))
            selected_route = common_routes[0] if common_routes else nearest_origin_stop['routes'][0]

            route_segments.append({
                "segment": 2,
                "type": nearest_origin_stop['type'],
                "from": nearest_origin_stop['name'],
                "to": nearest_dest_stop['name'],
                "distance_km": round(transit_distance, 2),
                "route": selected_route,
                "wait_time_minutes": wait_time,
                "travel_time_minutes": round(transit_time, 1),
                "estimated_time_minutes": round(wait_time + transit_time, 1),
                "instructions": f"Take {selected_route} from {nearest_origin_stop['name']} to {nearest_dest_stop['name']}"
            })
            total_time_minutes += wait_time + transit_time

        # Segment 3: Walk to final destination
        walk_to_dest_distance = min_dest_distance
        walk_to_dest_time = (walk_to_dest_distance / 5) * 60  # 5 km/h walking speed

        route_segments.append({
            "segment": len(route_segments) + 1,
            "type": "walk",
            "from": nearest_dest_stop['name'],
            "to": "Destination",
            "distance_km": round(walk_to_dest_distance, 2),
            "estimated_time_minutes": round(walk_to_dest_time, 1),
            "instructions": f"Walk to destination from {nearest_dest_stop['name']}"
        })
        total_time_minutes += walk_to_dest_time

        # Count transfers (transit segments - 1)
        transit_segments = [s for s in route_segments if s['type'] in ['bus', 'metro', 'tram']]
        transfers = max(0, len(transit_segments) - 1)

        return {
            "origin": {"lat": origin_lat, "lon": origin_lon},
            "destination": {"lat": dest_lat, "lon": dest_lon},
            "total_distance_km": round(total_distance, 2),
            "route_segments": route_segments,
            "estimated_total_time_minutes": round(total_time_minutes, 1),
            "transfers": transfers,
            "summary": {
                "total_segments": len(route_segments),
                "walking_segments": len([s for s in route_segments if s['type'] == 'walk']),
                "transit_segments": len(transit_segments),
                "total_walking_distance_km": round(walk_to_stop_distance + walk_to_dest_distance, 2)
            }
        }

    def find_nearby_pois(
        self,
        location: str,
        category: Optional[str] = None,
        radius_km: float = 3.0,
        min_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Find points of interest near a location.

        Args:
            location: Coordinates in "lat,lon" format
            category: Optional category filter (restaurant, hospital, hotel, school, etc.)
            radius_km: Search radius in kilometers (default: 3 km)
            min_rating: Optional minimum rating filter (0-5)

        Returns:
            Dictionary containing:
                - search_location: The search coordinates
                - radius_km: Search radius used
                - category_filter: Category filter applied (if any)
                - min_rating_filter: Minimum rating filter (if any)
                - pois_found: Number of POIs found
                - pois: List of matching points of interest
        """
        try:
            lat, lon = self._parse_location(location)
        except ValueError as e:
            return {
                "error": str(e),
                "search_location": location,
                "radius_km": radius_km,
                "pois_found": 0,
                "pois": []
            }

        matching_pois = []

        for poi in self.pois:
            # Calculate distance
            poi_lat = poi['location']['lat']
            poi_lon = poi['location']['lon']
            distance = self._calculate_distance(lat, lon, poi_lat, poi_lon)

            # Check if within radius
            if distance > radius_km:
                continue

            # Check category filter
            if category and poi['category'] != category.lower():
                continue

            # Check rating filter
            if min_rating is not None and poi.get('rating', 0) < min_rating:
                continue

            # Build POI info
            poi_info = {
                "id": poi['id'],
                "name": poi['name'],
                "category": poi['category'],
                "distance_km": round(distance, 2),
                "location": poi['location'],
                "address": poi['address'],
                "rating": poi.get('rating'),
                "features": poi.get('features', [])
            }

            # Add optional fields if present
            if 'contact' in poi:
                poi_info['contact'] = poi['contact']
            if 'cuisine' in poi:
                poi_info['cuisine'] = poi['cuisine']

            matching_pois.append(poi_info)

        # Sort by distance
        matching_pois.sort(key=lambda x: x['distance_km'])

        # Group by category for summary
        categories = {}
        for poi in matching_pois:
            cat = poi['category']
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "search_location": {"lat": lat, "lon": lon},
            "radius_km": radius_km,
            "category_filter": category,
            "min_rating_filter": min_rating,
            "pois_found": len(matching_pois),
            "pois": matching_pois,
            "categories_summary": categories
        }


# Tool definitions for OpenAI Agents SDK
def get_transit_poi_tools():
    """
    Get tool definitions for the Transit & POI Server.

    Returns:
        List of tool definitions compatible with OpenAI Agents SDK
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "nearby_transit_stops",
                "description": "Find public transportation stops (bus, metro, tram) near a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location coordinates in 'lat,lon' format (e.g., '33.8938,35.5018')"
                        },
                        "transit_type": {
                            "type": "string",
                            "description": "Optional filter for transit type",
                            "enum": ["bus", "metro", "tram"]
                        },
                        "radius_km": {
                            "type": "number",
                            "description": "Search radius in kilometers (default: 2)",
                            "default": 2.0
                        }
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "plan_transit_route",
                "description": "Plan a multi-modal public transportation route between two locations",
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
                        "preferred_transit_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["bus", "metro", "tram"]
                            },
                            "description": "Optional list of preferred transit types"
                        }
                    },
                    "required": ["origin", "destination"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "find_nearby_pois",
                "description": "Find points of interest (restaurants, hospitals, hotels, schools, etc.) near a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location coordinates in 'lat,lon' format"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category filter",
                            "enum": ["restaurant", "hospital", "hotel", "school", "shopping", "museum", "gym", "bank", "park", "landmark"]
                        },
                        "radius_km": {
                            "type": "number",
                            "description": "Search radius in kilometers (default: 3)",
                            "default": 3.0
                        },
                        "min_rating": {
                            "type": "number",
                            "description": "Optional minimum rating filter (0-5)",
                            "minimum": 0,
                            "maximum": 5
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
