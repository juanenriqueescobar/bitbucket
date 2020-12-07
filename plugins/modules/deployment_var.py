#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.juanenriqueescobar.bitbucket.plugins.module_utils.bitbucket_client import BitbucketClient, BitbucketClientException

from ansible.module_utils.basic import AnsibleModule

client = None
repository = None
deployment = None


def phase_3(name, deployment_var):
    # find especific var in list

    for item in deployment_var:
        if item['key'] == name:
            return item.get('uuid'), item.get('value'), item.get('secured')
    return '', '', False


def present(data):
    try:
        deployment_uuid = client.getDeploymentUUID(
            repository, deployment)
        deployment_var = client.getDeploymentVars(
            repository, deployment, deployment_uuid)

        has_changed = False
        result = {}

        uuid, value, secured = phase_3(data['var_name'], deployment_var)

        # la var no existe, hay que crearla
        if len(uuid) == 0:
            d = {
                'key': data['var_name'],
                'value': data['var_value'],
                'secured': data['var_secured'],
            }
            body = client.createDeploymentVar(
                repository, deployment_uuid, d)
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
                    'environmentUuid': deployment_uuid,
                    'key': data['var_name'],
                    'secured': True,
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
            body = client.updateDeploymentVar(
                repository, deployment_uuid, uuid, d)
            body['environmentUuid'] = deployment_uuid
            has_changed = True
            result = {
                'state': 'updated',
                'body': body,
            }
        else:
            result = {
                'state': 'not changed',
                'body': {
                    'environmentUuid': deployment_uuid,
                    'key': data['var_name'],
                    'secured': False,
                    'uuid': uuid,
                    'value': data['var_value'],
                },
            }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message}

    return False, has_changed, {'repository': repository, 'deployment': deployment, 'result': result}


def absent(data=None):
   # borra las variables del deployment

    try:
        deployment_uuid = client.getDeploymentUUID(
            repository, deployment)
        deployment_var = client.getDeploymentVars(
            repository, deployment, deployment_uuid)

        has_changed = False
        result = {}

        uuid, value, secured = phase_3(data['var_name'], deployment_var)

        # la var existe!, hay q borrarla
        if len(uuid) != 0:
            client.removeDeploymentVar(
                repository, deployment_uuid, uuid)
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
