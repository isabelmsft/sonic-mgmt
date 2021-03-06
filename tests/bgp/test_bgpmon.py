import pytest
import logging
from netaddr import IPNetwork
import ptf.testutils as testutils
from jinja2 import Template
import ptf.packet as scapy
from ptf.mask import Mask
import json
from tests.common.fixtures.ptfhost_utils import change_mac_addresses      # lgtm[py/unused-import]
from tests.common.fixtures.ptfhost_utils import remove_ip_addresses       # lgtm[py/unused-import]
from tests.common.helpers.generators import generate_ips as generate_ips
from tests.common.helpers.assertions import pytest_assert

pytestmark = [
    pytest.mark.topology('any'),
]

BGPMON_TEMPLATE_FILE = 'bgp/templates/bgpmon.j2'
BGPMON_CONFIG_FILE = '/tmp/bgpmon.json'
BGP_PORT = 179
BGP_CONNECT_TIMEOUT = 121
ZERO_ADDR = r'0.0.0.0/0'

logger = logging.getLogger(__name__)

def route_through_default_routes(host, ip_addr):
    output = host.shell("show ip route {} json".format(ip_addr))['stdout']
    routes_info = json.loads(output)
    ret = True
    for prefix in routes_info.keys():
        if prefix != ZERO_ADDR:
            ret = False
            break
    return ret

def generate_ip_through_default_route(host):
    # Generate an IP address routed through default routes
    for leading in range(11, 255):
        ip_addr = generate_ips(1, "{}.0.0.1/24".format(leading), [])[0]
        if route_through_default_routes(host, ip_addr):
            return ip_addr
    return None

def get_default_route_ports(host):
    mg_facts = host.minigraph_facts(host=host.hostname)['ansible_facts']
    route_info = json.loads(host.shell("show ip route {} json".format(ZERO_ADDR))['stdout'])
    ports = []
    for route in route_info[ZERO_ADDR]:
        if route['protocol'] != 'bgp':
            continue
        for itfs in route['nexthops']:
            ports.append(itfs['interfaceName'])
    port_indices = []
    for port in ports:
        if 'PortChannel' in port:
            for member in mg_facts['minigraph_portchannels'][port]['members']:
                port_indices.append(mg_facts['minigraph_port_indices'][member])
        else:
            port_indices.append(mg_facts['minigraph_port_indices'][port])
    return port_indices

@pytest.fixture
def common_setup_teardown(duthost, ptfhost):
    peer_addr = generate_ip_through_default_route(duthost)
    pytest_assert(peer_addr, "Failed to generate ip address for test")
    peer_addr = str(IPNetwork(peer_addr).ip)
    peer_ports = get_default_route_ports(duthost)
    mg_facts = duthost.minigraph_facts(host=duthost.hostname)['ansible_facts']
    local_addr = mg_facts['minigraph_lo_interfaces'][0]['addr']
    # Assign peer addr to an interface on ptf
    logger.info("Generated peer address {}".format(peer_addr))
    bgpmon_args = {
        'peer_addr': peer_addr,
        'asn': mg_facts['minigraph_bgp_asn'],
        'local_addr': local_addr,
        'peer_name': 'bgp_monitor'
    }
    bgpmon_template = Template(open(BGPMON_TEMPLATE_FILE).read())
    duthost.copy(content=bgpmon_template.render(**bgpmon_args),
                 dest=BGPMON_CONFIG_FILE)
    yield local_addr, peer_addr, peer_ports
    # Cleanup bgp monitor
    duthost.shell("redis-cli -n 4 -c DEL 'BGP_MONITORS|{}'".format(peer_addr))
    duthost.file(path=BGPMON_CONFIG_FILE, state='absent')

def build_syn_pkt(local_addr, peer_addr):
    pkt = testutils.simple_tcp_packet(
        pktlen=54,
        ip_src=local_addr,
        ip_dst=peer_addr,
        tcp_dport=BGP_PORT,
        tcp_flags="S"
    )
    exp_packet = Mask(pkt)
    exp_packet.set_do_not_care_scapy(scapy.Ether, "dst")
    exp_packet.set_do_not_care_scapy(scapy.Ether, "src")

    exp_packet.set_do_not_care_scapy(scapy.IP, "version")
    exp_packet.set_do_not_care_scapy(scapy.IP, "ihl")
    exp_packet.set_do_not_care_scapy(scapy.IP, "tos")
    exp_packet.set_do_not_care_scapy(scapy.IP, "len")
    exp_packet.set_do_not_care_scapy(scapy.IP, "flags")
    exp_packet.set_do_not_care_scapy(scapy.IP, "id")
    exp_packet.set_do_not_care_scapy(scapy.IP, "frag")
    exp_packet.set_do_not_care_scapy(scapy.IP, "ttl")
    exp_packet.set_do_not_care_scapy(scapy.IP, "chksum")
    exp_packet.set_do_not_care_scapy(scapy.IP, "options")

    exp_packet.set_do_not_care_scapy(scapy.TCP, "sport")
    exp_packet.set_do_not_care_scapy(scapy.TCP, "seq")
    exp_packet.set_do_not_care_scapy(scapy.TCP, "ack")
    exp_packet.set_do_not_care_scapy(scapy.TCP, "reserved")
    exp_packet.set_do_not_care_scapy(scapy.TCP, "dataofs")
    exp_packet.set_do_not_care_scapy(scapy.TCP, "window")
    exp_packet.set_do_not_care_scapy(scapy.TCP, "chksum")
    exp_packet.set_do_not_care_scapy(scapy.TCP, "urgptr")

    exp_packet.set_ignore_extra_bytes()
    return exp_packet

def test_bgpmon(duthost, common_setup_teardown, ptfadapter):
    """
    Add a bgp monitor on ptf and verify that DUT is attempting to establish connection to it
    """
    local_addr, peer_addr, peer_ports = common_setup_teardown
    exp_packet = build_syn_pkt(local_addr, peer_addr)
    # Load bgp monitor config
    logger.info("Configured bgpmon and verifying packet on {}".format(peer_ports))
    duthost.command("sonic-cfggen -j {} -w".format(BGPMON_CONFIG_FILE))
    # Verify syn packet on ptf
    testutils.verify_packet_any_port(test=ptfadapter, pkt=exp_packet, ports=peer_ports, timeout=BGP_CONNECT_TIMEOUT)

def test_bgpmon_no_resolve_via_default(duthost, common_setup_teardown, ptfadapter):
    """
    Verify no syn for BGP is sent when 'ip nht resolve-via-default' is disabled.
    """
    local_addr, peer_addr, peer_ports = common_setup_teardown
    exp_packet = build_syn_pkt(local_addr, peer_addr)
    # Load bgp monitor config
    logger.info("Configured bgpmon and verifying no packet on {} when resolve-via-default is disabled".format(peer_ports))
    try:
        # Disable resolve-via-default
        duthost.command("vtysh -c \"configure terminal\" \
                        -c \"no ip nht resolve-via-default\"")
        duthost.command("sonic-cfggen -j {} -w".format(BGPMON_CONFIG_FILE))
        # Verify no syn packet is received
        pytest_assert(0 == testutils.count_matched_packets_all_ports(test=ptfadapter, exp_packet=exp_packet, ports=peer_ports, timeout=BGP_CONNECT_TIMEOUT),
                     "Syn packets is captured when resolve-via-default is disabled")
    finally:
        # Re-enable resolve-via-default
        duthost.command("vtysh -c \"configure terminal\" \
                        -c \"ip nht resolve-via-default\"")

