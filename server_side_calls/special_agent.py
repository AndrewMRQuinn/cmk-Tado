#!/usr/bin/env python3

# This file is part of cmk-Tado.
# cmk-Tado is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation in version 2.
# cmk-Tado is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with cmk-Tado.
# If not, see <https://www.gnu.org/licenses/>.


from collections.abc import Iterable, Mapping
from cmk.server_side_calls.v1 import (
    HostConfig,
    noop_parser,
    Secret,
    SpecialAgentCommand,
    SpecialAgentConfig,
)


# Get params from WATO form
def agent_tado_arguments(params: Mapping[str, object], hostconfig: HostConfig) -> Iterable[SpecialAgentCommand]:
    assert isinstance(secret := params["password"], Secret)
    args: list[str | Secret] = [
        "--username", str(params["username"]),
        "--password", secret.unsafe()
    ]
    if "filters" in params:
        if "home" in params["filters"]:
            args.extend(["--home", str(params["filters"]["home"])])
        if "zone" in params["filters"]:
            args.extend(["--zone", str(params["filters"]["zone"])])
    yield SpecialAgentCommand(command_arguments=args)


# Register special agent
special_agent_tado = SpecialAgentConfig(
    name="tado",
    parameter_parser=noop_parser,
    commands_function=agent_tado_arguments
)
