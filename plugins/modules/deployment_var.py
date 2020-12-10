#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.juanenriqueescobar.bitbucket.plugins.module_utils.bitbucket_client import BitbucketClient, BitbucketClientException

from ansible.module_utils.basic import AnsibleModule

from hashlib import sha256
from base64 import b64encode

client = None
repository = None
deployment = None


def phase_3(name, deployment_vars):
    # find especific var in list

    for item in deployment_vars:
        if item['key'] == name:
            return item.get('uuid'), item.get('value'), item.get('secured')
    return '', '', False


def nh(name):
    return name+'__hash__'


def createVar(deployment_uuid, name, value, secured):
    d = {
        'key': name,
        'value': value,
        'secured': secured,
    }
    body = client.createDeploymentVar(
        repository, deployment_uuid, d)
    return True, {
        'state': 'created',
        'body': body,
    }


def updateVar(deployment_uuid, uuid, name, value, secured):
    d = {
        'key': name,
        'value': value,
        'secured': secured,
    }
    body = client.updateDeploymentVar(repository, deployment_uuid, uuid, d)
    body['environmentUuid'] = deployment_uuid
    return True, {
        'state': 'updated',
        'body': body,
    }


def deleteVar(deployment_uuid, uuid):
    client.removeDeploymentVar(
        repository, deployment_uuid, uuid)
    return True,  {
        'state': 'deleted',
    }


def present(data):

    has_changed = False
    result = {}

    try:
        deployment_uuid = client.getDeploymentUUID(
            repository, deployment)
        deployment_vars = client.getDeploymentVars(
            repository, deployment, deployment_uuid)

        var_name = data['var_name']
        var_value = data['var_value']
        var_secured = data['var_secured']

        hash_var_name = nh(var_name)
        hash_var_value = b64encode(
            sha256(var_value.encode('utf-8')).digest()).decode('utf-8')

        uuid, value, secured = phase_3(var_name, deployment_vars)

        # la var no existe, hay que crearla
        if len(uuid) == 0:
            has_changed, result = createVar(
                deployment_uuid, var_name, var_value, var_secured)
            if var_secured:
                createVar(deployment_uuid,
                          hash_var_name, hash_var_value, False)

        # la var existe pero es segura
        elif secured:
            huuid, hvalue, hsecured = phase_3(
                hash_var_name, deployment_vars)

            if len(huuid) == 0:
                has_changed, result = updateVar(
                    deployment_uuid, uuid, var_name, var_value, var_secured)
                createVar(deployment_uuid,
                          hash_var_name, hash_var_value, False)
            elif hvalue != hash_var_value:
                has_changed, result = updateVar(
                    deployment_uuid, uuid, var_name, var_value, var_secured)
                updateVar(
                    deployment_uuid, huuid, hash_var_name, hash_var_value, False)
            else:
                result = {
                    'state': 'not changed',
                    'body': {
                        'environmentUuid': deployment_uuid,
                        'key': var_name,
                        'secured': True,
                        'uuid': uuid,
                    },
                }

        # la var existe, hay que actualizarla
        elif value != var_value:
            has_changed, result = updateVar(
                deployment_uuid, uuid, var_name, var_value, var_secured)

        else:
            result = {
                'state': 'not changed',
                'body': {
                    'environmentUuid': deployment_uuid,
                    'key': var_name,
                    'secured': False,
                    'uuid': uuid,
                    'value': var_value,
                },
            }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message}

    return False, has_changed, {'repository': repository, 'deployment': deployment, 'result': result}


def absent(data=None):

    has_changed = False
    result = {}

    try:
        deployment_uuid = client.getDeploymentUUID(
            repository, deployment)
        deployment_vars = client.getDeploymentVars(
            repository, deployment, deployment_uuid)

        var_name = data['var_name']
        hash_var_name = nh(var_name)

        uuid, value, secured = phase_3(var_name, deployment_vars)

        # la var existe!, hay q borrarla
        if len(uuid) != 0:
            has_changed, result = deleteVar(deployment_uuid, uuid)
            if secured:
                huuid, hvalue, hsecured = phase_3(
                    hash_var_name, deployment_vars)
                deleteVar(deployment_uuid, huuid)
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
