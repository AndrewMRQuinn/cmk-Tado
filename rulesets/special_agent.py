#!/usr/bin/env python3

# This file is part of cmk-Tado.
# cmk-Tado is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation in version 2.
# cmk-Tado is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with cmk-Tado.
# If not, see <https://www.gnu.org/licenses/>.


from cmk.rulesets.v1 import Title, Help, Message
from cmk.rulesets.v1.form_specs import (
    DictElement,
    Dictionary,
    String,
)
from cmk.rulesets.v1.form_specs.validators import MatchRegex
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic


# Define form fields
def _form_spec() -> Dictionary:
    return Dictionary(
        title=Title("Tado (Advanced)"),
        help_text=Help("Requests data about device health in Tado zones."),
        elements={
            "home": DictElement(
                parameter_form=String(
                    title=Title("Filter by Home"),
                    help_text=Help(
                        "Only monitor devices from the specified home. "
                        "By default, all homes will be monitored."
                    )
                ),
                required=False
            ),
            "zone": DictElement(
                parameter_form=String(
                    title=Title("Filter by Zone"),
                    help_text=Help(
                        "Only monitor devices from the specified zone. "
                        "By default, all zones will be monitored."
                    )
                ),
                required=False
            ),
            "tokenid": DictElement(
                parameter_form=String(
                    title=Title("Custom Token ID"),
                    help_text=Help(
                        "If you have multiple Tado rules targeting the same host, they will share the same access token. "
                        "Give the rules custom token IDs if you need them to use different Tado accounts. "
                        "It doesn't matter what you choose as an ID as long as each Tado account on a host uses a different one. "
                        "If you don't require multiple Tado accounts per host you can ignore this setting and leave it empty. "
                    ),
                    custom_validate=[
                        MatchRegex(
                            regex="^[a-zA-Z0-9]+$",
                            error_msg=Message("Only alphanumeric characters are supported"),
                        )
                    ]
                ),
                required=False
            )
        }
    )


# Register the agent parameters
rule_spec_special_agent_tado = SpecialAgent(
    topic=Topic.SERVER_HARDWARE,
    name="tado",
    title=Title("Tado"),
    parameter_form=_form_spec,
)
