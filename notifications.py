import logging
from typing import Dict, List

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
        for channel in self.notification_channels:
            logger.debug(f"notifying {channel} about {event['type']}")
            channel.notify(event)


class _NotificationChannel(object):
    def __init__(self):
        raise NotImplementedError

    def notify(self, event: Dict[str, str]):
        raise NotImplementedError


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
