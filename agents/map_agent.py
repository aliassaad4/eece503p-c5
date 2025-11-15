"""
Map Agent - Integrates all map servers with OpenAI Agents SDK

This module provides a unified agent interface that can route user queries
to the appropriate map server following MCP principles.
"""

import os
import json
from typing import Any, Dict, List, Optional
from openai import OpenAI

from servers.ev_charging_server import EVChargingServer, get_ev_charging_tools
from servers.transit_poi_server import TransitPOIServer, get_transit_poi_tools
from servers.traffic_server import TrafficServer, get_traffic_tools


class MapAgent:
    """
    Unified agent that integrates EV Charging, Transit/POI, and Traffic map servers.

    This agent uses OpenAI's function calling to route user requests to the
    appropriate server tools, following the Model Context Protocol approach.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the Map Agent.

        Args:
            api_key: OpenAI API key (if not provided, reads from OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY env var")

        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = OpenAI(api_key=self.api_key)

        # Initialize map servers
        self.ev_server = EVChargingServer()
        self.transit_server = TransitPOIServer()
        self.traffic_server = TrafficServer()

        # Combine all tools
        self.tools = get_ev_charging_tools() + get_transit_poi_tools() + get_traffic_tools()

        # System message
        self.system_message = """You are an intelligent map assistant with access to specialized map services.

You can help users with:
1. EV Charging & Fuel Services:
   - Find nearby EV charging stations
   - Plan routes with charging stops for electric vehicles
   - Compare energy costs between electric and gas vehicles

2. Public Transportation & POI Services:
   - Find nearby public transit stops (bus, metro, tram)
   - Plan multi-modal public transportation routes
   - Discover points of interest (restaurants, hospitals, hotels, schools, etc.)

3. Real-Time Traffic & Road Conditions:
   - Check traffic conditions on routes
   - Find alternate routes to avoid congestion
   - Get road closure and construction alerts

When users ask about locations, transportation, traffic, or energy-related queries, use the appropriate tools to provide accurate, helpful information.

Always provide clear, well-formatted responses with specific details from the tool results."""

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by routing to the appropriate server.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            Result from the tool execution
        """
        # EV Charging Server tools
        if tool_name == "nearby_charging_stations":
            return self.ev_server.nearby_charging_stations(**arguments)
        elif tool_name == "plan_charging_route":
            return self.ev_server.plan_charging_route(**arguments)
        elif tool_name == "compare_energy_costs":
            return self.ev_server.compare_energy_costs(**arguments)

        # Transit & POI Server tools
        elif tool_name == "nearby_transit_stops":
            return self.transit_server.nearby_transit_stops(**arguments)
        elif tool_name == "plan_transit_route":
            return self.transit_server.plan_transit_route(**arguments)
        elif tool_name == "find_nearby_pois":
            return self.transit_server.find_nearby_pois(**arguments)

        # Traffic Server tools
        elif tool_name == "check_route_traffic":
            return self.traffic_server.check_route_traffic(**arguments)
        elif tool_name == "find_alternate_routes":
            return self.traffic_server.find_alternate_routes(**arguments)
        elif tool_name == "get_road_closures":
            return self.traffic_server.get_road_closures(**arguments)

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def chat(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Process a user message and return the agent's response.

        Args:
            user_message: The user's query
            conversation_history: Optional list of previous messages

        Returns:
            The agent's response as a string
        """
        # Build messages
        messages = [{"role": "system", "content": self.system_message}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

        # Initial API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # If no tool calls, return the response directly
        if not tool_calls:
            return response_message.content

        # Process tool calls
        messages.append(response_message)

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # Execute the tool
            function_response = self._execute_tool(function_name, function_args)

            # Add tool response to messages
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(function_response)
            })

        # Get final response
        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        return final_response.choices[0].message.content

    def interactive_session(self):
        """
        Run an interactive chat session with the agent.
        """
        print("=" * 70)
        print("Map Agent - Interactive Session")
        print("=" * 70)
        print("\nAvailable Services:")
        print("  - EV charging stations and route planning")
        print("  - Energy cost comparisons (EV vs gas)")
        print("  - Public transportation routing")
        print("  - Points of interest discovery")
        print("\nType 'exit' or 'quit' to end the session.")
        print("=" * 70)

        conversation_history = []

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\nGoodbye! Have a great day!")
                    break

                if not user_input:
                    continue

                # Get agent response
                response = self.chat(user_input, conversation_history)

                # Update conversation history
                conversation_history.append({"role": "user", "content": user_input})
                conversation_history.append({"role": "assistant", "content": response})

                print(f"\nAgent: {response}")

            except KeyboardInterrupt:
                print("\n\nSession interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Please try again.")


# Convenience function for quick testing
def create_map_agent(api_key: Optional[str] = None) -> MapAgent:
    """
    Create and return a MapAgent instance.

    Args:
        api_key: Optional OpenAI API key

    Returns:
        Configured MapAgent instance
    """
    return MapAgent(api_key=api_key)
