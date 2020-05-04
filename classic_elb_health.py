#!/usr/bin/env python3

import boto3.session
import sys
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--elb_name', help='Classic ELB Name', type=str, required=True)
parser.add_argument('--profile', help='AWS CLI Profile', type=str, required=True)
parser.add_argument('--region', help='AWS Region Name', type=str, required=True)

args = parser.parse_args()

session = boto3.session.Session(profile_name=args.profile)
elb_new = session.client('elb',region_name=args.region)

response = elb_new.describe_instance_health(
    LoadBalancerName=args.elb_name
    )




def health_check(response):
    InstanceStates = response.get('InstanceStates')
    #print(InstanceStates)
    for i in len(InstanceStates):
        #print(i)
        if i.get('State') == 'OutOfService':
            instances = i.get('InstanceId')
            elb_new.deregister_instances_from_load_balancer(
                    LoadBalancerName=args.elb_name,
                    Instances=[
                         {'InstanceId' : instances},
                        ]
                     )
            print("Deregister Instance ID: {}".format(instances))
    else:
        sys.exit("all Instances looks healthy")



def main():
    health_check(response)


if __name__ == '__main__':
    main()
