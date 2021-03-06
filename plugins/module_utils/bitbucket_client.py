from __future__ import (absolute_import, division, print_function)
import requests
import time

__metaclass__ = type


class BitbucketClientException(Exception):
    def __init__(self, code, message, func):
        self.code = code
        self.message = message
        self.func = func


class BitbucketClient():

    def __init__(self, username, password):
        self.url = 'https://api.bitbucket.org'
        self.client = requests.Session()
        self.client.auth = (username, password)
        self.client.headers.update({
            'Content-Type': 'application/json',
        })

    def simple_get_retry(self, url, expected):
        for i in range(0, 5):
            r = self.client.get(url)
            if r.status_code == expected:
                break
            time.sleep(i)

        return r

# deployments

    def getDeploymentUUID(self, repository, deployment):
        # obtenemos el uuid del deployment

        rd = self.getDeployments(repository)

        for item in rd['values']:
            if item['name'] == deployment:
                return item['uuid']

        data = {
            'error': 'deployment \'{0}\' not found'.format(deployment)
        }
        raise BitbucketClientException(404, data, 'getDeploymentUUID')

    def getDeployments(self, repository):
        # TODO pagination not used, maybe incomplete response

        url = '{0}/2.0/repositories/{1}/environments/'.format(
            self.url, repository)

        r = self.simple_get_retry(url, 200)
        if r.status_code == 200:
            return r.json()

        raise BitbucketClientException(
            r.status_code, r.json(), 'getDeployments')

    def createDeployment(self, repository, deployment, environment_type):
        url = '{0}/2.0/repositories/{1}/environments/'.format(
            self.url, repository)

        data = {
            'name': deployment,
            'environment_type': {
                'name': environment_type,
            },
        }

        r = self.client.post(url, json=data)
        if r.status_code == 201:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'createDeployment')

    def removeDeployment(self, repository, deployment_uuid):
        url = '{0}/2.0/repositories/{1}/environments/{2}'.format(
            self.url, repository, deployment_uuid)

        r = self.client.delete(url)

        if r.status_code != 204:
            raise BitbucketClientException(
                r.status_code, r.json(), url)

# deployment pattern

    def getDeploymentPatternUUID(self, repository, deployment_uuid, pattern):
        data = self.getDeploymentPatterns(repository, deployment_uuid)
        for item in data['values']:
            if item['pattern'] == pattern:
                return item['uuid']

        return ''

    def getDeploymentPatterns(self, repository, deployment_uuid):
        # TODO this is an internal api
        # return all pattern from one deployment
        url = '{0}/internal/repositories/{1}/environments/{2}/branch-restrictions/'.format(
            self.url, repository, deployment_uuid)

        r = self.client.get(url)
        if r.status_code == 200:
            return r.json()

        raise BitbucketClientException(
            r.status_code, r.json(), 'getDeploymentPatterns')

    def createDeploymentPattern(self, repository, deployment_uuid, pattern):
        # TODO is an internal api

        url = '{0}/internal/repositories/{1}/environments/{2}/branch-restrictions/'.format(
            self.url, repository, deployment_uuid)

        data = {
            'pattern': pattern,
            'type': 'branch_restriction_pattern',
        }

        r = self.client.post(url, json=data)
        if r.status_code == 201:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'createDeploymentPattern')

    def removeDeploymentPattern(self, repository, deployment_uuid, pattern_uuid):
        # TODO is an internal api

        url = '{0}/internal/repositories/{1}/environments/{2}/branch-restrictions/{3}'.format(
            self.url, repository, deployment_uuid, pattern_uuid)

        r = self.client.delete(url)
        if r.status_code != 204:
            raise BitbucketClientException(
                r.status_code, r.json(), url)

# deployment vars

    def getDeploymentVars(self, repository, deployment, deployment_uuid):
        # obtenemos todas las variables del deployment

        url = '{0}/2.0/repositories/{1}/deployments_config/environments/{2}/variables?pagelen=20'.format(
            self.url, repository, deployment_uuid)

        r = self.simple_get_retry(url, 200)
        if r.status_code == 200:
            return r.json()['values']

        raise BitbucketClientException(
            r.status_code, r.json(), 'getDeploymentVars')

    def createDeploymentVar(self, repository, deployment_uuid, data):
        url = '{0}/2.0/repositories/{1}/deployments_config/environments/{2}/variables'.format(
            self.url, repository, deployment_uuid)
        r = self.client.post(url, json=data)
        if r.status_code == 201:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'createDeploymentVar')

    def updateDeploymentVar(self, repository, deployment_uuid, var_uuid, data):
        url = '{0}/2.0/repositories/{1}/deployments_config/environments/{2}/variables/{3}'.format(
            self.url, repository, deployment_uuid, var_uuid)
        r = self.client.put(url, json=data)

        if r.status_code == 200:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'updateDeploymentVar')

    def removeDeploymentVar(self, repository, deployment_uuid, var_uuid):
        url = '{0}/2.0/repositories/{1}/deployments_config/environments/{2}/variables/{3}'.format(
            self.url, repository, deployment_uuid, var_uuid)
        r = self.client.delete(url)

        if r.status_code != 204:
            raise BitbucketClientException(
                r.status_code, r.json(), 'removeDeploymentVar')

# pipeline enabled

    def getPipelineEnabled(self, repository):
        url = '{0}/2.0/repositories/{1}/pipelines_config'.format(
            self.url, repository)
        r = self.client.get(url)
        if r.status_code == 200:
            return r.json()['enabled']
        raise BitbucketClientException(
            r.status_code, r.json(), 'getPipelineEnabled')

    def updatePipelineEnabled(self, repository, enabled):
        url = '{0}/2.0/repositories/{1}/pipelines_config'.format(
            self.url, repository)

        data = {
            "enabled": enabled
        }

        r = self.client.put(url, json=data)

        if r.status_code == 200:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'updatePipelineEnabled')

# repository vars

    def getRepositoryVars(self, repository):
        url = '{0}/2.0/repositories/{1}/pipelines_config/variables/'.format(
            self.url, repository)
        r = self.client.get(url)
        if r.status_code == 200:
            return r.json()['values']
        raise BitbucketClientException(
            r.status_code, r.json(), 'getRepositoryVars')

    def createRepositoryVar(self, repository, data):
        url = '{0}/2.0/repositories/{1}/pipelines_config/variables/'.format(
            self.url, repository)
        r = self.client.post(url, json=data)

        if r.status_code == 201:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'createRepositoryVar')

    def updateRepositoryVar(self, repository, var_uuid, data):
        url = '{0}/2.0/repositories/{1}/pipelines_config/variables/{2}'.format(
            self.url, repository, var_uuid)

        r = self.client.put(url, json=data)

        if r.status_code == 200:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'updateRepositoryVar')

    def removeRepositoryVar(self, repository, var_uuid):
        url = '{0}/2.0/repositories/{1}/pipelines_config/variables/{2}'.format(
            self.url, repository, var_uuid)
        r = self.client.delete(url)

        if r.status_code != 204:
            raise BitbucketClientException(
                r.status_code, r.json(), 'removeRepositoryVar')
