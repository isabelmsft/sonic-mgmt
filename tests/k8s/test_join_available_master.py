import pytest
import logging
import time
import k8s_test_utilities as ku

from tests.common.helpers.assertions import pytest_assert

WAIT_FOR_SYNC = 60

logger = logging.getLogger(__name__)

def make_vip_reachable(duthost, master_vip):
    """
    Makes Kubernetes master VIP reachable from SONiC DUT by removing any iptables rules associated with the VIP. 

    Args:
        duthost: DUT host object
        master_vip: VIP of high availability Kubernetes master
    """
    logger.info("Making Kubernetes master VIP reachable from DUT")
    clean_vip_iptables_rules(duthost, master_vip)


def clean_vip_iptables_rules(duthost, master_vip):
    """
    Removes all iptables ruls associated with the VIP.

    Args:
        duthost: DUT host object
        master_vip: VIP of high availability Kubernetes master
    """
    iptables_rules = duthost.shell('sudo iptables -S | grep {}'.format(master_vip))["stdout"].split("\n")
    for line in iptables_rules:
        duthost.shell('sudo iptables -D {}'.format(line[2:]))

pytestmark = [
    pytest.mark.disable_loganalyzer,  # disable automatic loganalyzer
]


def test_join_available_master(duthost, k8shosts):
    """
    Test case to ensure DUT properly joins Kubernetes master once VIP and API servers are both reachable

    Makes VIP unreachable, shuts down API server on all backend master servers

    Attempts to join DUT by configuring VIP and enabling kube server connection

    Ensures that DUT joins master only after VIP and API servers are both made available

    Args:
        duthost: DUT host object
        k8shosts: shortcut fixture for getting Kubernetes master hosts
    """

    master_vip = k8shosts['ha']['host'].ip_addr
    duthost.shell('sudo config kube server disable on')
    make_vip_unreachable(duthost, master_vip)
    ku.shutdown_all_api_server(k8shosts)
    time.sleep(WAIT_FOR_SYNC)
    
    duthost.shell('sudo config kube server disable off') 
    duthost.shell('sudo config kube server ip {}'.format(master_vip))
    time.sleep(WAIT_FOR_SYNC)
    
    server_connect_exp_status = False
    server_connect_act_status = ku.check_connected(duthost)
    pytest_assert(server_connect_exp_status == server_connect_act_status, "DUT join available master failed, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))

    make_vip_reachable(duthost, master_vip)
    time.sleep(WAIT_FOR_SYNC)
    
    server_connect_exp_status = False
    server_connect_act_status = ku.check_connected(duthost)
    pytest_assert(server_connect_exp_status == server_connect_act_status, "DUT join available master failed, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))

    ku.start_all_api_server(k8shosts)
    time.sleep(WAIT_FOR_SYNC)
    
    server_connect_exp_status = True
    server_connect_act_status = ku.check_connected(duthost)
    pytest_assert(server_connect_exp_status == server_connect_act_status, "DUT join available master failed, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))


