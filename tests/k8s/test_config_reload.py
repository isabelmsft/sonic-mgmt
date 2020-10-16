import pytest
import logging
import time
import k8s_test_utilities.py as ku

WAIT_FOR_SYNC = 60

logger = logging.getLogger(__name__)

"""when DUT starts as joined to master and config is saved as disable=false, DUT remains joined after config reload"""
def test_config_reload(precheck_k8s_vms, duthost, k8shosts):
    ku.join_master(duthost, k8shosts) # Assertion within to ensure successful join
    duthost.shell('sudo config reload -y')
    server_connect_status = ku.check_connected(duthost)
    pytest_assert(server_connect_status, "Config reload server connected failed, Expected server connected status: true, Found server connected status: {}".format(server_connect_status))


"""when DUT starts as not joined to master (disable=true) but config is saved as disable=false, DUT joins after config reload"""
def test_config_reload_toggle_join(precheck_k8s_vms, duthost, k8shosts):
    ku.join_master(duthost, k8shosts) # Assertion within to ensure successful join
    duthost.shell('sudo config kube server disable on')
    time.sleep(WAIT_FOR_SYNC)

    server_connect_status = ku.check_connected(duthost)
    pytest_assert(not server_connect_status, "DUT disable flag failed, Expected server connected status: false, Found server connected status: {}".format(server_connect_status))
    
    duthost.shell('sudo config reload -y')
    server_connect_status = ku.check_connected(duthost)
    pytest_assert(server_connect_status, "Config reload server connected failed, Expected server connected status: true, Found server connected status: {}".format(server_connect_status))


"""when DUT starts as joined to master (disable=false) but config is saved as disable=true, DUT resets after config reload"""
def test_config_reload_toggle_reset(precheck_k8s_vms, duthost, k8shosts):
    ku.join_master(duthost, k8shosts) # Assertion within to ensure successful join
    duthost.shell('sudo config kube server disable on')
    time.sleep(WAIT_FOR_SYNC)

    server_connect_status = ku.check_connected(duthost)
    pytest_assert(not server_connect_status, "DUT disable flag failed, Expected server connected status: false, Found server connected status: {}".format(server_connect_status))
    
    duthost.shell('sudo config save -y')
    duthost.shell('sudo config reload -y')

    server_connect_status = ku.check_connected(duthost)
    pytest_assert(not server_connect_status, "Config reload server connected failed, Expected server connected status: false, Found server connected status: {}".format(server_connect_status))
