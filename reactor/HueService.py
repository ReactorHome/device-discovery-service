import logging

from reactor.hue.HueApiClient import HueApiClient


class HueService:
    def __init__(self, hue_api_url):
        self.api_client = HueApiClient(hue_api_url, "reactor-home", None)
        self._logger = logging.getLogger("HueService")