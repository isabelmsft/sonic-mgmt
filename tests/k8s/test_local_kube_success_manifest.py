import pytest
import logging
import time
import k8s_test_utilities as ku
from tests.common.utilities import wait_until

from tests.common.helpers.assertions import pytest_assert

WAIT_FOR_SYNC = 60

logger = logging.getLogger(__name__)


pytestmark = [
    pytest.mark.disable_loganalyzer,  # disable automatic loganalyzer
]


def test_kube_local_transition(duthost, k8shosts):
    """
    Test case to ensure DUT properly transitions between local mode and kube mode when manifest is properly applied.

    Ensures that DUT is joined to Kubernetes master

    Applies valid manifest for kube mode feature, expect transition from local to kube mode once image is downloaded from ACR

    Configure owner back to local mode, expect transition from kube to local mode

    Configure owner back to kube mode, expect transition from local to kube mode with previously downloaded kube mode image

    Args:
        ensure_manifests_present: Shortcut fixture to ensure that manifests are present on Kubernetes master
        duthost: DUT host object
        k8shosts: shortcut fixture for getting Kubernetes master hosts
    """

    master_vip = k8scluster.get_master_vip()
    ku.join_master(duthost, master_vip) # Assertion within to ensure successful join
    
    feature='snmp'
    version='111'
    ku.apply_manifest(duthost, feature, version, True)

    duthost.shell('sudo config feature owner {} kube'.format(feature))
    ku.poll_for_owner_change(duthost, 'kube')
    assert wait_until(300, 20, duthost.is_service_fully_started, "snmp"), "SNMP service is not running"

    duthost.shell('sudo config feature owner {} local'.format(feature))
    ku.poll_for_owner_change(duthost, 'local')
    assert wait_until(300, 20, duthost.is_service_fully_started, "snmp"), "SNMP service is not running"
    
    duthost.shell('sudo config feature owner {} kube'.format(feature))
    ku.poll_for_owner_change(duthost, 'kube')
    assert wait_until(300, 20, duthost.is_service_fully_started, "snmp"), "SNMP service is not running" ')
    


