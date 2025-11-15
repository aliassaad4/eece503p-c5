# MCP Map Servers with OpenAI Agents SDK

This project implements multiple map servers using the OpenAI Agents SDK, following the Model Context Protocol (MCP) approach. The implementation includes an EV Charging & Fuel Map Server, a Public Transportation & POI Server, and a Real-Time Traffic & Road Conditions Server.

## Project Overview

This assignment explores the Model Context Protocol (MCP) concept by building custom map servers as agent "tools" using the OpenAI Agents SDK. The servers provide specialized mapping services for electric vehicle infrastructure, public transportation, points of interest, and real-time traffic conditions.

## Features

### 1. EV Charging & Fuel Map Server
- **nearby_charging_stations**: Find EV charging stations near a location with filtering options
- **plan_charging_route**: Plan routes with necessary charging stops for long-distance EV travel
- **compare_energy_costs**: Compare energy costs between electric and gas vehicles for trips

### 2. Public Transportation & POI Server
- **nearby_transit_stops**: Find public transportation stops (bus, metro, tram) near a location
- **plan_transit_route**: Plan multi-modal public transportation routes
- **find_nearby_pois**: Discover points of interest (restaurants, hospitals, schools, etc.)

### 3. Real-Time Traffic & Road Conditions Server
- **check_route_traffic**: Check real-time traffic conditions on routes with delay estimates
- **find_alternate_routes**: Find alternate routes to avoid congestion and save time
- **get_road_closures**: Get road closures, construction alerts, and incidents near a location

## Project Structure

```
C5/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── .env.example             # Example environment configuration
├── servers/                 # Map server implementations
│   ├── __init__.py
│   ├── ev_charging_server.py      # EV charging and fuel server
│   ├── transit_poi_server.py      # Public transportation and POI server
│   └── traffic_server.py          # Real-time traffic and road conditions
├── agents/                  # Agent implementations
│   ├── __init__.py
│   └── map_agent.py        # Main agent integrating all servers
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── test_ev_server.py
│   └── test_transit_server.py
├── demo.py                  # Interactive demonstration script
├── docs/                    # Documentation
│   ├── mcp_summary.md      # Summary of MCP concepts
│   └── reflection.md       # Reflection on implementation
└── data/                    # Mock data for demonstrations
    ├── charging_stations.json
    ├── transit_stops.json
    ├── pois.json
    ├── traffic_data.json
    └── road_closures.json
```

## Setup Instructions

### Prerequisites
- Python 3.9 or higher
- pip package manager
- OpenAI API key (for Agents SDK)

### Installation

1. Clone or download this repository

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file with your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### Running the Demo
```bash
python demo.py
```

This will launch an interactive demonstration of all server capabilities.

### Running Tests
```bash
pytest tests/
```

### Using Individual Servers

```python
from servers.ev_charging_server import EVChargingServer

# Create server instance
ev_server = EVChargingServer()

# Find nearby charging stations
stations = ev_server.nearby_charging_stations(
    location="33.8938,35.5018",  # Beirut, Lebanon
    connector_type="Type2",
    radius_km=10
)

# Plan a charging route
route = ev_server.plan_charging_route(
    origin="33.8938,35.5018",      # Beirut
    destination="34.4364,35.8211",  # Tripoli
    battery_range_km=300
)

# Compare energy costs
comparison = ev_server.compare_energy_costs(
    origin="33.8938,35.5018",
    destination="34.4364,35.8211",
    vehicle_type="ev",
    consumption_per_100km=15
)
```

## Implementation Details

### Mock Data
The servers use mock data for demonstration purposes. The data structure follows realistic API response formats and can be easily replaced with real API integration.

### Error Handling
All server operations include comprehensive error handling for:
- Invalid coordinates
- Missing required parameters
- Out-of-range values
- API failures (when integrated with real APIs)

### Extensibility
The architecture is designed for easy extension:
- Add new server operations by implementing new methods
- Integrate real APIs by replacing mock data functions
- Add new server types by following the existing patterns

## Future Enhancements

- **Real API Integration**: Connect to Open Charge Map, Google Maps, and other real-time services
- **Advanced Routing**: Implement algorithms considering elevation, traffic, and weather
- **Caching Strategy**: Add intelligent caching for frequently accessed data
- **Web Interface**: Build a web UI for easier interaction
- **Real-time Updates**: Implement WebSocket connections for live data updates
- **Multi-language Support**: Add internationalization for global usage

## Resources

- [OpenAI Agents SDK Documentation](https://platform.openai.com/docs/)
- [Model Context Protocol on Hugging Face](https://huggingface.co/blog/Kseniase/mcp)
- [Open Charge Map API](https://openchargemap.org/site/develop/api)
- [OpenStreetMap API](https://wiki.openstreetmap.org/wiki/API)

## License

This project is created for educational purposes as part of EECE 503P coursework.

## Author

[Your Name]
[Date: 2025]

## Acknowledgments

- OpenAI for the Agents SDK
- Open Charge Map for EV charging station data inspiration
- OpenStreetMap community for mapping data concepts
