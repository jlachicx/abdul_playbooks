from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
import six


CLUSTER_NAME_REGEX = (r'^(?P<cluster_type>[a-z]+(stor|test)?)'
                      r'(-)?'
                      r'(?P<dc>[a-z]{3}[0-9]{2})')


def _parse_cluster_or_host(name):
    match = re.match(CLUSTER_NAME_REGEX, name)
    if not match:
        return None

    return match.groupdict()


def _find_region_peer_clusters(regions, name):
    peers = []
    host_info = _parse_cluster_or_host(name)

    if not host_info:
        raise AnsibleError(
            'Cannot parse host/cluster name %r' % name)

    for region, region_dcs in six.iteritems(regions):
        if not region_dcs:
            continue
        if host_info['dc'] not in region_dcs:
            continue

        for region_dc, dc_clusters in six.iteritems(region_dcs):
            if not dc_clusters:
                continue

            for cluster in dc_clusters:
                cluster_info = _parse_cluster_or_host(cluster)

                # Don't include differing cluster types
                if cluster_info['cluster_type'] != host_info['cluster_type']:
                    continue

                # Don't include the same cluster we're a part of
                if name[0:len(cluster)] == cluster:
                    continue

                peers.append(cluster)

    return peers


class LookupModule(LookupBase):
    """Looks up cluster peers for the provided cluster or node name.

    These are defined in an accompanying YAML file, and this lookup will only
    match clusters of the same type together (e.g., stxf matches with stxf, but
    won't match to stbf, stxm, ccistor, etc.). The originating cluster also
    will *not* be included in the results.

    """
    def run(self, terms, variables=None, **kwargs):
        # Note: 'name' is a more appropriate arg name here since we can look up
        # given either a cluster or host name, but that's a reserved arg name
        # in Ansible lookups.
        if not kwargs.get('regions'):
            raise AnsibleError(
                'The regions argument is required for region peer lookups.')
        if not kwargs.get('hostname'):
            raise AnsibleError(
                'The hostname argument is required for region peer lookups.')

        return _find_region_peer_clusters(kwargs['regions'],
                                          kwargs['hostname'])


# # Test cases
# if __name__ == '__main__':
#     test_cases = [
#         'stxf-mex0101',
#         'stxf-mex0101a',
#         'stxf-mex0201a',
#         'stxf-sao0106d',
#         'ccistormon0101a',
#         'ccistorsng0101b',
#         'ccistorsng0201c',
#         'intstortok0201a',
#         'stxm-tok0401',
#         'stxm-tok0401a',
#         'stbf-utp0701',
#         'natestdal0501',
#         'natestdal0502',
#         'natestmon0101',
#     ]
#
#     for test_host in test_cases:
#         info = _parse_cluster_or_host(test_host)
#         print(
#             '*** %s (%s/%s) ***' %
#             (test_host, info['dc'], info['cluster_type']))
#         for peer in _find_region_peer_clusters(test_host):
#             print('  - %s' % peer)
#         print()
