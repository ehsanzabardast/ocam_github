# pylint: disable=locally-disabled, multiple-statements, line-too-long, missing-module-docstring, no-member,
# missing-class-docstring, missing-function-docstring

import argparse
from pathlib import Path

import orjson
from tqdm.auto import tqdm
import requests


class GitHubAPI:
    def __init__(self, api_token, api_url: str = 'https://api.github.com/', timeout: int = 2*60):
        self.headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {api_token}',
        }
        if api_url[-1] != '/':
            api_url += '/'
        self.api_url = api_url
        self.timeout = timeout

    def get(self, endpoint: str):
        resp = requests.get(self.api_url + endpoint, headers=self.headers, timeout=self.timeout)

        resp.raise_for_status()
        results = resp.json()
        while 'next' in resp.links:
            next_url = resp.links['next']['url']
            resp = requests.get(next_url, headers=self.headers, timeout=self.timeout)
            results += resp.json()
        return results


def store(data, file_path: Path):
    (file_path.parent).mkdir(parents=True, exist_ok=True)
    with open(file_path, 'wb') as json_file:
        json_file.write(orjson.dumps(data, option=orjson.OPT_NON_STR_KEYS))


endpoints = {
    # 'commits': 'commits',
    'pulls': 'pulls?state=all',
    'issues': 'issues?state=all',
    'commit_comments': 'comments',
    'issue_comments': 'issues/comments',
    'review_comments': 'pulls/comments'
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('api_token', type=str, help='API token')
    parser.add_argument('outdir', type=Path, help='The output directory for all data')
    parser.add_argument('--api_url', type=str, default='https://api.github.com',
                        help='Specify API URL for GitHub Enterprise')
    parser.add_argument('--org', type=str, help='Specify a single organization')
    parser.add_argument('--select', type=str, nargs='+', choices=set(endpoints),
                        help='Load a subset of the available endpoints',
                        default=set(endpoints) - {'commits'})

    args = parser.parse_args()

    gh = GitHubAPI(api_token=args.api_token, api_url=args.api_url)

    if not args.org:
        orgs = gh.get('organizations')
        store(orgs, args.outdir/'organizations.json')
    else:
        orgs = [{'login': args.org}]

    repos = []
    for org in tqdm([org['login'] for org in orgs], desc='Get repos'):
        org_repos = gh.get(f'orgs/{org}/repos?type=all')
        repos += org_repos
    store(repos, args.outdir/'repos.json')

    for full_name in tqdm([repo['full_name'] for repo in repos], desc='Get data', miniters=1):
        for endpoint in args.select:
            file_path = args.outdir/full_name/f'{endpoint}.json'
            if not file_path.exists():
                url_part = endpoints[endpoint]
                commits = gh.get(f'repos/{full_name}/{url_part}')
                store(commits, file_path)
