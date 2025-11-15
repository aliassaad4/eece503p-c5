"""
Real-Time Traffic & Road Conditions Server

This module implements a map server for real-time traffic conditions, route optimization,
and road closure alerts, following the Model Context Protocol (MCP) approach.
"""

import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime


class TrafficServer:
    """Server providing real-time traffic conditions and road information operations."""

    def __init__(self):
        """Initialize the Traffic Server with mock data."""
        self.data_dir = Path(__file__).parent.parent / "data"
        self.traffic_data = self._load_traffic_data()
        self.road_closures = self._load_road_closures()

    def _load_traffic_data(self) -> List[Dict[str, Any]]:
        """Load traffic data from JSON file."""
        traffic_file = self.data_dir / "traffic_data.json"
        with open(traffic_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_road_closures(self) -> List[Dict[str, Any]]:
        """Load road closures from JSON file."""
        closures_file = self.data_dir / "road_closures.json"
        with open(closures_file, 'r', encoding='utf-8') as f:
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

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def check_route_traffic(
        self,
        origin: str,
        destination: str,
        include_incidents: bool = True
    ) -> Dict[str, Any]:
        """
        Check traffic conditions on a route.

        Args:
            origin: Starting point in "lat,lon" format
            destination: End point in "lat,lon" format
            include_incidents: Whether to include incident details (default: True)

        Returns:
            Dictionary containing:
                - origin: Starting location
                - destination: End location
                - total_distance_km: Total route distance
                - overall_traffic_level: Average traffic condition
                - estimated_duration_minutes: Trip duration with current traffic
                - typical_duration_minutes: Trip duration without traffic
                - delay_minutes: Total expected delay
                - route_segments: List of segments with traffic info
                - incidents_count: Number of incidents on route
                - incidents: List of incidents (if include_incidents=True)
        """
        try:
            origin_lat, origin_lon = self._parse_location(origin)
            dest_lat, dest_lon = self._parse_location(destination)
        except ValueError as e:
            return {"error": str(e)}

        # Find relevant road segments for this route
        relevant_segments = []
        total_distance = self._calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)

        for segment in self.traffic_data:
            # Check if segment is roughly on the route
            seg_start = segment['start_location']
            seg_end = segment['end_location']

            # Distance from origin to segment start
            dist_to_start = self._calculate_distance(
                origin_lat, origin_lon, seg_start['lat'], seg_start['lon']
            )

            # Distance from segment end to destination
            dist_from_end = self._calculate_distance(
                seg_end['lat'], seg_end['lon'], dest_lat, dest_lon
            )

            # If segment is roughly on the route (simple heuristic)
            if dist_to_start < total_distance * 1.5 and dist_from_end < total_distance * 1.5:
                segment_distance = self._calculate_distance(
                    seg_start['lat'], seg_start['lon'], seg_end['lat'], seg_end['lon']
                )

                relevant_segments.append({
                    "road_name": segment['road_name'],
                    "segment": segment['segment'],
                    "distance_km": round(segment_distance, 2),
                    "traffic_level": segment['traffic_level'],
                    "average_speed_kmh": segment['average_speed_kmh'],
                    "typical_speed_kmh": segment['typical_speed_kmh'],
                    "delay_minutes": segment['delay_minutes'],
                    "incidents": segment['incidents'] if include_incidents else len(segment['incidents'])
                })

        # Calculate overall metrics
        if relevant_segments:
            total_delay = sum(s['delay_minutes'] for s in relevant_segments)
            avg_speed = sum(s['average_speed_kmh'] for s in relevant_segments) / len(relevant_segments)

            # Calculate durations
            typical_duration = (total_distance / 70) * 60  # Assuming 70 km/h typical speed
            estimated_duration = typical_duration + total_delay

            # Determine overall traffic level
            traffic_levels = [s['traffic_level'] for s in relevant_segments]
            if 'heavy' in traffic_levels:
                overall_level = 'heavy'
            elif 'moderate' in traffic_levels:
                overall_level = 'moderate'
            else:
                overall_level = 'light'

            # Count incidents
            all_incidents = []
            for seg in relevant_segments:
                if include_incidents and isinstance(seg['incidents'], list):
                    for incident in seg['incidents']:
                        all_incidents.append({
                            "road": seg['road_name'],
                            "segment": seg['segment'],
                            **incident
                        })

            return {
                "origin": {"lat": origin_lat, "lon": origin_lon},
                "destination": {"lat": dest_lat, "lon": dest_lon},
                "total_distance_km": round(total_distance, 2),
                "overall_traffic_level": overall_level,
                "estimated_duration_minutes": round(estimated_duration, 1),
                "typical_duration_minutes": round(typical_duration, 1),
                "delay_minutes": total_delay,
                "average_speed_kmh": round(avg_speed, 1),
                "route_segments": relevant_segments,
                "incidents_count": len(all_incidents),
                "incidents": all_incidents if include_incidents else None,
                "recommendation": self._get_traffic_recommendation(overall_level, total_delay)
            }
        else:
            # No traffic data available for this route
            typical_duration = (total_distance / 70) * 60
            return {
                "origin": {"lat": origin_lat, "lon": origin_lon},
                "destination": {"lat": dest_lat, "lon": dest_lon},
                "total_distance_km": round(total_distance, 2),
                "overall_traffic_level": "unknown",
                "estimated_duration_minutes": round(typical_duration, 1),
                "typical_duration_minutes": round(typical_duration, 1),
                "delay_minutes": 0,
                "route_segments": [],
                "incidents_count": 0,
                "incidents": [] if include_incidents else None,
                "recommendation": "No real-time traffic data available for this route"
            }

    @staticmethod
    def _get_traffic_recommendation(traffic_level: str, delay_minutes: int) -> str:
        """Generate traffic recommendation based on conditions."""
        if traffic_level == "heavy" or delay_minutes > 15:
            return "Heavy traffic expected. Consider alternate route or delay departure."
        elif traffic_level == "moderate" or delay_minutes > 5:
            return "Moderate traffic conditions. Allow extra time for your journey."
        else:
            return "Good conditions. Route is clear with minimal delays."

    def find_alternate_routes(
        self,
        origin: str,
        destination: str,
        avoid_traffic_level: Optional[str] = "heavy"
    ) -> Dict[str, Any]:
        """
        Find alternate routes to avoid traffic congestion.

        Args:
            origin: Starting point in "lat,lon" format
            destination: End point in "lat,lon" format
            avoid_traffic_level: Traffic level to avoid (heavy, moderate, light)

        Returns:
            Dictionary containing:
                - primary_route: Main route with traffic info
                - alternate_routes: List of suggested alternate routes
                - recommendation: Which route to take
        """
        try:
            origin_lat, origin_lon = self._parse_location(origin)
            dest_lat, dest_lon = self._parse_location(destination)
        except ValueError as e:
            return {"error": str(e)}

        # Get primary route traffic
        primary_route = self.check_route_traffic(origin, destination, include_incidents=False)

        # Generate alternate routes (simplified simulation)
        alternate_routes = []

        # Alternate 1: Coastal route (if applicable)
        coastal_delay = primary_route.get('delay_minutes', 0) * 0.7  # 30% less delay
        alternate_routes.append({
            "route_name": "Coastal Route",
            "description": "Take scenic coastal highway",
            "distance_km": round(primary_route['total_distance_km'] * 1.1, 2),  # 10% longer
            "estimated_duration_minutes": round(primary_route['typical_duration_minutes'] * 1.1 + coastal_delay, 1),
            "traffic_level": "light" if primary_route['overall_traffic_level'] == "heavy" else "moderate",
            "delay_minutes": round(coastal_delay, 1),
            "advantage": "Less traffic, more scenic" if primary_route['overall_traffic_level'] == "heavy" else "Alternative option"
        })

        # Alternate 2: Mountain route
        mountain_delay = max(0, primary_route.get('delay_minutes', 0) * 0.5)  # 50% less delay
        alternate_routes.append({
            "route_name": "Mountain Route",
            "description": "Take mountain highway through elevated areas",
            "distance_km": round(primary_route['total_distance_km'] * 1.15, 2),  # 15% longer
            "estimated_duration_minutes": round(primary_route['typical_duration_minutes'] * 1.2 + mountain_delay, 1),
            "traffic_level": "light",
            "delay_minutes": round(mountain_delay, 1),
            "advantage": "Minimal traffic" if primary_route['overall_traffic_level'] in ["heavy", "moderate"] else "Scenic route"
        })

        # Alternate 3: Secondary roads
        secondary_delay = primary_route.get('delay_minutes', 0) * 0.4  # 60% less delay
        alternate_routes.append({
            "route_name": "Secondary Roads",
            "description": "Use local roads and bypass highways",
            "distance_km": round(primary_route['total_distance_km'] * 1.05, 2),  # 5% longer
            "estimated_duration_minutes": round(primary_route['typical_duration_minutes'] * 1.15 + secondary_delay, 1),
            "traffic_level": "moderate" if primary_route['overall_traffic_level'] == "heavy" else "light",
            "delay_minutes": round(secondary_delay, 1),
            "advantage": "Avoid highway congestion"
        })

        # Determine recommendation
        primary_time = primary_route.get('estimated_duration_minutes', float('inf'))
        best_alternate = min(alternate_routes, key=lambda r: r['estimated_duration_minutes'])

        if best_alternate['estimated_duration_minutes'] < primary_time * 0.9:
            recommendation = f"Recommended: Take {best_alternate['route_name']} - saves approximately {round(primary_time - best_alternate['estimated_duration_minutes'])} minutes"
        elif primary_route['overall_traffic_level'] == "heavy":
            recommendation = f"Consider {best_alternate['route_name']} to avoid heavy traffic, though slightly longer"
        else:
            recommendation = "Primary route is optimal - stick to main highway"

        return {
            "origin": {"lat": origin_lat, "lon": origin_lon},
            "destination": {"lat": dest_lat, "lon": dest_lon},
            "primary_route": {
                "route_name": "Primary Highway Route",
                "distance_km": primary_route['total_distance_km'],
                "estimated_duration_minutes": primary_route['estimated_duration_minutes'],
                "traffic_level": primary_route['overall_traffic_level'],
                "delay_minutes": primary_route.get('delay_minutes', 0)
            },
            "alternate_routes": alternate_routes,
            "routes_compared": len(alternate_routes) + 1,
            "recommendation": recommendation,
            "best_route": best_alternate['route_name'] if best_alternate['estimated_duration_minutes'] < primary_time else "Primary Highway Route"
        }

    def get_road_closures(
        self,
        location: str,
        radius_km: float = 10.0,
        severity_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get road closures and construction alerts near a location.

        Args:
            location: Center point in "lat,lon" format
            radius_km: Search radius in kilometers (default: 10 km)
            severity_filter: Filter by severity (high, medium, low)

        Returns:
            Dictionary containing:
                - search_location: The search coordinates
                - radius_km: Search radius used
                - closures_found: Number of closures found
                - active_closures: List of active road closures
                - severity_summary: Count by severity level
        """
        try:
            lat, lon = self._parse_location(location)
        except ValueError as e:
            return {
                "error": str(e),
                "search_location": location,
                "radius_km": radius_km,
                "closures_found": 0,
                "active_closures": []
            }

        matching_closures = []

        for closure in self.road_closures:
            if not closure.get('is_active', False):
                continue

            # Calculate distance to closure
            closure_lat = closure['location']['lat']
            closure_lon = closure['location']['lon']
            distance = self._calculate_distance(lat, lon, closure_lat, closure_lon)

            # Check if within radius
            if distance > radius_km:
                continue

            # Check severity filter
            if severity_filter and closure['severity'] != severity_filter.lower():
                continue

            # Add distance to closure info
            closure_info = {
                "id": closure['id'],
                "road_name": closure['road_name'],
                "distance_km": round(distance, 2),
                "location": closure['location'],
                "closure_type": closure['closure_type'],
                "severity": closure['severity'],
                "description": closure['description'],
                "start_date": closure['start_date'],
                "estimated_end_date": closure['estimated_end_date'],
                "affected_directions": closure['affected_directions'],
                "alternate_routes": closure['alternate_routes']
            }

            # Add optional fields
            if 'time_restrictions' in closure:
                closure_info['time_restrictions'] = closure['time_restrictions']
            if 'estimated_clearance_time' in closure:
                closure_info['estimated_clearance_time'] = closure['estimated_clearance_time']

            matching_closures.append(closure_info)

        # Sort by distance
        matching_closures.sort(key=lambda x: x['distance_km'])

        # Calculate severity summary
        severity_summary = {
            "high": len([c for c in matching_closures if c['severity'] == 'high']),
            "medium": len([c for c in matching_closures if c['severity'] == 'medium']),
            "low": len([c for c in matching_closures if c['severity'] == 'low'])
        }

        return {
            "search_location": {"lat": lat, "lon": lon},
            "radius_km": radius_km,
            "severity_filter": severity_filter,
            "closures_found": len(matching_closures),
            "active_closures": matching_closures,
            "severity_summary": severity_summary,
            "alerts": self._generate_closure_alerts(matching_closures)
        }

    @staticmethod
    def _generate_closure_alerts(closures: List[Dict[str, Any]]) -> List[str]:
        """Generate alert messages for road closures."""
        alerts = []
        high_severity = [c for c in closures if c['severity'] == 'high']

        if high_severity:
            alerts.append(f"WARNING: {len(high_severity)} high-severity road closure(s) in your area")

        for closure in closures[:3]:  # Top 3 closest
            if closure['severity'] == 'high':
                alerts.append(f"ALERT: {closure['road_name']} - {closure['description']}")

        return alerts


# Tool definitions for OpenAI Agents SDK
def get_traffic_tools():
    """
    Get tool definitions for the Traffic Server.

    Returns:
        List of tool definitions compatible with OpenAI Agents SDK
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "check_route_traffic",
                "description": "Check real-time traffic conditions on a route between two locations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting location in 'lat,lon' format (e.g., '33.8938,35.5018')"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination location in 'lat,lon' format"
                        },
                        "include_incidents": {
                            "type": "boolean",
                            "description": "Whether to include detailed incident information (default: true)",
                            "default": True
                        }
                    },
                    "required": ["origin", "destination"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "find_alternate_routes",
                "description": "Find alternate routes to avoid traffic congestion and save time",
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
                        "avoid_traffic_level": {
                            "type": "string",
                            "description": "Traffic level to avoid",
                            "enum": ["heavy", "moderate", "light"],
                            "default": "heavy"
                        }
                    },
                    "required": ["origin", "destination"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_road_closures",
                "description": "Get road closures, construction alerts, and incidents near a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Location coordinates in 'lat,lon' format"
                        },
                        "radius_km": {
                            "type": "number",
                            "description": "Search radius in kilometers (default: 10)",
                            "default": 10.0
                        },
                        "severity_filter": {
                            "type": "string",
                            "description": "Filter by severity level",
                            "enum": ["high", "medium", "low"]
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
