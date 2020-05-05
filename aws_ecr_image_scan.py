#!/usr/bin/env python3

import argparse
import boto3.session
import botocore.exceptions


parser = argparse.ArgumentParser()

parser.add_argument('--profile', help='AWS CLI Profile', type=str, required=True)
parser.add_argument(
    '--account_id', help='The AWS account ID associated with the registry that contains the repositories to be described.', type=str, required=True)
parser.add_argument('--repo', nargs='+',
                    help='A list of repositories to describe. If this parameter is omitted, then all repositories in a registry are described.', type=str)

parser.add_argument('--exclude_repo', nargs='+', help='A list of exclude repositories.', type=str)

parser.add_argument('--result', help='Send result to given Email id', type=str)

args = parser.parse_args()

session = boto3.session.Session(profile_name=args.profile)
client = session.client('ecr', region_name='ap-south-1')

repo_list = []
image_list = []

if args.repo is None:
    response = client.describe_repositories(registryId=args.account_id)
    exclude_repo = args.exclude_repo
else:
    response = client.describe_repositories(registryId=args.account_id, repositoryNames=args.repo)
    exclude_repo = []


for i in response['repositories']:
    repo_name = i['repositoryName']
    ecr_latest = client.list_images(
        registryId=args.account_id, repositoryName=repo_name, maxResults=1, filter={'tagStatus': 'TAGGED'})
    if len(ecr_latest['imageIds']) != 0 and (not exclude_repo or repo_name not in exclude_repo):
        image_list.append([repo_name, ecr_latest['imageIds'][0]['imageDigest'],
                           ecr_latest['imageIds'][0]['imageTag']])


def image_scan(*args):
    for repo_name, image_id, image_tag in args:
        try:
            response = client.start_image_scan(repositoryName=repo_name, imageId={
                                               'imageDigest': image_id, 'imageTag': image_tag})
        except botocore.exceptions.ClientError as error:
            print(
                f"An image scan can only be started once per day on an individual image.\nExcepation: {error}")
            exit()

    return response['imageScanStatus']


def scan_result(*args):
    wait_scan = []
    failed_scan = []
    for repo_name, image_id, image_tag in args:
        response = client.describe_image_scan_findings(repositoryName=repo_name, imageId={
                                                       'imageDigest': image_id, 'imageTag': image_tag})
        if response['imageScanStatus'] == 'COMPLETE':
            print(response['imageScanFindings']['imageScanCompletedAt'])
            print(response['imageScanFindings']['vulnerabilitySourceUpdatedAt'])
            print(response['imageScanFindings']['findings'])
        elif response['imageScanStatus'] == 'IN_PROGRESS':
            wait_scan.append([repo_name, image_id, image_tag])
        elif response['imageScanStatus'] == 'FAILED':
            failed_scan.append([repo_name, image_id, image_tag])


if args.result True:
    scan_result(image_list)
    print(wait_scan)
    print(failed_scan)
