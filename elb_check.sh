#!/bin/bash


check_health()
{
  aws elb describe-instance-health --load-balancer-name $ELB_NAME --instances $INSTANCE_ID --profile payu --region $REGION

}

deregister_instance()
{
  echo "Enter Instance ID\n"
  read INSTANCE_ID
  aws elb deregister-instances-from-load-balancer --load-balancer-name $ELB_NAME --instances $INSTANCE_ID --profile payu --region $REGION
  echo "Instance Deregister\n"
  check_health
}

register_instance()
{
  echo "Enter Instance ID\n"
  read INSTANCE_ID
  aws elb register-instances-with-load-balancer --load-balancer-name $ELB_NAME --instances $INSTANCE_ID --profile payu --region $REGION
  echo "Instance Register\n"
  check_health
}


ELB_NAME=$1
REGION=$2
LIST_INSTANCES=`aws elb describe-instance-health --load-balancer-name $ELB_NAME  --profile payu --region $REGION --output text | awk '{print $3}' | xargs`
echo "List of Instance for this ELB\n"
for i in $LIST_INSTANCES
do
   IP=$(aws ec2 describe-instances --instance-id $i --profile payu --region $REGION --output text | grep PRIVATEIPADDRESSES | awk '{print $4}')
   echo "Instance-ID: $i  IP-Address: $IP"
done

echo "Enter your Choice\n 1.Deregister\n 2.Register\n 3.Check Health\n"
read CHOICE
if [[ "$CHOICE" = "1" ]]
then
    deregister_instance
elif [[ "$CHOICE" = "2" ]]
then
    register_instance
elif [[ "$CHOICE" = "3" ]]
then
    echo "Enter Instance ID\n"
    read INSTANCE_ID
    check_health
else
     echo "Please enter correct choice\n"
fi
