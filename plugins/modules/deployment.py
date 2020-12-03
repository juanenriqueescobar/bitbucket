#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.juanenriqueescobar.bitbucket.plugins.module_utils.bitbucket_client import BitbucketClient, BitbucketClientException

from ansible.module_utils.basic import AnsibleModule

client = None
repository = None
deployment = None


def present(data):

    has_changed = False
    result = None

    try:
        deployments = client.getDeployments(
            repository)

        deployment_uuid = ''
        for item in deployments['values']:
            if item['name'] == deployment:
                deployment_uuid = item['uuid']
                break

        if len(deployment_uuid) == 0:
            body = client.createDeployment(
                repository, deployment, data['type'])
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

    return False, has_changed, {'repository': repository, 'deployment': deployment, 'result': result}


def absent(data):

    has_changed = False
    result = None

    try:
        deployments = client.getDeployments(
            repository)

        deployment_uuid = ''
        for item in deployments['values']:
            if item['name'] == deployment:
                deployment_uuid = item['uuid']
                break

        if len(deployment_uuid) != 0:
            client.removeDeployment(repository, deployment_uuid)
            has_changed = True
            result = {
                'state': 'deleted',
            }
        else:
            result = {
                'state': 'not exists',
            }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message, 'err_func': err.func}

    return False, has_changed, {'repository': repository, 'deployment': deployment, 'result': result}


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
        'type': {
            'default': 'Test',
            'choices': ['Test', 'Staging', 'Production'],
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
        'absent':  absent,
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
        module.fail_json(msg='Error setting pipeline var', meta=result)
    else:
        module.exit_json(changed=has_changed, meta=result)


if __name__ == '__main__':
    main()
