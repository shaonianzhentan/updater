from __future__ import annotations
import _thread, os
from typing import Any
import voluptuous as vol

from homeassistant.data_entry_flow import FlowResult

import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry

from .const import DOMAIN
from .file_api import git_info, download, custom_components_path

proxy_list = {
    '不使用': '不使用', 
    'github.com': 'github.com',
    'ghproxy.com/https://github.com': 'ghproxy.com',
    'hub.fastgit.xyz': 'hub.fastgit.xyz',
    'github.com.cnpmjs.org': 'github.com.cnpmjs.org',
}

DATA_SCHEMA = vol.Schema({
    vol.Optional("title"): str,
    vol.Required("url"): str,
    vol.Required("proxy", default="不使用"): vol.In(proxy_list),
})

class SimpleConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        errors = {}
        if user_input is not None:
            global DATA_SCHEMA
            DATA_SCHEMA = vol.Schema({
                vol.Optional("title", default=user_input.get('title', '')): str,
                vol.Required("url", default=user_input.get('url', '')): str,
                vol.Required("proxy", default=user_input.get('proxy', '不使用')): vol.In(proxy_list),
            })
            
            # validate url format
            url = user_input.get('url')
            info = git_info(url)
            if info is None:
               errors['base'] = 'url'

            # validate success
            if errors.get('base', '') == '':
                domain = info.get('domain')
                title = user_input.get('title', domain)
                proxy = user_input.get('proxy')
                print(proxy)
                if proxy == '不使用':
                    return self.async_create_entry(title=title, data={
                        'title': title,
                        'url': url
                    })
                else:                    
                    sh_file = custom_components_path(f'{domain}.sh')
                    # download file of bash script
                    url = 'https://gitee.com/shaonianzhentan/updater/raw/main/bash/install.sh'
                    await download(url, sh_file)
                    # execute bash script                            
                    git_url = info.get('url').replace('github.com', proxy)
                    git_branch = info.get('branch')
                    git_project = info.get('project')
                    bash = f'sh {sh_file} {git_branch} {git_url} {git_project} {domain}'
                    print(bash)
                    _thread.start_new_thread(os.system, (bash, ))
                    
                    errors['base'] = 'proxy'

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)