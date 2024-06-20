import logging, aiohttp, async_timeout

from datetime import timedelta
from homeassistant.const import CONF_REGION
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)


_LOGGER = logging.getLogger(__name__)


async def login_qbittorrent(session: aiohttp.ClientSession, url, username, password):
    login_url = f"{url}/api/v2/auth/login"
    login_data = {"username": username, "password": password}
    async with session.post(login_url, data=login_data) as response:
        if response.status == 200:
            _LOGGER.info("登录成功")
            return True
        else:
            _LOGGER.info("登录失败")
            return False


async def get_speed_limits_mode(session: aiohttp.ClientSession, url):
    speed_limits_url = f"{url}/api/v2/transfer/speedLimitsMode"
    async with session.get(speed_limits_url) as response:
        if response.status == 200:
            speed_limits_mode = await response.json()
            if speed_limits_mode:
                _LOGGER.info("备用速度模式已启用")
                return True
            else:
                _LOGGER.info("备用速度模式已禁用")
                return False
        else:
            _LOGGER.info("获取备用速度状态失败")


async def fetch_data(ip, username, password):
    _LOGGER.info("fetch_data")
    sensors = {}
    async with aiohttp.ClientSession() as session:
        if await login_qbittorrent(session, ip, username, password):
            sensors["state"] = await get_speed_limits_mode(session, ip)
    return sensors


class MyCoordinator(DataUpdateCoordinator):
    """用于多个传感器同时更新信息的一个协调器"""

    def __init__(self, hass, _config_entry):
        """Initialize my coordinator."""
        from . import DOMAIN

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN + "_" + _config_entry.data[CONF_REGION],
            update_interval=timedelta(hours=1),
        )
        self.err_times = 0
        self._config_entry = _config_entry
        _LOGGER.info("init MyCoordinator")

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(10):
                self.err_times = 0
                return await self.fetch_data()
        except:
            if self.err_times < 10:
                self.err_times += 1
                await self._async_update_data()

    async def fetch_data(self):
        _LOGGER.info("MyCoordinator fetch data")
        sensors = await fetch_data(self._config_entry.data[CONF_REGION])
        self.sensors = sensors
        _LOGGER.info(sensors)
