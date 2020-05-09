#!/usr/bin/env python3

import argparse
import boto3.session
import botocore.exceptions
from prettytable import PrettyTable
import mysql.connector
from mysql.connector import Error, IntegrityError

parser = argparse.ArgumentParser()

parser.add_argument('--profile', help='AWS CLI Profile', type=str, required=True)
parser.add_argument(
    '--account_id', help='The AWS account ID associated with the registry that contains the repositories to be described.', type=str, required=True)
parser.add_argument('--repo', nargs='+',
                    help='A list of repositories to describe. If this parameter is omitted, then all repositories in a registry are described.', type=str)

parser.add_argument('--exclude_repo', nargs='+', help='A list of exclude repositories.', type=str)

parser.add_argument('--result', help='Send result to given Email id', action='store_true')

parser.add_argument('--email', help='RECIPIENT email id', type=str)

args = parser.parse_args()

session = boto3.session.Session(profile_name=args.profile)
client = session.client('ecr', region_name='ap-south-1')

repo_list = []
image_list = []

# Create response object depends on --exclude_repo value.
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
            response = client.start_image_scan(repositoryName=repo_name,
                                               imageId={
                                                   'imageDigest': image_id,
                                                   'imageTag': image_tag})
        except botocore.exceptions.ClientError as error:
            print(
                f"An image scan can only be started once per day on an \
                individual image.\nExcepation: {error}")
            exit()

    return response['imageScanStatus']


wait_scan = []
failed_scan = []
table = PrettyTable()
table.field_names = ["Repository", "Image Tag", "Scan Time", "Last Time report",
                     "Name", "Severity", "Package", "Version"]
table.align["Version"] = "l"


def scan_result(*args):
    for repo_name, image_id, image_tag in args:
        try:
            response = client.describe_image_scan_findings(repositoryName=repo_name,
                                                           imageId={
                                                               'imageDigest': image_id,
                                                               'imageTag': image_tag})
            connection = mysql.connector.connect(host='192.168.99.102',
                                                 database='ecr_scan',
                                                 user='app',
                                                 password='#Super@131',
                                                 port='3306')

            if response['imageScanStatus']['status'] == 'COMPLETE' and connection.is_connected():
                cursor = connection.cursor(prepared=True)
                #cursor.execute("SELECT id FROM scan_result ORDER BY id DESC LIMIT 1")
                #id = cursor.fetchall()
                #id = sum(id, 1)
                sql_insert_query = """INSERT INTO scan_result
                      (repo_name,image_id,image_tag,last_scanComplete,
                      last_vulnerabilityScan,name,severity,pkg_version,pkg_name)
                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                last_scanComplete = response['imageScanFindings']['imageScanCompletedAt']
                last_vulnerabilityScan = response['imageScanFindings']['vulnerabilitySourceUpdatedAt']
                vu_name = response['imageScanFindings']['findings'][0]['name']
                vu_severity = response['imageScanFindings']['findings'][0]['severity']
                pkg_version = response['imageScanFindings']['findings'][0]['attributes'][0]['value']
                pkg_name = response['imageScanFindings']['findings'][0]['attributes'][1]['value']

                insert_tuple = (repo_name, image_id, image_tag, last_scanComplete, last_vulnerabilityScan,
                                vu_name, vu_severity, pkg_version, pkg_name)
                cursor.execute(sql_insert_query, insert_tuple)
                connection.commit()
                # table.add_row([repo_name, image_tag, last_scanComplete, last_vulnerabilityScan,
                # vu_name, vu_severity, pkg_name, pkg_version])
                # print(f"{last_scanComplete}\n{last_vulnerabilityScan}\n{vulnerability_name}\n{vulnerability_URI}\n {vulnerability_severity}\n {package_version}\n{package_name}")
            elif response['imageScanStatus']['status'] == 'IN_PROGRESS':
                wait_scan.append([repo_name, image_id, image_tag])
            elif response['imageScanStatus']['status'] == 'FAILED':
                failed_scan.append([repo_name, image_id, image_tag])
        except botocore.exceptions.ClientError as error:
            print(f"Image is not part of scan {repo_name}:{image_id}\n")
        except mysql.connector.Error as error:
            print("Error reading data from MySQL table", error)
        except mysql.connector.IntegrityError as error:
            # https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-tag-mutability.html
            print(f"Same Image Tag already present in the system")
        finally:
            if (connection.is_connected()):
                cursor.close()
                connection.close()


"""
# Sending Email functionality is not working with current credentials and setup.
def send_email(table):
    sender = "sender@xyz.com"
    recipient = "recipient@xyz.com"
    aws_region = "us-east-1"
    subject = "AWS ECR SCAN Result for Account {args.account_id}"
    html = '''<html>
    <head>AWS Image Scan Result</head>
    <body>
    <p>Amazon ECR uses the severity for a CVE from the upstream distribution source and Common Vulnerability Scoring System (CVSS) score.</p>
    <tr>$tbl</tr>
    <a></a>
    </body
    </html>'''

    tb = Template(html).safe_substitute(tbl=table)
    print(tb)

    charset = "UTF-8"
    client = boto3.client('ses', region_name=aws_region)
    try:
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    recipient,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': charset,
                        'Data': tb,
                    }
                },
                'Subject': {
                    'Charset': charset,
                    'Data': subject,
                },
            },
            Source=sender,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
"""


def main():

    if args.result:
        for image in image_list:
            scan_result(image)
        # send_email(table)
    else:
        for image in image_list:
            image_scan(image)


if __name__ == '__main__':
    main()
