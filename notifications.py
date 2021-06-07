import logging
from typing import Dict, List
import configparser
from pathlib import Path
import json

logger = logging.getLogger("notification_manager")
config_file = Path.home() / ".nofconfig"


class _NotificationChannel(object):
    """
    Interface for new channels.
    New channels only *need* to overwrite "_send"
    If a persistent connection is used, optionally "_connect" as well
    If the message should be formatted differently for a channel, overwrite "_pprint"
    """

    def __init__(self):
        logger.debug(f"{self.__class__.__name__} instantiated")
        config = configparser.ConfigParser()
        config.read(config_file)
        self.config: Dict[str, str] = config[str(self.__class__.__name__)[1:]]
        self._connect()

    def _connect(self) -> None:
        pass

    def _pprint(self, event: Dict) -> str:
        """
        formats the kubernetes event into a nicely readable string
        """
        return f"{event['type']}: {event['object'].kind} {event['object'].metadata.name} ({event['object'].metadata.owner_references[0].kind} {event['object'].metadata.owner_references[0].name})"

    def _send(self, msg: str) -> None:
        raise NotImplementedError

    def notify(self, event: Dict) -> None:
        msg = self._pprint(event)
        try:
            self._send(msg)
        except:
            self._connect()
            try:
                self._send(msg)
            except Exception as e:
                logger.error(e)


class NotificationManager(object):
    def __init__(self, notification_channels: List[str]):
        self.notification_channels = [
            self._getChannel(val) for val in notification_channels
        ]
        logger.debug(f"found channels: {self.notification_channels}")

    @staticmethod
    def _getChannel(channelName: str) -> _NotificationChannel:
        import notifications as notif

        return getattr(notif, "_" + channelName)()

    def notify(self, event) -> None:
        for channel in self.notification_channels:
            logger.debug(f"notifying {channel} about {event['type']}")
            channel.notify(event)


# implement new channels below!


class _rocketchat(_NotificationChannel):
    def _connect(self):
        from rocketchat.api import RocketChatAPI

        self.rc = RocketChatAPI(
            settings={
                "username": self.config["username"],
                "password": self.config["password"],
                "domain": self.config["server"],
            }
        )
        logging.getLogger("base").setLevel(
            logging.WARN
        )  # FIXME still logs on debug level
        self.im_room = self.rc.create_im_room(self.config["yourUsername"])

    def _send(self, message: str):
        self.rc.send_message(message=message, room_id=self.im_room["id"])


class _elasticsearch(_NotificationChannel):
    def _connect(self):
        from elasticsearch import Elasticsearch, helpers
        import ssl
        from elasticsearch.connection import create_ssl_context
        import requests
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        # ignore https errors:
        ssl_context = create_ssl_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self.es = Elasticsearch(
            [
                f'{self.config["protocol"]}://{self.config["username"]}:{self.config["password"]}@{self.config["url"]}:{self.config["port"]}'
            ],
            ssl_context=ssl_context,
        )

    def _pprint(self, event: Dict):
        return json.loads(json.dumps(event))

    def _send(self, message: Dict):
        self.es.index(index=self.config["index"], body=message)
