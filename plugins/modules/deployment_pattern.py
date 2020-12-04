#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.juanenriqueescobar.bitbucket.plugins.module_utils.bitbucket_client import BitbucketClient, BitbucketClientException

from ansible.module_utils.basic import AnsibleModule

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
        'pattern': {
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
        module.fail_json(msg='Error', meta=result)
    else:
        module.exit_json(changed=has_changed, meta=result)


if __name__ == '__main__':
    main()
