import pytest
import logging
import time
import k8s_test_utilities.py as ku

WAIT_FOR_SYNC = 60

logger = logging.getLogger(__name__)

# def make_vip_unreachable(duthost, master_vip):
#     duthost.shell('sudo iptables -A INPUT -s {} -j DROP'.format(master_vip))
#     duthost.shell('sudo iptables -A OUTPUT -d {} -j DROP'.format(master_vip))

# def make_vip_reachable(duthost, master_vip):
#     duthost.shell('sudo iptables -D INPUT -s {} -j DROP'.format(master_vip))
#     duthost.shell('sudo iptables -D OUTPUT -d {} -j DROP'.format(master_vip))

# def shutdown_all_api_server(k8shosts):
#     for i in range(1, len(k8shosts)):
#         k8shost = k8shosts['m{}'.format(i)]['host']
#         logger.info("Shutting down API Server on master node m{}".format(i))
#         k8shost.shutdown_api_server()

# def start_all_api_server(k8shosts):
#     for i in range(1, len(k8shosts)):
#         k8shost = k8shosts['m{}'.format(i)]['host']
#         logger.info("Starting API Server on master node m{}".format(i))
#         k8shost.start_api_server()


# def check_connected(duthost, expected_status):
#     kube_server_status = duthost.shell('show kube server')["stdout"].split("\n")
#     logger.info("Kube server status: {}".format(kube_server_status))
#     for line in kube_server_status:
#         if line.startswith("KUBERNETES_MASTER SERVER connected"):
#             assert line.endswith(str(expected_status).lower())
#             break

def test_join_available_master(precheck_k8s_vms, duthost, k8shosts):
    
    duthost.shell('sudo config kube server disable on')
    master_vip = k8shosts['ha']['host'].ip_addr
    ku.make_vip_unreachable(duthost, master_vip)
    ku.shutdown_all_api_server(k8shosts)
    
    duthost.shell('sudo config kube server disable off') 
    duthost.shell('sudo config kube server ip {}'.format(master_vip))
    time.sleep(WAIT_FOR_SYNC)
    
    server_connect_status = ku.check_connected(duthost)
    pytest_assert(not server_connect_status, "DUT join available master failed, Expected server connected status: false, Found server connected status: {}".format(server_connect_status))

    ku.make_vip_reachable(duthost, master_vip)
    time.sleep(WAIT_FOR_SYNC)
    
    server_connect_status = ku.check_connected(duthost)
    pytest_assert(not server_connect_status, "DUT join available master failed, Expected server connected status: false, Found server connected status: {}".format(server_connect_status))

    ku.start_all_api_server(k8shosts)
    time.sleep(WAIT_FOR_SYNC)
    
    server_connect_status = ku.check_connected(duthost)
    pytest_assert(server_connect_status, "DUT join available master failed, Expected server connected status: true, Found server connected status: {}".format(server_connect_status))


