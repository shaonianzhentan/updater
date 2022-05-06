import requests, os
from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .manifest import manifest, Manifest
from .file_api import get_current_path, download

NAME = manifest.name
DOMAIN = manifest.domain

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    unique_id = entry.entry_id
    ent = EntityUpdate(hass, unique_id, entry.data)
    await ent.async_update()
    async_add_entities([ ent ])

class EntityUpdate(UpdateEntity):

    _attr_supported_features = UpdateEntityFeature.INSTALL

    def __init__(self, hass, unique_id, config):
        self.hass = hass
        self.git_url = config.get('url')
        self.git_branch = config.get('branch')
        self.git_project = config.get('project')
        self._attr_title = config.get('title')
        self._attr_unique_id = unique_id
        self._attr_release_url = self.git_url
        self._attr_latest_version = '主分支'
        self.manifest = Manifest(config.get('domain'))
        # 隐藏更新提示
        self._attributes = {
            'skipped_version': self._attr_latest_version
        }

    @property
    def name(self):
        return self.manifest.domain

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, NAME)
            },
            "name": NAME,
            "manufacturer": "shaonianzhentan",
            "model": DOMAIN,
            "sw_version": manifest.version
        }

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def installed_version(self):
        return self.manifest.version or '未安装'

    async def async_install(self, version: str, backup: bool):
        sh_file = get_current_path(f'{self.name}.sh')
        if self.name == 'hacs':
            # download file of hacs install script
            url = 'https://gitee.com/shaonianzhentan/updater/raw/main/bash/hacs.sh'
            await download(url, sh_file)
            os.system(f'sh {sh_file}')
        else:
            # download file of bash script
            url = 'https://gitee.com/shaonianzhentan/updater/raw/main/bash/install.sh'
            await download(url, sh_file)
            # execute bash script
            os.system(f'sh {sh_file} {self.git_branch} {self.git_url} {self.git_project} {self.name}')

        self._attr_title = f'{self.name} 重启生效'
        self.manifest.update()
        print(f'install {self.name}')

    async def async_update(self):
        print(f'update {self.name}')