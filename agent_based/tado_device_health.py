#!/usr/bin/env python3

# This file is part of cmk-Tado.
# cmk-Tado is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation in version 2.
# cmk-Tado is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with cmk-Tado.
# If not, see <https://www.gnu.org/licenses/>.


from .agent_based_api.v1 import register, Result, Service, State
from .agent_based_api.v1.type_defs import StringTable


# Parse function
def parse_tado_device_health(string_table: StringTable) -> dict:
    parsed = {}
    for line in string_table:
        try:
            # 0=HomeName, 1=ZoneName, 2=DeviceType, 3=SerialNo, 4=CheckStatus, 5=CheckDetail
            parsed[f"{line[0]} / {line[1]} / {line[2]} ({line[3]})"] = {"status": int(line[4]), "detail": line[5]}
        # If one of the lines can't be parsed, skip it
        except ValueError:
            sys.stderr.write(f"Failed to parse tado_device_health result: {str(line)}")
            pass
    return parsed


# Discovery function
def discover_tado_device_health(section: dict) -> Service:
    for device in section.keys():
        yield Service(item=device)


# Check function
def check_tado_device_health(item: str, section: dict) -> Result:
    if item in section.keys():
        yield Result(state=State(section[item]["status"]), summary=section[item]["detail"])
    else:
        yield Result(state=State.UNKNOWN, summary="Device not found")


# Register with Checkmk
register.agent_section(
    name = "tado_device_health",
    parse_function = parse_tado_device_health,
)

register.check_plugin(
    name = "tado_device_health",
    service_name = "Tado / %s",
    discovery_function = discover_tado_device_health,
    check_function = check_tado_device_health,
)
