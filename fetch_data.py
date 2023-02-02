import argparse
import pathlib

import orjson
from tqdm.auto import tqdm
from agithub.GitHub import GitHub


class HTTPError(Exception):
    """An HTTP error occurred."""


def store(data, file_path):
    (file_path.parent).mkdir(parents=True, exist_ok=True)
    with open(file_path, 'wb') as json_file:
        json_file.write(orjson.dumps(data, option=orjson.OPT_NON_STR_KEYS))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='desc')
    parser.add_argument('org', type=str, help='Name of the organization')
    parser.add_argument('api_token', type=str, help='API token')
    parser.add_argument('outdir', type=pathlib.Path, help='The output directory for the JSON files')
    parser.add_argument('--api_url', type=str, default='api.github.com', help='Specify API-URL for GitHub Enterprise')

    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    client = GitHub(token=args.api_token, paginate=True, api_url=args.api_url)

    print(f'Get all repositories of {args.org}...')

    status, repositories = client.orgs[args.org].repos.get()
    if status != 200: raise HTTPError(f'HTTP error {status}')
    store(repositories, args.outdir / 'repositories.json')

    print(f'Found {len(repositories)} repositories of {args.org}')

    for repo in tqdm(repositories):
        owner, repository = repo['full_name'].split('/')

        status, pulls = client.repos[owner][repository].pulls.get()
        if status != 200: raise HTTPError(f'HTTP error {status}')
        store(repositories, args.outdir / owner / repository / 'pulls.json')

        status, issues = client.repos[owner][repository].issues.get()
        if status != 200: raise HTTPError(f'HTTP error {status}')
        store(repositories, args.outdir / owner / repository / 'issues.json')

        status, commit_comments = client.repos[owner][repository].comments.get()  # commit comments
        if status != 200: raise HTTPError(f'HTTP error {status}')
        store(repositories, args.outdir / owner / repository / 'comments.json')

        status, issue_comments = client.repos[owner][repository].issues.comments.get()  # issue comments
        if status != 200: raise HTTPError(f'HTTP error {status}')
        store(repositories, args.outdir / owner / repository / 'issue_comments.json')

        status, review_comments = client.repos[owner][repository].pulls.comments.get()  # pull request review comments
        if status != 200: raise HTTPError(f'HTTP error {status}')
        store(repositories, args.outdir / owner / repository / 'review_comments.json')

        status, commits = client.repos[owner][repository].commits.get()
        if status != 200: raise HTTPError(f'HTTP error {status}')
        store(repositories, args.outdir / owner / repository / 'commits.json')