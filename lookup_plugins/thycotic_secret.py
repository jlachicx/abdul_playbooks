from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import ssl

# from ansible.errors import AnsibleError, AnsibleParserError
# from ansible.module_utils._text import to_text
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
import suds

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


TOKEN_FILE = os.path.expanduser('~/.config/thycotic.token')


def save_token(token):
    try:
        os.makedirs(os.path.dirname(TOKEN_FILE))
    except Exception:
        pass

    with open(TOKEN_FILE, 'w') as ff:
        ff.write('')

    os.chmod(TOKEN_FILE, 0o600)
    print(TOKEN_FILE)
    print('%r' % token)
    with open(TOKEN_FILE, 'w') as ff:
        ff.write(token)


def load_token():
    if not os.path.exists(TOKEN_FILE):
        return

    return open(TOKEN_FILE, 'r').read()


def secret_field(secret, field_name):
    fld = [x for x in secret.Items.SecretItem if x.FieldName == field_name]
    if not fld:
        return None
    return fld[0]


def secret_field_value(secret, field_name):
    fld = secret_field(secret, field_name)
    if not fld:
        return None
    return str(fld.Value)


def transform_secret(secret, result=None):
    if (secret.SecretTypeId in (6042, 6046) or
            (result and result.secretTypeName == 'UNIXIS-local-user')):
        return {
            'user': secret_field_value(secret, 'principal'),
            'password': secret_field_value(secret, 'password'),
            'host': secret_field_value(secret, 'machine'),
            'key': secret_field_value(secret, 'key'),
            'name': secret.Name,
            'type': result.SecretTypeName if result else None,
            'type_id': secret.SecretTypeId,
        }
    elif secret.SecretTypeId == 2:
        return {
            'user': secret_field_value(secret, 'Username'),
            'password': secret_field_value(secret, 'Password'),
            'host': secret_field_value(secret, 'Resource'),
            'key': secret.Name,
            'name': secret.Name,
            'type': result.SecretTypeName if result else None,
            'type_id': secret.SecretTypeId,
        }
    elif secret.SecretTypeId == 7066:  # Netapp-ONTAP-login
        return {
            'user': secret_field_value(secret, 'Username'),
            'password': secret_field_value(secret, 'Password'),
            'host': secret_field_value(secret, 'Hostname'),
            'key': secret.Name,
            'name': secret.Name,
            'type': result.SecretTypeName if result else None,
            'type_id': secret.SecretTypeId,
        }

    return None


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        field = kwargs['field']
        url = kwargs['url']
        result = []

        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context

        client = suds.client.Client(url)
        token = load_token()

        secret = client.service.GetSecret(token, kwargs['secret'])
        if secret.Errors:
            raise AnsibleError("Thycotic API Error: %s" % secret.Errors[0][0])

        if 'SecretError' in secret:
            raise AnsibleError("Thycotic Secret Error: %s" %
                               secret.SecretError)

        simple_secret = transform_secret(secret.Secret)
        result.append(simple_secret[field])

        return result
