import logging
import time

logger = logging.getLogger(__name__)

WAIT_FOR_SYNC = 60

def join_master(duthost, k8shosts):
    master_vip = k8shosts['ha']['host'].ip_addr
    duthost.shell('sudo config kube server ip {}'.format(master_vip))
    duthost.shell('sudo config kube server disable off')
    time.sleep(WAIT_FOR_SYNC)
    assert check_connected(duthost)
    
def make_vip_unreachable(duthost, master_vip):
    duthost.shell('sudo iptables -A INPUT -s {} -j DROP'.format(master_vip))
    duthost.shell('sudo iptables -A OUTPUT -d {} -j DROP'.format(master_vip))

def make_vip_reachable(duthost, master_vip):
    duthost.shell('sudo iptables -D INPUT -s {} -j DROP'.format(master_vip))
    duthost.shell('sudo iptables -D OUTPUT -d {} -j DROP'.format(master_vip))

def shutdown_all_api_server(k8shosts):
    for i in range(1, len(k8shosts)):
        k8shost = k8shosts['m{}'.format(i)]['host']
        logger.info("Shutting down API Server on master node m{}".format(i))
        k8shost.shutdown_api_server()

def start_all_api_server(k8shosts):
    for i in range(1, len(k8shosts)):
        k8shost = k8shosts['m{}'.format(i)]['host']
        logger.info("Starting API Server on master node m{}".format(i))
        k8shost.start_api_server()

def check_connected(duthost):
    kube_server_status = duthost.shell('show kube server')["stdout"].split("\n")
    logger.info("Kube server status: {}".format(kube_server_status))
    for line in kube_server_status:
        if line.startswith("KUBERNETES_MASTER SERVER connected"):
            return line.endswith("true")
    logger.info("Kubernetes server check_connected failed to identify server status")
