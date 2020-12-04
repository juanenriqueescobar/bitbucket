#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.juanenriqueescobar.bitbucket.plugins.module_utils.bitbucket_client import BitbucketClient, BitbucketClientException

from ansible.module_utils.basic import AnsibleModule

client = None
repository = None


def phase_3(name, repository_vars):
    # find especific var in list

    for item in repository_vars:
        if item['key'] == name:
            return item.get('uuid'), item.get('value'), item.get('secured')
    return '', '', False


def present(data):
    # crea o actualiza las variables del repository

    has_changed = False
    result = {}

    try:
        repository_vars = client.getRepositoryVars(repository)

        for var in data['vars']:

            uuid, value, secured = phase_3(var['name'], repository_vars)

            result[var['name']] = {
                'state': 'not changed',
            }

            # la var no existe, hay que crearla
            if len(uuid) == 0:
                d = {
                    'key': var['name'],
                    'value': var['value'],
                    'secured': var['secured'],
                }
                body = client.createRepositoryVar(
                    repository, d)
                has_changed = True
                result[var['name']] = {
                    'state': 'created',
                    'body': body,
                }

            # la var existe, pero es segura, no hacemos nada!!!
            elif secured:
                result[var['name']] = {
                    'state': 'hidden',
                    'body': {
                        'key': var['name'],
                        'secured': True,
                        'type': 'pipeline_variable',
                        'uuid': uuid,
                    },
                }

            # la var existe, hay que actualizarla
            elif value != var['value']:
                d = {
                    'key': var['name'],
                    'value': var['value'],
                    'secured': var['secured'],
                }
                body = client.updateRepositoryVar(
                    repository, uuid, d)
                has_changed = True
                result[var['name']] = {
                    'state': 'updated',
                    'body': body,
                }

    except BitbucketClientException as err:
        return True, False, {'err_code': err.code, 'err_message': err.message}

    return False, has_changed, {'repo': repository, 'result': result}


def absent(data=None):

    has_changed = False
    result = {}

    try:
        repository_vars = client.getRepositoryVars(repository)
    
        for var in data['vars']:

            uuid, value, secured = phase_3(var['name'], repository_vars)

            # la var existe!, hay q borrarla
            if len(uuid) != 0:
                client.removeRepositoryVar(
                    repository, uuid)
                has_changed = True
                result[var['name']] = {
                    'state': 'deleted',
                }
            else:
                result[var['name']] = {
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
        'vars': {
            'required': True,
            'type': 'list',
        }
    }

    choice_map = {
        'present': present,
        'absent':  absent,
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
