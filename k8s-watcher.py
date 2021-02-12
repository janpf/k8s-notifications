import logging
from kubernetes import client, config, watch
from notifications import NotificationManager

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s.%(msecs)03d %(levelname)s %(module)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("k8s_watch")

config.load_kube_config()
v1 = client.CoreV1Api()
w = watch.Watch()

# TODO make argparse settable
namespace = config.kube_config.list_kube_config_contexts()[0][0]["context"]["namespace"]
events_to_notify = ["ERROR", "DONE", "ADDED"]
ways_to_notify = ["rocketchat"]  # rocketchat, discord, telegram, email, whatev


logger.info(f"watching namespace {namespace}")
logger.info(f"notification triggers {events_to_notify}")
logger.info(f"notification channels {ways_to_notify}")

not_man = NotificationManager(ways_to_notify)

logger.info("start watching cluster")
while True:
    for e in w.stream(v1.list_namespaced_pod, namespace=namespace):
        if e["type"] == "ERROR" and e["raw_object"]["message"].contains("too old resource"):
            logger.warning("Going to restart as 'watch' lost connection. Going to relist all existing pods:")
            continue
        logger.info(f"Event '{e['type']}' for pod '{e['object'].metadata.name}'")
        if e["type"] in events_to_notify:
            not_man.notify(e)
