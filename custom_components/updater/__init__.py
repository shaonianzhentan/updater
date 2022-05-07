from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
import hashlib
from .const import PLATFORMS
from .manifest import manifest

DOMAIN = manifest.domain
CONFIG_SCHEMA = cv.deprecated(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    '''
    初始化默认加载组件
    HACS、HomeAssitant
    '''
    if DOMAIN not in hass.data:
        entities = [
            {
                'title': 'HACS',
                'url': 'https://github.com/hacs/integration/tree/main/custom_components/hacs'
            },
            {
                'title': 'HomeAssistant',
                'url': 'https://github.com/home-assistant/core/tree/dev/homeassistant/components'
            }
        ]
        hass.data[DOMAIN] = entities
        for data in entities:            
            hass.config_entries.async_setup_platforms({
                'entry_id': hashlib.md5(data['url'].encode(encoding='UTF-8')).hexdigest(),
                'data': data
            }, PLATFORMS)

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)