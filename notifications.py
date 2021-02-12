import logging
from typing import Dict, List
import configparser
from pathlib import Path


logger = logging.getLogger("notification_manager")
config_file = Path.home() / ".nofconfig"


class _NotificationChannel(object):
    def __init__(self):
        raise NotImplementedError

    def notify(self, event: str) -> None:
        raise NotImplementedError

    def pprint(self, event: Dict) -> str:
        """
        formats the kubernetes event into a nicely readable string
        :param event:
        :return:
        """
        return f"{event['type']}: {event['object'].kind} {event['object'].metadata.name} ({event['object'].metadata.owner_references[0].kind} {event['object'].metadata.owner_references[0].name})"


class NotificationManager(object):
    def __init__(self, notification_channels: List[str]):
        self.notification_channels = [self._getChannel(val) for val in notification_channels]
        logger.debug(f"found channels: {self.notification_channels}")

    @staticmethod
    def _getChannel(channelName: str) -> _NotificationChannel:
        import notifications as notif

        return getattr(notif, "_" + channelName)()

    def notify(self, event) -> None:
        for channel in self.notification_channels:
            logger.debug(f"notifying {channel} about {event['type']}")
            channel.notify(channel.pprint(event))


class _rocketchat(_NotificationChannel):
    def __init__(self):
        logger.debug(f"{type(self)} instantiated")
        config = configparser.ConfigParser()
        config.read(config_file)
        self.config: Dict[str, str] = config["rocketchat"]
        self._new_rc_connection()
        logger.debug(f"{self.config['username']} will notify {self.config['yourUsername']}")

    def _new_rc_connection(self):
        from rocketchat.api import RocketChatAPI

        self.rc = RocketChatAPI(
            settings={
                "username": self.config["username"],
                "password": self.config["password"],
                "domain": self.config["server"],
            }
        )
        logging.getLogger("base").setLevel(logging.WARN) # FIXME still logs on debug level

        self.im_room = self.rc.create_im_room(self.config["yourUsername"])

    def notify(self, event: str):
        try:
            self.rc.send_message(message=str(event), room_id=self.im_room["id"])
        except:
            self._new_rc_connection()
            try:
                self.rc.send_message(message=str(event), room_id=self.im_room["id"])
            except Exception as e:
                logger.error(e)


class _webhook(_NotificationChannel):
    def __init__(self):
        logger.debug(f"{type(self)} instantiated")
        config = configparser.ConfigParser()
        config.read(config_file)
        self.config: Dict[str, str] = config["webhook"]
        logger.info(f"webhook url: {self.config['url']}")

    def notify(self, event: str):
        raise NotImplementedError()
