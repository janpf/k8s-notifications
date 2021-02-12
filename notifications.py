import logging
from typing import Dict, List
import configparser


logger = logging.getLogger("notification_manager")


class NotificationManager(object):
    def __init__(self, notification_channels: List[str]):
        self.notification_channels = [self._getChannel(val) for val in notification_channels]
        logger.debug(f"found channels: {self.notification_channels}")

    @staticmethod
    def _getChannel(channelName: str):
        import notifications as notif

        cls: notif._NotificationChannel = getattr(notif, "_" + channelName)()
        return cls

    def notify(self, event):
        # TODO clean message
        for channel in self.notification_channels:
            logger.debug(f"notifying {channel} about {event['type']}")
            channel.notify(event)


class _NotificationChannel(object):
    def __init__(self):
        raise NotImplementedError

    def notify(self, event: Dict[str, str]):
        raise NotImplementedError


class _rocketchat(_NotificationChannel):
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("/home/ls6/pfister/.nofconfig")
        self.config: Dict[str, str] = config["rocketchat"]
        self._new_rc_connection()

    def _new_rc_connection(self):
        from rocketchat.api import RocketChatAPI

        self.rc = RocketChatAPI(
            settings={
                "username": self.config["username"],
                "password": self.config["password"],
                "domain": self.config["server"],
            }
        )
        self.im_room = self.rc.create_im_room(self.config["yourUsername"])

    def notify(self, event: Dict[str, str]):
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
        self.url = ""  # where to get from?
        logger.info(f"webhook url: {self.url}")

    def notify(self, event: Dict[str, str]):
        pass


class _discordwebhook(_webhook):
    def notify(self, event: Dict[str, str]):
        pass
