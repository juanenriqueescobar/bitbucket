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
- name: set the branch pattern for deployment
  juanenriqueescobar.bitbucket.deployment_pattern:
    username:    myuser
    password:    password-generated-by-bitbucket
    repository:  myworkspace/myrepo
    state:       present
    deployment:  region-us-east-1
    pattern:     deploy/us-east-1

- name: remove the branch pattern for deployment
  juanenriqueescobar.bitbucket.deployment_pattern:
    username:    myuser
    password:    password-generated-by-bitbucket
    repository:  myworkspace/myrepo
    state:       absent
    deployment:  region-us-east-1
    pattern:     deploy/us-east-1
'''

RETURN = r'''
repository:
    description: The original repository param that was passed in.
    type: str
    returned: always
deployment:
    description: The original deployment param that was passed in.
    type: str
    returned: always
pattern:
    description: The original pattern param that was passed in.
    type: str
    returned: always
result:
    description: the result of the api call
    type: dict
    returned: always
result.body:
    description: body of the api call
    type: dict
    returned: only when result.state is created
result.state:
    description: one of 'created, not changed, deleted, not exists'
    type: str
    returned: always
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
