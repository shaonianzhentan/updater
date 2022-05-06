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

from .file_api import get_current_path
from .manifest import manifest, Manifest

NAME = manifest.name
DOMAIN = manifest.domain

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    unique_id = entry.entry_id
    title = entry.data.get('title')
    url = entry.options.get('url')
    domain = entry.options.get('domain')
    ent = EntityUpdate(hass, unique_id, title, url, domain)
    await ent.async_update()
    async_add_entities([ ent ])

class EntityUpdate(UpdateEntity):

    _attr_supported_features = UpdateEntityFeature.INSTALL

    def __init__(self, hass, unique_id, title, url, domain):
        self.hass = hass
        self._attr_title = title
        self._attr_unique_id = unique_id
        self._attr_release_url = url
        self._attr_latest_version = '主分支'
        self.manifest = Manifest(domain)

    @property
    def name(self):
        return self.manifest.domain

    @property
    def installed_version(self):
        return self.manifest.version or '未安装'

    async def async_install(self, version: str, backup: bool):
        sh_file = get_current_path('updater.sh')
        config_dir = self.hass.config.path('')
        os.system(f'''
cd {config_dir}
git clone {self._attr_release_url} --depth=1
rm -rf custom_components/{self.name}
cp -r ./{self.name}/custom_components/{self.name} custom_components/{self.name}
rm -rf {self.name}
        ''')
        self._attr_title = f'重启生效 {self.name}'
        self.manifest.update()

    async def async_update(self):
        print('update')