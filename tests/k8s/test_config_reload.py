import pytest
import logging
import time
import k8s_test_utilities as ku
from tests.common.platform.processes_utils import wait_critical_processes

WAIT_FOR_SYNC = 60

logger = logging.getLogger(__name__)

"""when DUT starts as joined to master and config is saved as disable=false, DUT remains joined after config reload"""
def test_config_reload_no_toggle(duthost, k8shosts):
    ku.join_master(duthost, k8shosts) # Assertion within to ensure successful join
    duthost.shell('sudo config reload -y')
    wait_critical_processes(duthost)
    time.sleep(WAIT_FOR_SYNC)

    server_connect_exp_status = True
    server_connect_act_status = ku.check_connected(duthost)
    pytest_assert(server_connect_exp_status == server_connect_act_status, "Unexpected k8s server connection status after config reload, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))


"""when DUT is not connected to master due to unsaved disable=true but config is saved as disable=false, DUT joins after config reload"""
def test_config_reload_toggle_join(duthost, k8shosts):
    ku.join_master(duthost, k8shosts) # Assertion within to ensure successful join
    duthost.shell('sudo config kube server disable on')
    time.sleep(WAIT_FOR_SYNC)

    server_connect_exp_status = False
    server_connect_act_status = ku.check_connected(duthost)
    pytest_assert(server_connect_exp_status == server_connect_act_status, "Unexpected k8s server connection status, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))
    
    duthost.shell('sudo config reload -y')
    wait_critical_processes(duthost)
    time.sleep(WAIT_FOR_SYNC)

    server_connect_exp_status = True
    server_connect_act_status = ku.check_connected(duthost)
    pytest_assert(server_connect_exp_status == server_connect_act_status, "Unexpected k8s server connection status after config reload, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))


"""when DUT starts as joined to master (disable=false) but config is saved as disable=true, DUT resets after config reload"""
def test_config_reload_toggle_reset(duthost, k8shosts):
    ku.join_master(duthost, k8shosts) # Assertion within to ensure successful join
    duthost.shell('sudo config kube server disable on')
    duthost.shell('sudo config save -y')
    time.sleep(WAIT_FOR_SYNC)

    server_connect_exp_status = False
    server_connect_act_status = ku.check_connected(duthost)
    pytest_assert(server_connect_exp_status == server_connect_act_status, "Unexpected k8s server connection status, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))

    duthost.shell('sudo config reload -y')
    wait_critical_processes(duthost)
    time.sleep(WAIT_FOR_SYNC)

    server_connect_exp_status = False
    server_connect_status = ku.check_connected(duthost)
    pytest_assert(server_connect_exp_status == server_connect_act_status, "Unexpected k8s server connection status, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))
