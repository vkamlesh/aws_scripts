#!/bin/bash

##This script will print List of ELB Name and attached instance's private IP in given region.

echo -e "PROFILE:"
read PROFILE
echo -e "REGION:"
read REGION

ELB_NAME=$(aws elb describe-load-balancers  --profile $PROFILE --region $REGION \
| jq '.LoadBalancerDescriptions[] | "\(.LoadBalancerName)"' | sed 's/"//g' | xargs)

for ELB in $ELB_NAME
do
  INSTANCE_ID=$(aws elb describe-instance-health --load-balancer-name $ELB --profile $PROFILE --region $REGION \
  | jq '.InstanceStates[] | "\(.InstanceId)"'| sed 's/"//g' | xargs)

  for INSTANCE in $INSTANCE_ID
  do
    aws ec2 describe-instances --instance-id $INSTANCE --query "Reservations[*].Instances[].[PrivateIpAddress,InstanceId,InstanceType,Tags[?Key == 'Name'].Value[]]" --profile $PROFILE --region $REGION --output text

  done

done
