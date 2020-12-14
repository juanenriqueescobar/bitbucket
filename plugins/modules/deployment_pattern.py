#!/usr/bin/python

# Copyright: (c) 2020, Juan Enrique Escobar <https://github.com/juanenriqueescobar>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: deployment_pattern

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
    deployment:
        description: The name of deployment
        required: true
        type: str
    state:
        description: create or remove the deployment
        type: str
        default: present
        choices: ['present', 'absent']
    pattern:
        description: The pattern of the branchs that will use this deployment
        required: true
        type: str

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
deployment = None


def present(data):

    try:
        deployment_uuid = client.getDeploymentUUID(
            repository, deployment)

        uuid = client.getDeploymentPatternUUID(
            repository, deployment_uuid, data['pattern'])

        has_changed = False
        result = None

        if len(uuid) == 0:
            # el deployment no existe lo creamos
            body = client.createDeploymentPattern(
                repository, deployment_uuid, data['pattern'])
            has_changed = True
            result = {
                'state': 'created',
                'body': body,
            }
        else:
            result = {
                'state': 'not changed',
            }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message}

    return False, has_changed, {'repository': repository, 'deployment': deployment, 'pattern': data['pattern'], 'result': result}


def absent(data):

    try:
        deployment_uuid = client.getDeploymentUUID(
            repository, deployment)

        uuid = client.getDeploymentPatternUUID(
            repository, deployment_uuid, data['pattern'])

        has_changed = False
        result = None

        if len(uuid) != 0:
            client.removeDeploymentPattern(
                repository, deployment_uuid, uuid)
            has_changed = True
            result = {
                'state': 'deleted',
                'uuid': uuid,
            }
        else:
            result = {
                'state': 'not exists',
            }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message}

    return False, has_changed, {'repository': repository, 'deployment': deployment, 'pattern': data['pattern'], 'result': result}


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
        'deployment': {
            'required': True,
            'type': 'str',
        },
        'state': {
            'default': 'present',
            'choices': ['present', 'absent'],
            'type': 'str'
        },
        'pattern': {
            'required': True,
            'type': 'str',
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

    global repository, deployment
    repository = module.params['repository']
    deployment = module.params['deployment']

    has_failed, has_changed, result = choice_map.get(
        module.params['state'])(module.params)

    if has_failed:
        module.fail_json(msg='Error', meta=result)
    else:
        module.exit_json(changed=has_changed, meta=result)


if __name__ == '__main__':
    main()
