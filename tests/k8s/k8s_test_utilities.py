import logging
import time
import yaml
import re

from tests.common.helpers.assertions import pytest_assert

logger = logging.getLogger(__name__)


KUBECONFIG_PATH = /etc/sonic/kube_admin.conf


def join_master(duthost, master_vip):
    """
    Joins DUT to Kubernetes master

    Args:
        duthost: DUT host object
        master_vip: VIP of high availability Kubernetes master

    If join fails, test will fail at the assertion to check_connected
    """
    logger.info("Joining DUT to Kubernetes master")
    dut_join_cmds = ['sudo config kube server disable on',
                     'sudo config kube server ip {}'.format(master_vip),
                     'sudo config kube server disable off']
    duthost.shell_cmds(cmds=dut_join_cmds)
    pytest_assert(poll_for_status_change(duthost, True),"DUT failed to successfully join Kubernetes master")
    

def make_vip_unreachable(duthost, master_vip):
    """
    Makes Kubernetes master VIP unreachable from SONiC DUT by configuring iptables rules. Cleans preexisting iptables rules for VIP. 

    Args:
        duthost: DUT host object
        master_vip: VIP of high availability Kubernetes master
    """
    logger.info("Making Kubernetes master VIP unreachable from DUT")
    clean_vip_iptables_rules(duthost, master_vip)
    duthost.shell('sudo iptables -A INPUT -s {} -j DROP'.format(master_vip))
    duthost.shell('sudo iptables -A OUTPUT -d {} -j DROP'.format(master_vip))


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
    Removes all iptables rules associated with the VIP.

    Args:
        duthost: DUT host object
        master_vip: VIP of high availability Kubernetes master
    """
    iptables_rules = duthost.shell('sudo iptables -S | grep {} || true'.format(master_vip))["stdout_lines"]
    logger.info('iptables rules: {}'.format(iptables_rules))
    for line in iptables_rules:
        if line: 
            duthost.shell('sudo iptables -D {}'.format(line[2:]))


def check_connected(duthost, exp_status):
    """
    Checks if the DUT already shows status 'connected' to Kubernetes master
    
    Args:
        duthost: DUT host object
    
    Returns:
        True if connected, False if not connected
    """
    kube_server_status = duthost.shell('show kube server status')["stdout_lines"]
    logger.info("Kube server status: {}".format(kube_server_status))
    for line in kube_server_status:
        if line.contains(exp_status)
            return True

def check_feature_owner(duthost, feature, exp_owner):
    kube_owner_status = duthost.shell('show feature status {}'.format(feature))
    logger.info("Kube feature {} owner status: {}".format(feature, kube_owner_status))
    for line in kube_owner_status:
        if line.startswith(''.format(feature)):
            return line.endswith(exp_owner)

def poll_for_status_change(duthost, status_to_check, exp_status, feature=None, poll_wait_secs=5, min_wait_time=20, max_wait_time=120):
    """
    Polls to see if kube server connected status updates as expected

    Args:
        duthost: DUT host object
        exp_status: expected server connected status once processes are synced
        poll_wait_secs: seconds between each server connected status poll. Default: 5 seconds
        min_wait_time: seconds before starting poll of server connected status. Default: 20 seconds
        max_wait_time: maximum amount of time to spend polling for status change. Default: 120 seconds

    Returns: 
        True if server connected status updates as expected by max_wait_time
        False if server connected status fails to update as expected by max_wait_time
    """
    time.sleep(min_wait_time)
    timeout_wait_secs = max_wait_time - min_wait_time
    while (timeout_wait_secs > 0):
<<<<<<< HEAD
        if (status_to_check == 'connected'):
            if (check_connected(duthost, exp_status)):
                logging.info("Time taken to update status: {} seconds".format(timeout_wait_secs))
                return True
        elif (status_to_check == 'feature_owner'):
            if (check_feature_owner(duthost, exp_status, feature)):
                logging.info("Time taken to update status: {} seconds".format(timeout_wait_secs))
                return True
=======
       if (check_connected(duthost) == exp_status):
           logging.info("Time taken to update Kube server status: {} seconds".format(timeout_wait_secs))
           return True
>>>>>>> upstream/master
       time.sleep(poll_wait_secs)
       timeout_wait_secs -= poll_wait_secs
    return False

def apply_manifest(duthost, k8scluster, feature, version, valid_url):
    feature_manifest_path = "{}/{}.yaml".format(MANIFESTS_PATH, feature)
    fill_manifest_template(duthost, feature_manifest_path, version, valid_url)
    duthost.shell('kubectl --kubeconfig={} apply -f {}'.format(KUBECONFIG_PATH, feature_manifest_path))

def fill_manifest_template(duthost, k8scluster, feature_manifest_template, version, valid_url):
    registry_address = '{}:5000'.format(k8scluster.get_master_vip())
    with open(feature_manifest_template) as f:
        manifest_data = yaml.safe_load(f)
    manifest_data['metadata']['name'] = '{}-v{}'.format(feature, version)
    if valid_url:
        manifest_data['spec']['template']['spec']['containers']['image'] = '{}:{}:{}'.format(registry_address, feature, version)
    else:
        manifest_data['spec']['template']['spec']['containers']['image'] = '{}:{}:{}ext'.format(registry_address, feature, version)
    
def get_feature_version(duthost, feature):
    base_image_version = duthost.os_version.split('.')[0]
    feature_status = duthost.shell('show feature status {} | grep {}'.format(feature, feature)).split()
    for value in feature_status:
        if base_image_version in word:
            feature_version = word
    return feature_version
    