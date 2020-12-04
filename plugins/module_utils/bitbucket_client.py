

import requests
import time


class BitbucketClientException(Exception):
    def __init__(self, code, message, func):
        self.code = code
        self.message = message
        self.func = func

# TODO raise custom Exceptions
# TODO raise exceptions if status code != 2XX


class BitbucketClient():

    def __init__(self, username, password):
        self.auth = (username, password)
        self.url = 'https://api.bitbucket.org'
        self.headers = {
            'Content-Type': 'application/json'
        }

    def simple_get_retry(self, url, expected):
        for i in range(0, 10):
            r = requests.get(url, auth=self.auth, headers=self.headers)
            if r.status_code == expected:
                break
            else:
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
            'error': 'deployment \'{}\' not found'.format(deployment)
        }
        raise BitbucketClientException(404, data, 'getDeploymentUUID')

    def getDeployments(self, repository):
        # TODO pagination not used, maybe incomplete response

        url = '{}/2.0/repositories/{}/environments/'.format(
            self.url, repository)

        r = self.simple_get_retry(url, 200)
        if r.status_code == 200:
            return r.json()

        raise BitbucketClientException(
            r.status_code, r.json(), 'getDeployments')

    def createDeployment(self, repository, deployment, environment_type):
        url = '{}/2.0/repositories/{}/environments/'.format(
            self.url, repository)

        data = {
            'name': deployment,
            'environment_type': {
                'name': environment_type,
            },
        }

        r = requests.post(url, auth=self.auth,
                          headers=self.headers, json=data)
        if r.status_code == 201:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'createDeployment')

    def removeDeployment(self, repository, deployment_uuid):
        url = '{}/2.0/repositories/{}/environments/{}'.format(
            self.url, repository, deployment_uuid)

        r = requests.delete(url, auth=self.auth,
                            headers=self.headers)

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
        url = '{}/internal/repositories/{}/environments/{}/branch-restrictions/'.format(
            self.url, repository, deployment_uuid)

        r = requests.get(url, auth=self.auth,
                         headers=self.headers)
        if r.status_code == 200:
            return r.json()

        raise BitbucketClientException(
            r.status_code, r.json(), 'getDeploymentPatterns')

    def createDeploymentPattern(self, repository, deployment_uuid, pattern):
        # TODO is an internal api

        url = '{}/internal/repositories/{}/environments/{}/branch-restrictions/'.format(
            self.url, repository, deployment_uuid)

        data = {
            'pattern': pattern,
            'type': 'branch_restriction_pattern',
        }

        r = requests.post(url, auth=self.auth,
                          headers=self.headers, json=data)
        if r.status_code == 201:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'createDeploymentPattern')

    def removeDeploymentPattern(self, repository, deployment_uuid, pattern_uuid):
        # TODO is an internal api

        url = '{}/internal/repositories/{}/environments/{}/branch-restrictions/{}'.format(
            self.url, repository, deployment_uuid, pattern_uuid)

        r = requests.delete(url, auth=self.auth,
                            headers=self.headers)
        if r.status_code != 204:
            raise BitbucketClientException(
                r.status_code, r.json(), url)

# deployment vars

    def getDeploymentVars(self, repository, deployment, deployment_uuid):
        # obtenemos todas las variables del deployment

        url = '{}/2.0/repositories/{}/deployments_config/environments/{}/variables?pagelen=20'.format(
            self.url, repository, deployment_uuid)

        r = self.simple_get_retry(url, 200)
        if r.status_code != 200:
            raise Exception('impossible to get the deployment vars \'{}\', code: {}'.format(
                deployment, r.status_code))

        return r.json()['values']

    def createDeploymentVar(self, repository, deployment_uuid, data):
        url = '{}/2.0/repositories/{}/deployments_config/environments/{}/variables'.format(
            self.url, repository, deployment_uuid)
        r = requests.post(url, auth=self.auth,
                          headers=self.headers, json=data)

        return r.status_code

    def updateDeploymentVar(self, repository, deployment_uuid, var_uuid, data):
        url = '{}/2.0/repositories/{}/deployments_config/environments/{}/variables/{}'.format(
            self.url, repository, deployment_uuid, var_uuid)
        r = requests.put(url, auth=self.auth,
                         headers=self.headers, json=data)

        return r.status_code

    def removeDeploymentVar(self, repository, deployment_uuid, var_uuid):
        url = '{}/2.0/repositories/{}/deployments_config/environments/{}/variables/{}'.format(
            self.url, repository, deployment_uuid, var_uuid)
        r = requests.delete(url, auth=self.auth,
                            headers=self.headers)

        return r.status_code

# repository

    def getRepositoryVars(self, repository):
        url = '{}/2.0/repositories/{}/pipelines_config/variables/'.format(
            self.url, repository)
        r = requests.get(url, auth=self.auth, headers=self.headers)
        if r.status_code == 200:
            return r.json()['values']
        raise BitbucketClientException(
            r.status_code, r.json(), 'getRepositoryVars')

    def createRepositoryVar(self, repository, data):
        url = '{}/2.0/repositories/{}/pipelines_config/variables/'.format(
            self.url, repository)
        r = requests.post(url, auth=self.auth,
                          headers=self.headers, json=data)

        if r.status_code == 201:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'createRepositoryVar')

    def updateRepositoryVar(self, repository, var_uuid, data):
        url = '{}/2.0/repositories/{}/pipelines_config/variables/{}'.format(
            self.url, repository, var_uuid)

        r = requests.put(url, auth=self.auth,
                         headers=self.headers, json=data)

        if r.status_code == 200:
            return r.json()
        raise BitbucketClientException(
            r.status_code, r.json(), 'updateRepositoryVar')

    def removeRepositoryVar(self, repository, var_uuid):
        url = '{}/2.0/repositories/{}/pipelines_config/variables/{}'.format(
            self.url, repository, var_uuid)
        r = requests.delete(url, auth=self.auth,
                            headers=self.headers)

        if r.status_code != 204:
            raise BitbucketClientException(
                r.status_code, r.json(), 'removeRepositoryVar')
