#!/usr/bin/env python3

# This file is part of cmk-Tado.
# cmk-Tado is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation in version 2.
# cmk-Tado is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with cmk-Tado.
# If not, see <https://www.gnu.org/licenses/>.


from cmk.rulesets.v1 import Title, Help
from cmk.rulesets.v1.form_specs import (
    DictElement,
    Dictionary,
    migrate_to_password,
    Password,
    String,
)
from cmk.rulesets.v1.form_specs.validators import LengthInRange
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic


# Define form fields
def _form_spec() -> Dictionary:
    return Dictionary(
        title=Title("Tado"),
        help_text=Help("Requests data about device health in Tado zones."),
        elements={
            "username": DictElement(
                parameter_form=String(
                    title=Title("Username"),
                    help_text=Help("The username for your Tado account."),
                    custom_validate=(LengthInRange(min_value=1),)
                ),
                required=True
            ),
            "password": DictElement(
                parameter_form=Password(
                    title=Title("Password"),
                    help_text=Help("The password for your Tado account."),
                    custom_validate=(LengthInRange(min_value=1),),
                    migrate=migrate_to_password
                ),
                required=True
            ),
            "filters": DictElement(
                parameter_form=Dictionary(
                    title=Title("Filters"),
                    help_text=Help(
                        "Only monitor devices from the specified home and/or zone. "
                        "By default, all homes and zones in your account will be monitored."
                    ),
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
                        )
                    }
                )
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
