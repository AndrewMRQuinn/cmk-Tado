#!/usr/bin/env python3

# This file is part of cmk-Tado.
# cmk-Tado is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation in version 2.
# cmk-Tado is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with cmk-Tado.
# If not, see <https://www.gnu.org/licenses/>.


from collections.abc import Iterable
from pydantic import BaseModel
from cmk.server_side_calls.v1 import (
    HostConfig,
    SpecialAgentCommand,
    SpecialAgentConfig,
)
import cmk.utils.paths


# Paramenter validation
class TadoParams(BaseModel):
    home: str | None = None
    zone: str | None = None
    tokenid: str | None = None


# Get params from WATO form
def agent_tado_arguments(params: TadoParams, hostconfig: HostConfig) -> Iterable[SpecialAgentCommand]:
    args: list = []
    args.extend(["--name", str(hostconfig.name)])
    if params.home is not None:
        args.extend(["--home", str(params.home)])
    if params.zone is not None:
        args.extend(["--zone", str(params.zone)])
    if params.tokenid is not None:
        args.extend(["--tokenid", str(params.tokenid)])
    yield SpecialAgentCommand(command_arguments=args)


# Register special agent
special_agent_tado = SpecialAgentConfig(
    name="tado",
    parameter_parser=TadoParams.model_validate,
    commands_function=agent_tado_arguments
)
