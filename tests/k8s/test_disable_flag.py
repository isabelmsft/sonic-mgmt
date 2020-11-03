import pytest
import logging
import time
import k8s_test_utilities as ku

from tests.common.helpers.assertions import pytest_assert

WAIT_FOR_SYNC = 60

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.disable_loganalyzer, # disable automatic loganalyzer
]


def test_disable_flag(duthost, k8shosts):
   ku.join_master(duthost, k8shosts) # Assertion within to ensure successful join

   duthost.shell('sudo config kube server disable on')
   time.sleep(WAIT_FOR_SYNC)

   server_connect_exp_status = False
   server_connect_act_status = ku.check_connected(duthost)
   pytest_assert(server_connect_exp_status == server_connect_act_status, "Test disable flag failed, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))
   
   duthost.shell('sudo config kube server disable off')
   time.sleep(WAIT_FOR_SYNC)

   server_connect_exp_status = True
   server_connect_act_status = ku.check_connected(duthost)
   pytest_assert(server_connect_exp_status == server_connect_act_status, "Test disable flag failed, Expected server connected status: {}, Found server connected status: {}".format(server_connect_exp_status, server_connect_act_status))
