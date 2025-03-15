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
import json
from datetime import datetime
from collections.abc import Sequence
from cmk.special_agents.v0_unstable.agent_common import SectionWriter, special_agent_main
from cmk.special_agents.v0_unstable.argument_parsing import Args, create_default_argument_parser
import cmk.utils.paths


# Dictionary of Tado device type prefixes
# List compiled from my own devices and those listed at https://shop.tado.com/en/pages/conformity
DEVICE_PREFIXES = {
    "AC": "AC Control",
    "WR": "AC Control",
    "BU": "Extension Kit",
    "EK": "Extension Kit",
    "LB": "Battery Pack",
    "LM": "Battery Pack",
    "MB": "Battery Pack",
    "CK": "Heat Pump Optimizer",
    "HPO": "Heat Pump Optimizer",
    "IB": "Internet Bridge",
    "GW": "Internet Bridge",
    "SRT": "Radiator Thermostat",
    "VA": "Radiator Thermostat",
    "BP": "Receiver",
    "BR": "Receiver",
    "PR": "Receiver",
    "TR": "Receiver",
    "WRB": "Receiver",
    "WRP": "Receiver",
    "SU": "Temperature Sensor",
    "WTS": "Temperature Sensor",
    "RU": "Thermostat",
    "ST": "Thermostat",
}

# Tado API details
# https://support.tado.com/en/articles/8565472-how-do-i-authenticate-to-access-the-rest-api
TADO_DEVICE_AUTH_URL = "https://login.tado.com/oauth2/device_authorize"
TADO_TOKEN_AUTH_URL = "https://login.tado.com/oauth2/token"
TADO_API_URL = "https://my.tado.com/api/v2"
TADO_OAUTH_SCOPE = "offline_access"
TADO_DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
TADO_TOKEN_GRANT = "refresh_token"
TADO_CLIENT_ID = "1bb50063-6b0c-4d11-bd99-387f4a91cc46"

# Stop using device codes or access tokens when they are this many seconds from expiry
DEVICE_CODE_GRACE = 60
ACCESS_TOKEN_GRACE = 30

# Class to handle persistent data
class PersistentStore:
    def __init__(self, name, tokenid):
        # Construct data file path
        self.data_file = "tado"
        if name is not None:
            self.data_file = f"{self.data_file}-{name}"
        if tokenid is not None:
            self.data_file = f"{self.data_file}-{tokenid}"
        self.data_file = f"{cmk.utils.paths.var_dir}/{self.data_file}.json"
        # Load persistent values from data file
        try:
            with open(self.data_file, "r") as file:
                data = (json.load(file))
            self.device_code = data.get("device_code")
            self.device_code_url = data.get("device_code_url")
            self.device_code_expiry = data.get("device_code_expiry")
            self.access_token = data.get("access_token")
            self.access_token_expiry = data.get("access_token_expiry")
            self.refresh_token = data.get("refresh_token")
        except:
            self.device_code = None
            self.device_code_url = None
            self.device_code_expiry = None
            self.access_token = None
            self.access_token_expiry = None
            self.refresh_token = None

    # Save data to file
    def save(self):
        with open(self.data_file, 'w') as file:
            json.dump({
                "device_code": self.device_code,
                "device_code_url": self.device_code_url,
                "device_code_expiry": self.device_code_expiry,
                "access_token": self.access_token,
                "access_token_expiry": self.access_token_expiry,
                "refresh_token": self.refresh_token
            }, file)


# Start device code grant flow
def start_device_flow(store: PersistentStore) -> str:
    headers = {
        "User-Agent": "Checkmk/Tado",
    }
    body = {
        "client_id": TADO_CLIENT_ID,
        "scope": TADO_OAUTH_SCOPE
    }
    response = requests.post(TADO_DEVICE_AUTH_URL, data=body, headers=headers)
    # Check for error response
    response.raise_for_status()
    # Save persistent values for next run
    response_json = response.json()
    store.device_code = response_json.get("device_code")
    store.device_code_url = response_json.get("verification_uri_complete")
    store.device_code_expiry = datetime.now().timestamp() + response_json.get("expires_in", 0) - DEVICE_CODE_GRACE
    store.save()


# Get Tado access token
def get_access_token(store: PersistentStore, body: dict) -> str:
    headers = {
        "User-Agent": "Checkmk/Tado",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(TADO_TOKEN_AUTH_URL, data=body, headers=headers)
    # Check for error response
    response.raise_for_status()
    # Save persistent values for next run
    response_json = response.json()
    store.access_token = response_json.get("access_token")
    store.access_token_expiry = datetime.now().timestamp() + response_json.get("expires_in", 0) - ACCESS_TOKEN_GRACE
    store.refresh_token = response_json.get("refresh_token")
    store.save()


# Get Tado access token using a device code
def auth_device_code(store: PersistentStore) -> str:
    body = {
        "client_id": TADO_CLIENT_ID,
        "device_code": store.device_code,
        "grant_type": TADO_DEVICE_GRANT
    }
    get_access_token(store, body)


# Get Tado access token using a refresh token
def auth_refresh_token(store: PersistentStore):
    body = {
        "client_id": TADO_CLIENT_ID,
        "refresh_token": store.refresh_token,
        "grant_type": TADO_TOKEN_GRANT
    }
    get_access_token(store, body)


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
    store = PersistentStore(args.name, args.tokenid)
    try:
        # Use refresh token if access token has expired
        now = datetime.now().timestamp()
        if store.access_token is not None and store.access_token_expiry is not None and store.refresh_token is not None and store.access_token_expiry < now:
            try:
                auth_refresh_token(store)
            except:
                store.access_token = None

        # Use device code grant flow if neither access token or refresh token works
        if store.access_token is None:
            # We have a device code - check if the user has authenticated
            if store.device_code is not None and store.device_code_url is not None and store.device_code_expiry > now:
                try:
                    auth_device_code(store)
                except:
                    store.access_token = None
                # The user hasn't authenticated - prompt again
                if (store.access_token is None):
                    sys.stderr.write(f"Log in at {store.device_code_url} to authorise access to Tado")
                    return 1
            # Get a new device code and prompt the user to authenticate
            else:
                start_device_flow(store)
                sys.stderr.write(f"Log in at {store.device_code_url} to authorise access to Tado")
                return 1

        # Get account details
        account = get_tado_account(store.access_token)

        # Define section header
        with SectionWriter("tado_device_health", separator="|") as writer:
            # Iterate over each home
            for home in account["homes"]:
                # Check if we want to monitor this home
                if args.home is None or args.home.lower() == home["name"].lower():
                    # Get all Tado devices and zones in this home
                    devices = get_tado_devices(home["id"], store.access_token)
                    zones = get_tado_zones(home["id"], store.access_token)

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
    parser.add_argument("-n", "--name", default=None, help="The name of the host")
    parser.add_argument("-o", "--home", default=None, help="Limit monitoring to the specified home")
    parser.add_argument("-z", "--zone", default=None, help="Limit monitoring to the specified zone")
    parser.add_argument("-t", "--tokenid", default=None, help="Custom ID for saving auth token")
    return parser.parse_args(argv)


# Authentication exception class
class AuthError(Exception):
    pass


# Starting point
def main() -> int:
    return special_agent_main(parse_arguments, agent_tado_main)


if __name__ == "__main__":
    sys.exit(main())
