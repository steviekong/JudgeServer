# coding=utf-8
from __future__ import unicode_literals
import os
import json
import logging
import requests

from exception import JudgeServiceError
from utils import server_info, get_token


logger = logging.getLogger(__name__)
handler = logging.FileHandler("/log/service_log.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)


class JudgeService(object):
    def __init__(self):
        # exists if docker link oj_web_server:oj_web_server
        self.service_discovery_host = os.environ.get("OJ_WEB_SERVER_PORT_8080_TCP_ADDR")
        self.service_discovery_port = os.environ.get("OJ_WEB_SERVER_PORT_8080_TCP_PORT")
        self.service_discovery_url = os.environ.get("service_discovery_url", "")

        # this container's ip and port, if these are not set, web server will think it's a linked container
        self.service_host = os.environ.get("service_host")
        self.service_port = os.environ.get("service_port")

        if not self.service_discovery_url:
            if not (self.service_discovery_host and self.service_discovery_port):
                raise JudgeServiceError("service discovery host or port not found")
            else:
                self.service_discovery_url = "http://" + self.service_discovery_host + ":" + \
                                             str(self.service_discovery_port) + "/api/judge_service/"

    def _request(self, data):
        try:
            r = requests.post(self.service_discovery_url, data=json.dumps(data),
                              headers={"X-JUDGE-SERVER-TOKEN": get_token()}, timeout=5).json()
        except Exception as e:
            logger.exception(e)
            raise JudgeServiceError(e.message)
        if r["err"]:
            raise JudgeServiceError(r["data"])

    def register(self):
        data = server_info()
        data["action"] = "register"
        data["service_host"] = self.service_host
        data["service_port"] = self.service_port
        self._request(data)

    def unregister(self):
        data = server_info()
        data["action"] = "unregister"
        self._request(data)

    def heartbeat(self):
        data = server_info()
        data["action"] = "heartbeat"
        self._request(data)


if __name__ == "__main__":
    try:
        service = JudgeService()
        service.heartbeat()
        exit(0)
    except Exception as e:
        logger.exception(e)
        exit(1)