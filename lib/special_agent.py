#!/usr/bin/env python3

# This file is part of cmk-Tado.
# cmk-Tado is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation in version 2.
# cmk-Tado is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with cmk-Tado.
# If not, see <https://www.gnu.org/licenses/>.


import sys
import requests
import string
from pathlib import Path
from cmk.utils import password_store
from collections.abc import Sequence
from cmk.special_agents.v0_unstable.agent_common import SectionWriter, special_agent_main
from cmk.special_agents.v0_unstable.argument_parsing import Args, create_default_argument_parser


# Dictionary of Tado device type prefixes
# List compiled from my own devices and those listed at https://shop.tado.com/en/pages/conformity
DEVICE_PREFIXES = {
    "IB": "Internet Bridge",
    "GW": "Internet Bridge",
    "AC": "AC Control",
    "WR": "AC Control",
    "ST": "Thermostat",
    "RU": "Thermostat",
    "VA": "Radiator Thermostat",
    "SRT": "Radiator Thermostat",
    "WTS": "Temperature Sensor",
    "SU": "Temperature Sensor",
    "WRP": "Receiver",
    "BP": "Receiver",
    "EK": "Extension Kit",
    "BU": "Extension Kit",
}

# Tado API details
# This not offically suported - details found via openHAB Tado binding
# https://github.com/openhab/openhab-addons/tree/main/bundles/org.openhab.binding.tado
TADO_AUTH_URL = "https://auth.tado.com/oauth/token"
TADO_API_URL = "https://my.tado.com/api/v2"
TADO_OAUTH_SCOPE = "home.user"
TADO_OAUTH_GRANT = "password"
TADO_CLIENT_ID = "public-api-preview"
TADO_CLIENT_SECRET = "4HJGRffVR8xb3XdEUQpjgZ1VplJi6Xgw"


# Get Tado access token
def get_access_token(username: str, password: str) -> str:
    headers = {
        "User-Agent": "Checkmk/Tado",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    body = {
        "client_id": TADO_CLIENT_ID,
        "client_secret": TADO_CLIENT_SECRET,
        "scope": TADO_OAUTH_SCOPE,
        "grant_type": TADO_OAUTH_GRANT,
        "username": username,
        "password": password
    }
    response = requests.post(TADO_AUTH_URL, data=body, headers=headers)
    # Check for authentication failure
    if response.status_code == 400:
        raise AuthError("Tado username/password is incorrect")
    # Check for error response
    response.raise_for_status()
    # Return access token
    return response.json()["access_token"]


# Call Tado API
def call_tado_api(access_token: str, endpoint: str):
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{TADO_API_URL}{endpoint}", headers=headers)
    # Check for error response
    response.raise_for_status()
    # Return response
    return response.json()


# Get Tado account details
def get_tado_account(access_token: str) -> dict:
    return call_tado_api(access_token, "/me")


# Get all Tado devices within a home
def get_tado_devices(home_id: int, access_token: str) -> list[dict]:
    return call_tado_api(access_token, f"/homes/{home_id}/devices")


# Get all Tado heating zones within a home
def get_tado_zones(home_id: int, access_token: str) -> list[dict]:
    return call_tado_api(access_token, f"/homes/{home_id}/zones")


# Check device details
def check_device(device: dict) -> str:
    # Get device type description
    remove_numbers = str.maketrans("", "", string.digits)
    device_prefix = device["deviceType"].translate(remove_numbers)
    device_type = DEVICE_PREFIXES.get(device_prefix, "Device")

    # Default status is good if we do not find problems
    check_status = 0
    check_detail = "Connected"

    # Check if the device is disconnected
    if not device["connectionState"]["value"]:
        check_status = 2
        check_detail = "Disconnected"

    # Check if the device is not calibrated
    elif "mountingStateWithError" in device and not device["mountingStateWithError"] == "CALIBRATED":
        check_status = 2
        check_detail = "Mounting Error"

    # Check if the device has a low battery
    elif "batteryState" in device and not device["batteryState"] == "NORMAL" and check_status == 0:
        check_status = 1
        check_detail = "Low Battery"

    # Return check result for this device
    # device_type|SerialNo|check_status|check_detail
    return f"{device_type}|{device['serialNo']}|{str(check_status)}|{check_detail}"


# Run special agent
def agent_tado_main(args: Args) -> int:
    try:
        password = None
        # Get password from command line
        if args.password is not None:
            password = args.password
        # Get password from store
        elif args.password_id is not None:
            pw_id, pw_path = args.password_id.split(":")
            password = password_store.lookup(Path(pw_path), pw_id)
        # Username and/or password was not provided
        if password is None or args.username is None:
             raise AuthError("A Tado username and password is required")

        # Get access token
        access_token = get_access_token(args.username, password)

        # Get account details
        account = get_tado_account(access_token)

        # Define section header
        with SectionWriter("tado_device_health", separator="|") as writer:
            # Iterate over each home
            for home in account["homes"]:
                # Check if we want to monitor this home
                if args.home is None or args.home.lower() == home["name"].lower():
                    # Get all Tado devices and zones in this home
                    devices = get_tado_devices(home["id"], access_token)
                    zones = get_tado_zones(home["id"], access_token)

                    # Iterate over each zone
                    for zone in zones:
                        # Check if we want to monitor this zone
                        if args.zone is None or args.zone.lower() == zone["name"].lower():
                            # Exclude hot water zone as it is not a physical zone and may duplicate devices with other zones
                            if zone["type"] != "HOT_WATER":

                                # Iterate over every device in the zone
                                for device in zone["devices"]:

                                    # Device belongs to a zone, so remove it from the list of unassigned devices
                                    del device["duties"]
                                    if device in devices:
                                        devices.remove(device)

                                    # Print check result for this device
                                    # HomeName|ZoneName|device_type|SerialNo|check_status|check_detail
                                    writer.append(f"{home['name']}|{zone['name']}|{check_device(device)}")

                    # Iterate over remaining devices that are not assigned to zones
                    if args.zone is None:
                        for device in devices:
                            # Print check result for this device
                            # HomeName|ZoneName|device_type|SerialNo|check_status|check_detail
                            writer.append(f"{home['name']}|Other|{check_device(device)}")
        return 0
    # Catch Tado API exceptions
    except (AuthError, requests.exceptions.RequestException) as e:
        sys.stderr.write(e.args[0])
        return 1


# Parse arguments
def parse_arguments(argv: Sequence[str]) -> Args:
    parser = create_default_argument_parser(description=__doc__)
    parser.add_argument("-u", "--username", default=None, help="Tado username")
    parser.add_argument("-p", "--password", default=None, help="Tado password")
    parser.add_argument("-i", "--password-id", default=None, help="Password store reference for Tado login")
    parser.add_argument("-o", "--home", default=None, help="Limit monitoring to the specified home")
    parser.add_argument("-z", "--zone", default=None, help="Limit monitoring to the specified zone")
    return parser.parse_args(argv)


# Authentication exception class
class AuthError(Exception):
    pass


# Starting point
def main() -> int:
    return special_agent_main(parse_arguments, agent_tado_main)


if __name__ == "__main__":
    sys.exit(main())
