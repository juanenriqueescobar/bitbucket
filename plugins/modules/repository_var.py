#!/usr/bin/python

# Copyright: (c) 2020, Juan Enrique Escobar <https://github.com/juanenriqueescobar>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: repository_var

short_description: create a deployment in repository

version_added: "0.0.0"

description: create a deployment in repository

options:
    username:
        description: The bitbucket username
        required: true
        type: str
    password:
        description: The bitbucket password
        required: true
        type: str
    repository:
        description: The workspace/repo
        required: true
        type: str
    state:
        description: create or remove the deployment
        type: str
        default: present
        choices: ['present', 'absent']
    var_name:
        description: the name of the var
        required: true
        type: str
    var_value:
        description: the value of the var
        type: str
        default: ''
    var_secured:
        description: if var is hidden, only pipelines can see the value
        type: bool
        default: false

author:
    - Juan Enrique Escobar Robles (@juanenriqueescobar)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test_info:
    name: hello world
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
my_useful_info:
    description: The dictionary containing information about your system.
    type: dict
    returned: always
    sample: {
        'foo': 'bar',
        'answer': 42,
    }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juanenriqueescobar.bitbucket.plugins.module_utils.bitbucket_client import BitbucketClient, BitbucketClientException

client = None
repository = None


def phase_3(name, repository_var):
    # find especific var in list

    for item in repository_var:
        if item['key'] == name:
            return item.get('uuid'), item.get('value'), item.get('secured')
    return '', '', False


def present(data):
    # crea o actualiza las variables del repository

    has_changed = False
    result = {}

    try:
        repository_var = client.getRepositoryVars(repository)

        uuid, value, secured = phase_3(data['var_name'], repository_var)

        # la var no existe, hay que crearla
        if len(uuid) == 0:
            d = {
                'key': data['var_name'],
                'value': data['var_value'],
                'secured': data['var_secured'],
            }
            body = client.createRepositoryVar(
                repository, d)
            has_changed = True
            result = {
                'state': 'created',
                'body': body,
            }

        # la var existe, pero es segura, no hacemos nada!!!
        elif secured:
            result = {
                'state': 'hidden',
                'body': {
                    'key': data['var_name'],
                    'secured': True,
                    'type': 'pipeline_variable',
                    'uuid': uuid,
                },
            }

        # la var existe, hay que actualizarla
        elif value != data['var_value']:
            d = {
                'key': data['var_name'],
                'value': data['var_value'],
                'secured': data['var_secured'],
            }
            body = client.updateRepositoryVar(
                repository, uuid, d)
            has_changed = True
            result = {
                'state': 'updated',
                'body': body,
            }
        else:
            result = {
                'state': 'not changed',
                'body': {
                    'key': data['var_name'],
                    'secured': False,
                    'type': 'pipeline_variable',
                    'uuid': uuid,
                    'value': data['var_value'],
                },
            }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message}

    return False, has_changed, {'repo': repository, 'result': result}


def absent(data=None):

    has_changed = False
    result = {}

    try:
        repository_var = client.getRepositoryVars(repository)

        uuid, value, secured = phase_3(data['var_name'], repository_var)

        # la var existe!, hay q borrarla
        if len(uuid) != 0:
            client.removeRepositoryVar(
                repository, uuid)
            has_changed = True
            result = {
                'state': 'deleted',
            }
        else:
            result = {
                'state': 'not exists',
            }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message}

    return False, has_changed, {'repo': repository, 'result': result}


def main():

    fields = {
        'username': {
            'required': True,
            'type': 'str',
        },
        'password': {
            'required': True,
            'type': 'str',
            'no_log': True,
        },
        'repository': {
            'required': True,
            'type': 'str',
        },
        'state': {
            'default': 'present',
            'choices': ['present', 'absent'],
            'type': 'str'
        },
        'var_name': {
            'required': True,
            'type': 'str',
        },
        'var_value': {
            'type': 'str',
            'default': '',
        },
        'var_secured': {
            'type': 'bool',
            'default': False
        },
    }

    choice_map = {
        'present': present,
        'absent': absent,
    }

    module = AnsibleModule(argument_spec=fields)

    global client
    client = BitbucketClient(
        module.params['username'], module.params['password'])

    global repository
    repository = module.params['repository']

    has_failed, has_changed, result = choice_map.get(
        module.params['state'])(module.params)

    if has_failed:
        module.fail_json(msg='Error', meta=result)
    else:
        module.exit_json(changed=has_changed, meta=result)


if __name__ == '__main__':
    main()
