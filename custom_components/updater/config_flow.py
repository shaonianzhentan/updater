from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.data_entry_flow import FlowResult

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry

from .const import DOMAIN
from .file_api import git_info

DATA_SCHEMA = vol.Schema({
    vol.Required("title"): str,
    vol.Required("url"): str,
})

class SimpleConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        errors = {}
        if user_input is not None:
            
            # validate url format
            info = git_info(user_input['url'])
            if  info is None:
                errors['base'] = 'url'

            # validate success
            if errors.get('base', '') == '':
                title = user_input['title']
                return self.async_create_entry(title=title, data={
                    'title': title,
                    'branch': info['branch'],
                    'project': info['project'],
                    'domain': info['domain'],
                    'url': info['url']
                })

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

