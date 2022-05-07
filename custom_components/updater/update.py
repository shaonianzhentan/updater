import requests, datetime, os, hashlib, time, _thread
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
            },
            {
                'title': 'QQ邮箱',
                'url': 'https://gitee.com/shaonianzhentan/smtp/tree/main/custom_components/smtp'
            },
            {
                'title': '待办事项',
                'url': 'https://gitee.com/shaonianzhentan/todoist/tree/master/custom_components/todoist'
            },
            {
                'title': '语音小助手',
                'url': 'https://gitee.com/shaonianzhentan/conversation/tree/master/custom_components/conversation'
            },
            {
                'title': '小米电视',
                'url': 'https://gitee.com/shaonianzhentan/xiaomi_tv/tree/main/custom_components/xiaomi_tv'
            },
            {
                'title': '侧边栏面板',
                'url': 'https://gitee.com/shaonianzhentan/panel_iframe/tree/main/custom_components/panel_iframe'
            },
            {
                'title': 'Yoosee摄像头',
                'url': 'https://gitee.com/shaonianzhentan/yoosee/tree/master/custom_components/yoosee'
            },
            {
                'title': '浏览器主页',
                'url': 'https://gitee.com/shaonianzhentan/ha-homepage/tree/master/custom_components/homepage'
            },
            {
                'title': '小说阅读器',
                'url': 'https://gitee.com/shaonianzhentan/ha-novel/tree/master/custom_components/feedreader'
            },
            {
                'title': '云音乐',
                'url': 'https://gitee.com/shaonianzhentan/ha_cloud_music/tree/master/custom_components/ha_cloud_music'
            },
            {
                'title': '百度地图',
                'url': 'https://gitee.com/shaonianzhentan/google_maps/tree/main/custom_components/google_maps'
            },
            {
                'title': '小米网关收音机',
                'url': 'https://gitee.com/shaonianzhentan/xiaomi_radio/tree/main/custom_components/xiaomi_radio'
            },
            {
                'title': '工作日',
                'url': 'https://gitee.com/shaonianzhentan/workday/tree/main/custom_components/workday'
            },
            {
                'title': 'IP蓝牙检测在家',
                'url': 'https://gitee.com/shaonianzhentan/bluetooth_tracker/tree/main/custom_components/bluetooth_tracker'
            },
            {
                'title': '云眸社区',
                'url': 'https://gitee.com/shaonianzhentan/hikvision/tree/main/custom_components/hikvision'
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
        self._attr_latest_version = self.git_branch
        # 隐藏更新提示
        self._attributes = {
            'skipped_version': self._attr_latest_version
        }
        self._in_progress = False

    @property
    def name(self):
        return self.manifest.domain

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
        return self.manifest.version or '未安装'

    def release_notes(self):
        return '''
        '''

    async def async_install(self, version: str, backup: bool):
        self._in_progress = True
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

        _thread.start_new_thread(self.exec_script, (bash, ))

    def exec_script(self, bash):
        os.system(bash)
        self._attr_title = f'{self.name} 重启生效'
        self.manifest.update()
        self._in_progress = False
        # print(f'install {self.name}')
        self.hass.services.call('homeassistant', 'update_entity', { 'entity_id': self.entity_id})

    async def async_update(self):
        #print(f'update {self.name}')
        pass