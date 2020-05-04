#!/usr/bin/env python3

import boto3.session
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--profile', help='AWS CLI Profile', type=str, required=True)
parser.add_argument(
    '--account_id', help='The AWS account ID associated with the registry that contains the repositories to be described.', type=str, required=True)
parser.add_argument('--repo', nargs='+',
                    help='A list of repositories to describe. If this parameter is omitted, then all repositories in a registry are described.', type=str)

parser.add_argument('--exclude_repo', nargs='+', help='A list of exclude repositories.', type=str)

args = parser.parse_args()

session = boto3.session.Session(profile_name=args.profile)
client = session.client('ecr', region_name='ap-south-1')

if len(args.repo) > 0:
    print(f"this is value for {args.repo}")
    response = client.describe_repositories(registryId=args.account_id, repositoryNames=args.repo)
else:
    response = client.describe_repositories(registryId=args.account_id)

for i in response['repositories']:
    repo_name = i['repositoryName']
    ecr_latest = client.list_images(
        registryId=args.account_id, repositoryName=repo_name, maxResults=1, filter={'tagStatus': 'TAGGED'})
    if len(ecr_latest['imageIds']) != 0  repo_name not in args.exclude_repo:
        print(f"\nRepo name: {repo_name} \n\n First_Image: {ecr_latest}\n\n")
    # print(i['repositoryArn'], i['repositoryName'])

    # print(ecr_latest['imageIds'][0]['imageTag'])
