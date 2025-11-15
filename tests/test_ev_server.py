"""
Unit tests for EV Charging Server

Tests all three required operations:
1. nearby_charging_stations
2. plan_charging_route
3. compare_energy_costs
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from servers.ev_charging_server import EVChargingServer


class TestEVChargingServer:
    """Test suite for EV Charging Server."""

    @pytest.fixture
    def server(self):
        """Create a server instance for testing."""
        return EVChargingServer()

    def test_nearby_charging_stations_basic(self, server):
        """Test basic nearby charging stations search."""
        result = server.nearby_charging_stations(
            location="33.8938,35.5018",  # Beirut
            radius_km=10
        )

        assert "stations_found" in result
        assert result["stations_found"] > 0
        assert "stations" in result
        assert isinstance(result["stations"], list)

    def test_nearby_charging_stations_with_filter(self, server):
        """Test nearby stations with connector type filter."""
        result = server.nearby_charging_stations(
            location="33.8938,35.5018",
            connector_type="CCS",
            radius_km=10
        )

        assert "connector_filter" in result
        assert result["connector_filter"] == "CCS"

        # Verify all returned stations have CCS connector
        for station in result["stations"]:
            assert "CCS" in station["connector_types"]

    def test_nearby_charging_stations_no_results(self, server):
        """Test search with very small radius returns no results."""
        result = server.nearby_charging_stations(
            location="33.8938,35.5018",
            radius_km=0.001  # Very small radius
        )

        # Should return valid structure even with no results
        assert "stations_found" in result
        assert result["stations_found"] == 0
        assert result["stations"] == []

    def test_nearby_charging_stations_invalid_location(self, server):
        """Test error handling for invalid location format."""
        result = server.nearby_charging_stations(
            location="invalid",
            radius_km=5
        )

        assert "error" in result

    def test_nearby_charging_stations_sorted_by_distance(self, server):
        """Test that results are sorted by distance."""
        result = server.nearby_charging_stations(
            location="33.8938,35.5018",
            radius_km=50
        )

        if result["stations_found"] > 1:
            distances = [s["distance_km"] for s in result["stations"]]
            assert distances == sorted(distances)

    def test_plan_charging_route_short_trip(self, server):
        """Test route planning for a trip within battery range."""
        result = server.plan_charging_route(
            origin="33.8938,35.5018",  # Beirut
            destination="33.9018,35.4787",  # AUB (very close)
            battery_range_km=50
        )

        assert "charging_stops_needed" in result
        assert result["charging_stops_needed"] == 0
        assert "route_plan" in result
        assert len(result["route_plan"]) == 1

    def test_plan_charging_route_long_trip(self, server):
        """Test route planning for a trip requiring charging stops."""
        result = server.plan_charging_route(
            origin="33.8938,35.5018",  # Beirut
            destination="34.4364,35.8211",  # Tripoli
            battery_range_km=30  # Short range to force charging stops
        )

        assert "charging_stops_needed" in result
        assert result["charging_stops_needed"] > 0
        assert "route_plan" in result
        assert "estimated_total_time_hours" in result

    def test_plan_charging_route_invalid_location(self, server):
        """Test error handling for invalid locations in route planning."""
        result = server.plan_charging_route(
            origin="invalid",
            destination="33.8938,35.5018",
            battery_range_km=50
        )

        assert "error" in result

    def test_plan_charging_route_has_charging_details(self, server):
        """Test that charging stops include necessary details."""
        result = server.plan_charging_route(
            origin="33.8938,35.5018",
            destination="34.4364,35.8211",
            battery_range_km=30
        )

        if result["charging_stops_needed"] > 0:
            # Find a leg with a charging stop
            charging_leg = None
            for leg in result["route_plan"]:
                if leg.get("charging_stop"):
                    charging_leg = leg
                    break

            assert charging_leg is not None
            charging_stop = charging_leg["charging_stop"]
            assert "station_name" in charging_stop
            assert "estimated_charging_time_hours" in charging_stop
            assert "max_power_kw" in charging_stop

    def test_compare_energy_costs_ev(self, server):
        """Test energy cost comparison for EV."""
        result = server.compare_energy_costs(
            origin="33.8938,35.5018",
            destination="33.5631,35.3708",
            vehicle_type="ev",
            consumption_per_100km=15
        )

        assert "cost_estimate_usd" in result
        assert "energy_required" in result
        assert "comparison" in result
        assert result["vehicle_type"] == "ev"
        assert result["unit"] == "kWh"

    def test_compare_energy_costs_gas(self, server):
        """Test energy cost comparison for gas vehicle."""
        result = server.compare_energy_costs(
            origin="33.8938,35.5018",
            destination="33.5631,35.3708",
            vehicle_type="gas",
            consumption_per_100km=7
        )

        assert "cost_estimate_usd" in result
        assert "energy_required" in result
        assert "comparison" in result
        assert result["vehicle_type"] == "gas"
        assert result["unit"] == "liters"

    def test_compare_energy_costs_ev_vs_gas(self, server):
        """Test that EV is cheaper than gas for same trip."""
        ev_result = server.compare_energy_costs(
            origin="33.8938,35.5018",
            destination="34.4364,35.8211",
            vehicle_type="ev",
            consumption_per_100km=15
        )

        gas_result = server.compare_energy_costs(
            origin="33.8938,35.5018",
            destination="34.4364,35.8211",
            vehicle_type="gas",
            consumption_per_100km=7
        )

        # EV should generally be cheaper
        assert ev_result["cost_estimate_usd"] < gas_result["cost_estimate_usd"]

    def test_compare_energy_costs_invalid_vehicle_type(self, server):
        """Test error handling for invalid vehicle type."""
        result = server.compare_energy_costs(
            origin="33.8938,35.5018",
            destination="33.5631,35.3708",
            vehicle_type="invalid",
            consumption_per_100km=15
        )

        assert "error" in result

    def test_compare_energy_costs_has_breakdown(self, server):
        """Test that cost comparison includes detailed breakdown."""
        result = server.compare_energy_costs(
            origin="33.8938,35.5018",
            destination="33.5631,35.3708",
            vehicle_type="ev",
            consumption_per_100km=15
        )

        assert "cost_breakdown" in result
        breakdown = result["cost_breakdown"]
        assert "distance_km" in breakdown
        assert "consumption_rate" in breakdown
        assert "total_energy" in breakdown
        assert "unit_price" in breakdown
        assert "total_cost" in breakdown

    def test_calculate_distance_accuracy(self, server):
        """Test distance calculation is reasonably accurate."""
        # Beirut to Tripoli is approximately 85 km
        result = server.plan_charging_route(
            origin="33.8938,35.5018",  # Beirut
            destination="34.4364,35.8211",  # Tripoli
            battery_range_km=300
        )

        distance = result["total_distance_km"]
        # Should be roughly 85 km (allow 10% margin)
        assert 75 < distance < 95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
