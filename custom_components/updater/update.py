import requests, datetime, os, hashlib, time, _thread, sys
from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityDescription,
    UpdateEntityFeature
)

from homeassistant.const import __version__ as current_version
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .manifest import manifest, Manifest
from .file_api import custom_components_path, download, git_info

NAME = manifest.name
DOMAIN = manifest.domain
HOMEASSISTANT = 'homeassistant'
HACS = 'hacs'

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entities = []
    '''
    初始化默认加载组件
    HACS、HomeAssitant
    '''
    if DOMAIN not in hass.data:
        arr = [
            {
                'title': 'Home Assistant',
                'url': 'homeassistant'
            },
            {
                'title': 'HACS',
                'url': 'https://github.com/hacs/integration/tree/main/custom_components/hacs'
            }
        ]
        hass.data[DOMAIN] = arr
        for data in arr:
            unique_id = hashlib.md5(data['url'].encode(encoding='UTF-8')).hexdigest()
            entities.append(EntityUpdate(hass, unique_id, data))

    entities.append(EntityUpdate(hass, entry.entry_id, entry.data))
    async_add_entities(entities)

class EntityUpdate(UpdateEntity):

    _attr_supported_features = UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES | UpdateEntityFeature.PROGRESS

    def __init__(self, hass, unique_id, config):
        self.hass = hass
        self._attr_unique_id = unique_id
        self._attr_title = config.get('title')
        self._release_notes = ''
        # config url
        url = config.get('url')
        if url == HOMEASSISTANT:
            self._attr_release_url = 'https://www.home-assistant.io/'
            self._attr_name = url
            self._attr_latest_version = 'latest'
        else:
            self._attr_release_url = url
            # github url info
            info = git_info(url)
            self._attr_name = info.get('domain')
            self.git_url = info.get('url')
            self.git_branch = info.get('branch')
            self.git_author = info.get('author')
            self.git_project = info.get('project')
            self.git_source = info.get('source')
            self.manifest = Manifest(self._attr_name)
            self._attr_latest_version = self.git_branch
        # 隐藏更新提示
        self._attributes = {
            'skipped_version': self._attr_latest_version
        }
        self._in_progress = False

    @property
    def in_progress(self) -> bool:
        return self._in_progress

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
        if self._attr_name == HOMEASSISTANT:
            return current_version

        return self.manifest.version or '未安装'

    def release_notes(self):
        return self._release_notes

    async def async_install(self, version: str, backup: bool):
        self._in_progress = True
        sh_file = custom_components_path(f'{self._attr_name}.sh')
        if self._attr_name == HACS:
            # download file of hacs install script
            url = 'https://gitee.com/shaonianzhentan/updater/raw/main/bash/hacs.sh'
            await download(url, sh_file)
            bash = f'sh {sh_file}'
        elif self._attr_name == HOMEASSISTANT:
            # upgrade homeassistant
            url = 'https://gitee.com/shaonianzhentan/updater/raw/main/bash/homeassistant.sh'
            await download(url, sh_file)
            python_version = sys.version_info
            bash = f'sh {sh_file} python{python_version[0]}.{python_version[1]}'
        else:
            # download file of bash script
            url = 'https://gitee.com/shaonianzhentan/updater/raw/main/bash/install.sh'
            await download(url, sh_file)
            # execute bash script
            bash = f'sh {sh_file} {self.git_branch} {self.git_url} {self.git_project} {self._attr_name}'

        _thread.start_new_thread(self.exec_script, (bash, ))

    def exec_script(self, bash):
        os.system(bash)        
        if self._attr_name == HOMEASSISTANT:
            pass
        else:
            self.manifest.update()
        self._attr_title = f'{self._attr_name} 重启生效'
        self._in_progress = False
        # print(f'install {self._attr_name}')
        self.hass.services.call('homeassistant', 'update_entity', { 'entity_id': self.entity_id})

    async def async_update(self):
        if self._attr_name == HOMEASSISTANT:
            url = 'https://api.github.com/repos/home-assistant/core/releases/latest'
            res = await self.hass.async_add_executor_job(requests.get, (url))
            data = res.json()
            self._attr_latest_version = data.get('name')
            self._release_notes = data.get('body')
        else:
            self._release_notes = ''