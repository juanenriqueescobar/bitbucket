#!/usr/bin/python

# Copyright: (c) 2020, Juan Enrique Escobar <https://github.com/juanenriqueescobar>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: pipelines_enabled

short_description: create a deployment in repository

version_added: "0.0.5"

description: enable or disable pipelines in repository

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

author:
    - Juan Enrique Escobar Robles (@juanenriqueescobar)
'''

EXAMPLES = r'''
- name: enable pipelines
  juanenriqueescobar.bitbucket.pipelines_enabled:
    username:    myuser
    password:    password-generated-by-bitbucket
    repository:  myworkspace/myrepo
    state:       present

- name: disable pipelines
  juanenriqueescobar.bitbucket.pipelines_enabled:
    username:    myuser
    password:    password-generated-by-bitbucket
    repository:  myworkspace/myrepo
    state:       absent
'''

RETURN = r'''
repository:
    description: The original repository param that was passed in.
    type: str
    returned: always
result:
    description: the result of the api call
    type: dict
    returned: always
result.body:
    description: body of the api call
    type: dict
    returned: only on enabled or disabled state
result.state:
    description: one of 'enabled, disabled, not changed'
    type: str
    returned: always

'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.juanenriqueescobar.bitbucket.plugins.module_utils.bitbucket_client import BitbucketClient, BitbucketClientException

client = None
repository = None


def present(data):
    try:
        enabled = client.getPipelineEnabled(repository)

        has_changed = False
        result = None

        if enabled is False:
            body = client.updatePipelineEnabled(repository, True)
            has_changed = True
            result = {
                'state': 'enabled',
                'body': body,
            }
        else:
            result = {
                'state': 'not changed',
            }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message}

    return False, has_changed, {'repository': repository, 'result': result}


def absent(data):
    try:
        enabled = client.getPipelineEnabled(repository)

        has_changed = False
        result = None

        if enabled is True:
            body = client.updatePipelineEnabled(repository, False)
            has_changed = True
            result = {
                'state': 'disabled',
                'body': body,
            }
        else:
            result = {
                'state': 'not changed',
            }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message}

    return False, has_changed, {'repository': repository, 'result': result}


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
