import pytest
import logging
import re
logger = logging.getLogger(__name__)




@pytest.fixture(scope="session")
def precheck_k8s_vms(k8shosts):
    k8s_vms_ready = True
    for i in range(1, len(k8shosts)):
        k8shost = k8shosts['m{}'.format(i)]['host']
        logger.info("Check to make sure master and API server are reachable {}".format(hostname))
        if not k8shost.check_k8s_master_ready():
            k8s_vms_ready = False
    assert k8s_vms_ready
