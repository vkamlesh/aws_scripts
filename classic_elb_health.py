#!/usr/bin/env python3

import boto3.session
import sys


elb_name = sys.argv[1]
region = sys.argv[2]
profile = sys.argv[3]

session = boto3.session.Session(profile_name=profile)
elb_new = session.client('elb',region_name=region)

response = elb_new.describe_instance_health(
    LoadBalancerName=elb_name
    )

def health_check(response):
    InstanceStates = response.get('InstanceStates')
    for i in InstanceStates:
        if i.get('State') == 'OutOfService':
            instances = i.get('InstanceId')
            elb_new.deregister_instances_from_load_balancer(
                    LoadBalancerName=elb_name,
                    Instances=[
                         {'InstanceId' : instances},
                        ]
                     )
            print("Deregister Instance ID: {}".format(instances))







def main():
    health_check(response)




if __name__ == '__main__':
    main()
