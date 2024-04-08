#!/usr/bin/env python3

# This file is part of cmk-Tado.
# cmk-Tado is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation in version 2.
# cmk-Tado is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with cmk-Tado.
# If not, see <https://www.gnu.org/licenses/>.


from cmk.gui.i18n import _
from cmk.gui.plugins.wato.special_agents.common import RulespecGroupDatasourceProgramsHardware
from cmk.gui.plugins.wato.utils import (
    HostRulespec,
    IndividualOrStoredPassword,
    rulespec_registry
)
from cmk.gui.valuespec import (
    Dictionary,
    TextInput,
)
from cmk.gui.watolib.rulespecs import Rulespec


# No default, do not use setting if no rule matches
def _factory_default_special_agents_tado():
    return Rulespec.FACTORY_DEFAULT_UNUSED


# Define WATO fields
def _valuespec_special_agents_tado():
    return Dictionary(
        title=_("Tado"),
        help=_("Requests data about device health in Tado zones."),
        optional_keys=[],
        elements=[
            (
                "username", TextInput(
                    title=_("Username"),
                    allow_empty=False,
                    help=_("The username for your Tado account.")
                )
            ),
            (
                "password", IndividualOrStoredPassword(
                    title=_("Password"),
                    allow_empty=False,
                    help=_("The password for your Tado account.")
                )
            ),
            (
                "filters", Dictionary(
                    title=_("Filters"),
                    help=_(
                        "Only monitor devices from the specified home and/or zone. "
                        "By default, all homes and zones in your account will be monitored."
                    ),
                    elements=[
                        (
                            "home", TextInput(
                                title=_("Filter by Home"),
                                allow_empty=False,
                                help=_("The name of the home to be monitored.")
                            )
                        ),
                        (
                            "zone", TextInput(
                                title=_("Filter by Zone"),
                                allow_empty=False,
                                help=_("The name of the zone to be monitored.")
                            )
                        )
                    ]
                )
            )
        ]
    )


# Register the agent parameters
rulespec_registry.register(
    HostRulespec(
        factory_default=_factory_default_special_agents_tado(),
        group=RulespecGroupDatasourceProgramsHardware,
        name="special_agents:tado",
        valuespec=_valuespec_special_agents_tado
    )
)
