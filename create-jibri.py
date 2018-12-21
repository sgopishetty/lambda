import boto3,socket,json
import time
import datetime

# Region to launch instance.
REGION = 'us-west-2'

EC2 = boto3.client('ec2', region_name=REGION)

# Assign tag values to EC2 instance
TAG_VALUES = {"Key": "Name", "Value": "jibri"}

def lambda_handler(event, context):
    
    init_script = """#!/bin/bash

# Update and install python-pip and awscli
apt-get update -y
apt-get install -y python-pip
apt-get install -y awscli

# Allows us to add, change or remove records form Route 53 through command line calls.
cd /usr/local/bin/
wget https://github.com/barnybug/cli53/releases/download/0.8.7/cli53-linux-amd64
mv cli53-linux-amd64 /usr/local/bin/cli53
chmod +x /usr/local/bin/cli53

#create the file that contains the script to update the AWS Route 53 records.
touch /usr/sbin/update-route53-dns
chmod +x /usr/sbin/update-route53-dns

echo '#!/bin/sh

# The TimeToLive in seconds we use for the DNS records
TTL="300"

# Hosted Zone ID on Route53
ZONE="Z2S8NDZVRP07VL"
# Export access key ID and secret for cli53 and aws cli

export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=""
export AWS_DEFAULT_REGION="us-west-2"
export AWS_DEFAULT_OUTPUT="text"


SUB_DOMAIN="""+event['sessionId']+"""
REC_DOMAIN="recorder_$SUB_DOMAIN"

grep -rl "jitsi34.edvie.com" /etc/ | xargs sed -i "s/jitsi34.edvie.com/$REC_DOMAIN.edvie.com/g"
sed -i /etc/hosts -e "s/^127.0.0.1 localhost ip-172-30-0-210$/127.0.0.1 localhost $(hostname)/"
sed -i "s/jitsi34.edvie.com/${SUB_DOMAIN}.edvie.com/g" /var/www/html/jibriRecordings/start_selenium_user.sh
sed -i "/xmpp_domain/c\ \\"xmpp_domain\\":\\"${SUB_DOMAIN}.edvie.com\\"," /home/jibri/config.json
sed -i "/servers/c\ \\"servers\\":\[\\"${SUB_DOMAIN}.edvie.com\\"]," /home/jibri/config.json

service jibri-xmpp restart 
service jibri-xorg restart
service jibri-icewm restart
service jibri restart

# Use command line scripts to get instance ID and public IP address
REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\\" "{print $4}")
INSTANCE_ID=$(ec2metadata | grep "instance-id:" | cut -d " " -f 2)
PUBLIC_IPV4=$(ec2metadata | grep "public-ipv4:" | cut -d " "  -f 2)

# Create a new or update the A-Records on Route53 with public IP address
cli53 rrcreate --replace "$ZONE" "$REC_DOMAIN $TTL A $PUBLIC_IPV4"' >> /usr/sbin/update-route53-dns

# Execute the script to create records on Route53
/usr/sbin/update-route53-dns

# Set to shutdown the instance in 1 minute.
#shutdown -h +1"""    
    
#    print 'Running script:'
#    print init_script
    
    instance = EC2.run_instances(
        ImageId='ami-074b86b9c91c222bf',
        SubnetId='subnet-0c6215dc722e45117',
        SecurityGroupIds=['sg-0181f76db45fd8312'],
        MaxCount=1,
        MinCount=1,
        KeyName='test-jitsi',
        InstanceType='t2.medium',
        BlockDeviceMappings=[
        {
        'DeviceName': '/dev/sda1',
        'Ebs': {
            'VolumeSize': 30,
            'VolumeType': 'gp2'
            }
        }    
        ],
#        InstanceInitiatedShutdownBehavior='terminate', # Make shutdown in script terminate ec2
        UserData=init_script, # File to run on instance init.
        TagSpecifications=[{'ResourceType': 'instance', 'Tags': [TAG_VALUES]}]
    )
    
    print "New recording session created."
    print "jibri event session id :",event['sessionId']
    
    instance_id = instance['Instances'][0]['InstanceId']
    print "jibri Instance Id:",instance_id
    
    sub_domain = "recorder_"+event['sessionId']+".edvie.com"
    print "jibri sub_domain :",sub_domain
    
    ins = instance['Instances'][0]
    print "jibri ins is:::::",ins
    
    
    response = {
        "jibriinstanceId":instance_id,
        "jibrisubDomain":sub_domain
    }
    return response
    
def myconverter(o):
    print "hi:::",o
    if isinstance(o, datetime.datetime):
        return o.__str__()
