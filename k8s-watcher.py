import logging
from kubernetes import client, config, watch
from notifications import NotificationManager
import argparse

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("k8s_watch")

config.load_kube_config()
v1 = client.CoreV1Api()
w = watch.Watch()

try:
    namespace = config.kube_config.list_kube_config_contexts()[0][0]["context"]["namespace"]
except:
    try:
        namespace = config.kube_config.list_kube_config_contexts()[0][0]["context"]["user"]
    except:
        namespace = ""

default_events_to_notify = ["ERROR", "DONE", "DELETED"] #  "ADDED", "MODIFIED"
default_ways_to_notify = ["rocketchat"]  # rocketchat, discord, telegram, email, whatev

parser = argparse.ArgumentParser()
parser.add_argument("--namespace", type=str, default=namespace, help="the namespace to watch for changes")
parser.add_argument("--events_to_notify", type=str, nargs="+", default=default_events_to_notify, help="ERROR DONE ADDED DELETED MODIFIED")
parser.add_argument("--notification_channels", type=str, nargs="+", default=default_ways_to_notify, help="implement new ones in notifications.py")

pargs = parser.parse_args()

logger.info(f"watching namespace {pargs.namespace}")
logger.info(f"notification triggers {pargs.events_to_notify}")
logger.info(f"notification channels {pargs.notification_channels}")

not_man = NotificationManager(pargs.notification_channels)
logger.info("start watching cluster")
while True:
    for e in w.stream(v1.list_namespaced_pod, namespace=namespace, _preload_content=False):
        if e["type"] == "ERROR" and e["raw_object"]["message"].contains("too old resource"):
            logger.warning("Going to restart as 'watch' lost connection. Going to relist all existing pods:")
            continue
        logger.info(f"Event '{e['type']}' for pod '{e['object'].metadata.name}'")
        logger.debug(str(e))
        if e["type"] in pargs.events_to_notify:
            not_man.notify(e)
            # TODO v1.read_namespaced_pod_log()
            # append last 5 lines of logs
