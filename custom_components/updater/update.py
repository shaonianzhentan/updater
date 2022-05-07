import requests, datetime, subprocess, hashlib
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
from .file_api import custom_components_path, download, git_info

NAME = manifest.name
DOMAIN = manifest.domain

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
                'title': 'HACS',
                'url': 'https://github.com/hacs/integration/tree/main/custom_components/hacs'
            },
            {
                'title': '文件管理',
                'url': 'https://gitee.com/shaonianzhentan/ha_file_explorer/tree/dev/custom_components/ha_file_explorer'
            }
        ]
        hass.data[DOMAIN] = arr
        for data in arr:            
            unique_id = hashlib.md5(data['url'].encode(encoding='UTF-8')).hexdigest()
            entities.append(EntityUpdate(hass, unique_id, data))

    entities.append(EntityUpdate(hass, entry.entry_id, entry.data))
    async_add_entities(entities)

class EntityUpdate(UpdateEntity):

    _attr_supported_features = UpdateEntityFeature.INSTALL | UpdateEntityFeature.RELEASE_NOTES

    def __init__(self, hass, unique_id, config):
        self.hass = hass
        self._attr_unique_id = unique_id
        self._attr_title = config.get('title')
        # config url
        url = config.get('url')
        self._attr_release_url = url

        # github url info
        info = git_info(url)
        self.git_url = info.get('url')
        self.git_branch = info.get('branch')
        self.git_author = info.get('author')
        self.git_project = info.get('project')
        self.git_source = info.get('source')
        self.manifest = Manifest(info.get('domain'))
        self.commit_message = ''
        self._attr_latest_version = self.installed_version
        # 隐藏更新提示
        self._attributes = {}

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

    def release_notes(self):
        return self.commit_message

    async def async_install(self, version: str, backup: bool):
        sh_file = custom_components_path(f'{self.name}.sh')
        if self.name == 'hacs':
            # download file of hacs install script
            url = 'https://gitee.com/shaonianzhentan/updater/raw/main/bash/hacs.sh'
            await download(url, sh_file)
            bash = f'sh {sh_file}'
        else:
            # download file of bash script
            url = 'https://gitee.com/shaonianzhentan/updater/raw/main/bash/install.sh'
            await download(url, sh_file)
            # execute bash script
            bash = f'sh {sh_file} {self.git_branch} {self.git_url} {self.git_project} {self.name}'

        subprocess.Popen(bash, shell=True)

        self._attr_title = f'{self.name} 重启生效'
        self.manifest.update()
        print(f'install {self.name}')
        # record lastest version

    async def async_update(self):
        print(f'update {self.name}')
        git_api = 'api.github.com' 
        if self.git_source == 'gitee':
            git_api = 'gitee.com/api/v5'
        url = f'https://{git_api}/repos/{self.git_author}/{self.git_project}/branches/{self.git_branch}'
        
        res = await self.hass.async_add_executor_job(requests.get, (url))
        data = res.json()
        commit = data['commit']['commit']
        self.commit_message = commit.get('message')
        committer = commit.get('committer')
        date_str = committer.get('date')[:19]
        dt = datetime.datetime.fromisoformat(f'{date_str}+08:00')
        self._attr_latest_version = dt.strftime('%Y-%m-%d %H:%M:%S')

        self._attributes['skipped_version'] = self._attr_latest_version