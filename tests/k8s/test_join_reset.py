import pytest
import logging
import time

WAIT_FOR_SYNC = 60

logger = logging.getLogger(__name__)

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


def check_connected(duthost, expected_status):
    kube_server_status = duthost.shell('show kube server')["stdout"].split("\n")
    logger.info("Kube server status: {}".format(kube_server_status))
    for line in kube_server_status:
        if line.startswith("KUBERNETES_MASTER SERVER connected"):
            assert line.endswith(str(expected_status).lower())
            break

def test_join_available_master(precheck_k8s_vms, duthost, k8shosts):
    duthost.shell('sudo config kube server disable on')
    master_vip = k8shosts['ha']['host'].ip_addr

    make_vip_unreachable(duthost, master_vip)
    shutdown_all_api_server(k8shosts)
    duthost.shell('sudo config kube server disable off') 
    
    duthost.shell('sudo config kube server ip {}'.format(master_vip))
    time.sleep(WAIT_FOR_SYNC)
    check_connected(duthost, False)

    make_vip_reachable(duthost, master_vip)
    time.sleep(WAIT_FOR_SYNC)
    check_connected(duthost, False)

    start_all_api_server(k8shosts)
    time.sleep(WAIT_FOR_SYNC)
    check_connected(duthost, True)


# def test_disable_flag(precheck_masters, duthost):
#    """join master when disable=false and reset from master when disable=true"""

# def test_config_reload(precheck_masters, duthost):
#    """when DUT starts as joined to master and config is saved as disable=false, DUT remains joined after config reload"""

# def test_config_reload_toggle_join(precheck_masters, duthost):
#    """when DUT starts as not joined to master (disable=true) but config is saved as disable=false, DUT joins after config reload"""

# def test_config_reload_toggle_reset(precheck_masters, duthost):
#    """when DUT starts as joined to master (disable=false) but config is saved as disable=true, DUT resets after config reload"""


