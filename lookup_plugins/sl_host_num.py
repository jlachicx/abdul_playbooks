from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


NODE_NUMERAL_START = ord('a')
NODE_NUMERAL_END = ord('z')
NODE_NUMERALS = ''.join([chr(x) for x in range(NODE_NUMERAL_START,
                                               NODE_NUMERAL_END + 1)])


def _node_letter_to_number(suffix):
    """Convert a letter-based node suffix numeral to a number.

    :param suffix(str): A node's letter-based suffix, for instance 'a' or 'cr'.
    """
    suffix = suffix if suffix is not None else ''
    basenchars = NODE_NUMERALS
    base10chars = '0123456789'
    node_num = 0
    for ii in range(0, len(suffix)):
        node_num = (node_num * len(basenchars) +
                    (basenchars.index(suffix[ii]) + 1))

    res = base10chars[0]  # default to 0
    if node_num != 0:
        res = ''
        while node_num > 0:
            c = node_num % len(base10chars)
            res = base10chars[c] + res
            node_num = int(node_num // len(base10chars))

    return int(res)


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        letter = kwargs['letter']
        as_str = kwargs.get('as_str', False)
        val = _node_letter_to_number(letter)

        if as_str:
            val = str(val)

        return [val]
