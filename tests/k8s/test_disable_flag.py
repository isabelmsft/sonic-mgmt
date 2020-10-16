import pytest
import logging
import time
import k8s_test_utilities as ku

WAIT_FOR_SYNC = 60

logger = logging.getLogger(__name__)


 def test_disable_flag(precheck_k8s_vms, duthost, k8shosts):
    ku.join_master(duthost, k8shosts) # Assertion within to ensure successful join

    duthost.shell('sudo config kube server disable on')
    time.sleep(WAIT_FOR_SYNC)

    server_connect_status = ku.check_connected(duthost)
    pytest_assert(not server_connect_status, "DUT disable flag failed, Expected server connected status: false, Found server connected status: {}".format(server_connect_status))

    duthost.shell('sudo config kube server disable off')
    time.sleep(WAIT_FOR_SYNC)

    server_connect_status = ku.check_connected(duthost)
    pytest_assert(server_connect_status, "DUT disable flag failed, Expected server connected status: true, Found server connected status: {}".format(server_connect_status))

