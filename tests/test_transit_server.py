"""
Unit tests for Transit & POI Server

Tests all three required operations:
1. nearby_transit_stops
2. plan_transit_route
3. find_nearby_pois
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from servers.transit_poi_server import TransitPOIServer


class TestTransitPOIServer:
    """Test suite for Transit & POI Server."""

    @pytest.fixture
    def server(self):
        """Create a server instance for testing."""
        return TransitPOIServer()

    # Tests for nearby_transit_stops
    def test_nearby_transit_stops_basic(self, server):
        """Test basic nearby transit stops search."""
        result = server.nearby_transit_stops(
            location="33.8938,35.5018",  # Beirut
            radius_km=2
        )

        assert "stops_found" in result
        assert result["stops_found"] > 0
        assert "stops" in result
        assert isinstance(result["stops"], list)

    def test_nearby_transit_stops_with_filter(self, server):
        """Test nearby stops with transit type filter."""
        result = server.nearby_transit_stops(
            location="33.8938,35.5018",
            transit_type="bus",
            radius_km=5
        )

        assert "transit_type_filter" in result
        assert result["transit_type_filter"] == "bus"

        # Verify all returned stops are buses
        for stop in result["stops"]:
            assert stop["type"] == "bus"

    def test_nearby_transit_stops_metro_filter(self, server):
        """Test filtering for metro stops."""
        result = server.nearby_transit_stops(
            location="33.8919,35.5167",  # Near Sassine Square
            transit_type="metro",
            radius_km=2
        )

        if result["stops_found"] > 0:
            for stop in result["stops"]:
                assert stop["type"] == "metro"

    def test_nearby_transit_stops_no_results(self, server):
        """Test search with very small radius returns no results."""
        result = server.nearby_transit_stops(
            location="33.8938,35.5018",
            radius_km=0.001  # Very small radius
        )

        assert "stops_found" in result
        assert result["stops_found"] == 0
        assert result["stops"] == []

    def test_nearby_transit_stops_invalid_location(self, server):
        """Test error handling for invalid location format."""
        result = server.nearby_transit_stops(
            location="invalid",
            radius_km=2
        )

        assert "error" in result

    def test_nearby_transit_stops_sorted_by_distance(self, server):
        """Test that results are sorted by distance."""
        result = server.nearby_transit_stops(
            location="33.8938,35.5018",
            radius_km=10
        )

        if result["stops_found"] > 1:
            distances = [s["distance_km"] for s in result["stops"]]
            assert distances == sorted(distances)

    def test_nearby_transit_stops_has_routes(self, server):
        """Test that transit stops include route information."""
        result = server.nearby_transit_stops(
            location="33.8938,35.5018",
            radius_km=5
        )

        if result["stops_found"] > 0:
            stop = result["stops"][0]
            assert "routes" in stop
            assert isinstance(stop["routes"], list)
            assert len(stop["routes"]) > 0

    # Tests for plan_transit_route
    def test_plan_transit_route_basic(self, server):
        """Test basic transit route planning."""
        result = server.plan_transit_route(
            origin="33.9018,35.4787",  # AUB
            destination="33.8938,35.5018"  # Downtown
        )

        assert "route_segments" in result
        assert "estimated_total_time_minutes" in result
        assert "transfers" in result
        assert len(result["route_segments"]) > 0

    def test_plan_transit_route_has_walk_segments(self, server):
        """Test that route includes walking segments."""
        result = server.plan_transit_route(
            origin="33.9018,35.4787",
            destination="33.8938,35.5018"
        )

        # Should have at least one walking segment
        walk_segments = [s for s in result["route_segments"] if s["type"] == "walk"]
        assert len(walk_segments) > 0

    def test_plan_transit_route_has_transit_segments(self, server):
        """Test that route includes transit segments."""
        result = server.plan_transit_route(
            origin="33.9018,35.4787",
            destination="34.4364,35.8211"  # Tripoli (long distance)
        )

        # Should have transit segments for long distances
        transit_segments = [s for s in result["route_segments"]
                           if s["type"] in ["bus", "metro", "tram"]]
        assert len(transit_segments) > 0

    def test_plan_transit_route_invalid_location(self, server):
        """Test error handling for invalid locations."""
        result = server.plan_transit_route(
            origin="invalid",
            destination="33.8938,35.5018"
        )

        assert "error" in result

    def test_plan_transit_route_has_summary(self, server):
        """Test that route includes summary information."""
        result = server.plan_transit_route(
            origin="33.9018,35.4787",
            destination="33.8938,35.5018"
        )

        assert "summary" in result
        summary = result["summary"]
        assert "total_segments" in summary
        assert "walking_segments" in summary
        assert "transit_segments" in summary

    def test_plan_transit_route_time_estimation(self, server):
        """Test that time estimation is reasonable."""
        result = server.plan_transit_route(
            origin="33.9018,35.4787",
            destination="33.8938,35.5018"
        )

        # Short distance should take less than 60 minutes
        assert result["estimated_total_time_minutes"] < 60

        # Should be positive
        assert result["estimated_total_time_minutes"] > 0

    # Tests for find_nearby_pois
    def test_find_nearby_pois_basic(self, server):
        """Test basic POI search."""
        result = server.find_nearby_pois(
            location="33.8938,35.5018",  # Beirut
            radius_km=3
        )

        assert "pois_found" in result
        assert result["pois_found"] > 0
        assert "pois" in result
        assert isinstance(result["pois"], list)

    def test_find_nearby_pois_with_category(self, server):
        """Test POI search with category filter."""
        result = server.find_nearby_pois(
            location="33.8978,35.4823",  # Hamra
            category="restaurant",
            radius_km=3
        )

        assert "category_filter" in result
        assert result["category_filter"] == "restaurant"

        # Verify all returned POIs are restaurants
        for poi in result["pois"]:
            assert poi["category"] == "restaurant"

    def test_find_nearby_pois_with_rating_filter(self, server):
        """Test POI search with minimum rating filter."""
        result = server.find_nearby_pois(
            location="33.8938,35.5018",
            category="restaurant",
            radius_km=5,
            min_rating=4.5
        )

        # Verify all returned POIs meet minimum rating
        for poi in result["pois"]:
            if poi["rating"] is not None:
                assert poi["rating"] >= 4.5

    def test_find_nearby_pois_hospitals(self, server):
        """Test finding hospitals."""
        result = server.find_nearby_pois(
            location="33.9018,35.4787",  # Near AUB
            category="hospital",
            radius_km=2
        )

        if result["pois_found"] > 0:
            for poi in result["pois"]:
                assert poi["category"] == "hospital"

    def test_find_nearby_pois_hotels(self, server):
        """Test finding hotels."""
        result = server.find_nearby_pois(
            location="33.8938,35.5018",
            category="hotel",
            radius_km=3
        )

        if result["pois_found"] > 0:
            for poi in result["pois"]:
                assert poi["category"] == "hotel"

    def test_find_nearby_pois_sorted_by_distance(self, server):
        """Test that POI results are sorted by distance."""
        result = server.find_nearby_pois(
            location="33.8938,35.5018",
            radius_km=10
        )

        if result["pois_found"] > 1:
            distances = [p["distance_km"] for p in result["pois"]]
            assert distances == sorted(distances)

    def test_find_nearby_pois_has_features(self, server):
        """Test that POIs include features information."""
        result = server.find_nearby_pois(
            location="33.8938,35.5018",
            radius_km=5
        )

        if result["pois_found"] > 0:
            poi = result["pois"][0]
            assert "features" in poi
            assert isinstance(poi["features"], list)

    def test_find_nearby_pois_invalid_location(self, server):
        """Test error handling for invalid location."""
        result = server.find_nearby_pois(
            location="invalid",
            radius_km=3
        )

        assert "error" in result

    def test_find_nearby_pois_no_results(self, server):
        """Test search with very small radius returns no results."""
        result = server.find_nearby_pois(
            location="33.8938,35.5018",
            radius_km=0.001  # Very small radius
        )

        assert "pois_found" in result
        assert result["pois_found"] == 0
        assert result["pois"] == []

    def test_find_nearby_pois_categories_summary(self, server):
        """Test that results include category summary."""
        result = server.find_nearby_pois(
            location="33.8938,35.5018",
            radius_km=5
        )

        assert "categories_summary" in result
        assert isinstance(result["categories_summary"], dict)

        # Summary counts should match actual results
        total_from_summary = sum(result["categories_summary"].values())
        assert total_from_summary == result["pois_found"]

    def test_find_nearby_pois_multiple_categories(self, server):
        """Test that unfiltered search returns multiple categories."""
        result = server.find_nearby_pois(
            location="33.8938,35.5018",
            radius_km=5
        )

        # Should have multiple categories
        categories = result["categories_summary"]
        assert len(categories) > 1

    def test_location_parsing_edge_cases(self, server):
        """Test location parsing with various formats."""
        # Test with extra spaces
        result = server.nearby_transit_stops(
            location="33.8938 , 35.5018",
            radius_km=2
        )
        assert "error" not in result

        # Test with negative coordinates
        result = server.nearby_transit_stops(
            location="-33.8938,35.5018",
            radius_km=2
        )
        assert "error" not in result

    def test_distance_calculation_consistency(self, server):
        """Test that distance calculations are consistent."""
        # Same location for origin and destination should give ~0 distance
        result = server.plan_transit_route(
            origin="33.8938,35.5018",
            destination="33.8938,35.5018"
        )

        assert result["total_distance_km"] < 0.1  # Should be very close to 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
