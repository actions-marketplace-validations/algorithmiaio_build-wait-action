#!/usr/bin/python
import Algorithmia
import os
import requests
import time


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Simple " + self.token
        return r


# TODO: Make sure this works even when a build id isn't visible just yet
def get_build_id(api_key, api_address, algo_name, hash, marker=None):
    if marker:
        url = "{}/v1/algorithms/{}/builds?limit={}&marker={}".format(api_address, algo_name, 10, marker)
    else:
        url = "{}/v1/algorithms/{}/builds?limit={}".format(api_address, algo_name, 10)
    result = get_api_request(url, api_key)
    if "error" in result:
        raise Exception(result['error']['message'])
    else:
        builds = result['results']
        for build in builds:
            if hash in build['commit_sha']:
                build_id = build['build_id']
                return build_id
        marker = result['marker']
        return get_build_id(api_key, api_address, algo_name, hash, marker)


def wait_for_result(api_key, api_address, algo_name, build_id):
    waiting = True
    url = "{}/v1/algorithms/{}/builds/{}".format(api_address, algo_name, build_id)
    url_logs = "{}/v1/algorithms/{}/builds/{}/logs".format(api_address, algo_name, build_id)
    while waiting:
        result = get_api_request(url, api_key)
        if "error" in result:
            raise Exception(result['error']['message'])
        else:
            if result['status'] != u'in-progress':
                if result['status'] == u'succeeded':
                    waiting = False
                else:
                    log_data = get_api_request(url_logs, api_key)
                    raise Exception("build failure:\n{}".format(log_data['logs']))
            else:
                time.sleep(5)


def get_api_request(url, api_key):
    response = requests.get(auth=BearerAuth(api_key), url=url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("request failed with status: {}".format(response.status_code))


if __name__ == "__main__":
    api_key = os.getenv("INPUT_MGMT_API_KEY")
    api_address = os.getenv("INPUT_API_ADDRESS")
    algo_name = os.getenv("INPUT_ALGORITHM_NAME")
    algo_hash = os.getenv("GITHUB_SHA")
    print("--- Finding build in progress ---")
    build_id = get_build_id(api_key, api_address, algo_name, algo_hash)
    print("--- Build ID found, waiting for result ---")
    wait_for_result(api_key, api_address, algo_name, build_id)
    print("--- Build successful ---")
