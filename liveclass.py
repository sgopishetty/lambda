import boto3,socket,json
import time
import datetime
from botocore.vendored import requests


# Region to launch instance.
REGION = 'us-west-2'

EC2 = boto3.client('ec2', region_name=REGION)

# Assign tag values to EC2 instance
TAG_VALUES = {"Key": "Name", "Value": "jitsi-1"}

def lambda_to_ec2(event, context):
    ID = event['sessionId'] 
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

export AWS_ACCESS_KEY_ID="xxxxxxxxxxxxx"
export AWS_SECRET_ACCESS_KEY="xxxxxxxxxxxx"
export AWS_DEFAULT_REGION="us-west-2"
export AWS_DEFAULT_OUTPUT="text"

SUB_DOMAIN="""+event['sessionId']+"""

#"$(aws events list-targets-by-rule --rule  "test" | grep sessionId | awk '{print $4}' | jq -r ".sessionId")"

sed -i /etc/hosts -e "s/^127.0.0.1 localhost ip-172-30-0-114$/127.0.0.1 localhost $(hostname)/"
sed -i /etc/jitsi/jicofo/config -e "/JICOFO_AUTH_PASSWORD=/ s/=.*/=edvie123/" 

grep -rl "jitsi12.edvie.com" /etc/ |xargs sed -i "s/jitsi12.edvie.com/$SUB_DOMAIN.edvie.com/g"

mv /etc/prosody/conf.avail/jitsi12.edvie.com.cfg.lua "/etc/prosody/conf.avail/${SUB_DOMAIN}.edvie.com.cfg.lua"

ln -s /etc/prosody/conf.avail/${SUB_DOMAIN}.edvie.com.cfg.lua "/etc/prosody/conf.d/${SUB_DOMAIN}.edvie.com.cfg.lua"
unlink /etc/prosody/conf.d/jitsi12.edvie.com.cfg.lua

mv /etc/nginx/sites-available/jitsi12.edvie.com.conf "/etc/nginx/sites-available/${SUB_DOMAIN}.edvie.com.conf"

ln -s /etc/nginx/sites-available/${SUB_DOMAIN}.edvie.com.conf "/etc/nginx/sites-enabled/${SUB_DOMAIN}.edvie.com.conf"
unlink /etc/nginx/sites-enabled/jitsi12.edvie.com.conf

mv /etc/jitsi/meet/jitsi12.edvie.com-config.js "/etc/jitsi/meet/${SUB_DOMAIN}.edvie.com-config.js"

prosodyctl register edvie auth.${SUB_DOMAIN}.edvie.com edvie123
prosodyctl register focus auth.${SUB_DOMAIN}.edvie.com edvie123
prosodyctl register jibri auth.${SUB_DOMAIN}.edvie.com edvie123
prosodyctl register recorder recorder.${SUB_DOMAIN}.edvie.com edvie123



service prosody restart
service nginx restart
service jicofo restart
service jitsi-videobridge restart


# Use command line scripts to get instance ID and public IP address
REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\\" "{print $4}")
INSTANCE_ID=$(ec2metadata | grep "instance-id:" | cut -d " " -f 2)
PUBLIC_IPV4=$(ec2metadata | grep "public-ipv4:" | cut -d " "  -f 2)
PUBLICIP=$(echo ${PUBLIC_IPV4} | cut -d "b" -f1)
/bin/su - enlumelive sh -c "cd /home/enlumelive/WhiteBoard-1.0; forever start whiteboard.js"

# Create a new or update the A-Records on Route53 with public IP address
cli53 rrcreate --replace "$ZONE" "$SUB_DOMAIN $TTL A $PUBLIC_IPV4"' >> /usr/sbin/update-route53-dns


# Execute the script to create records on Route53
/usr/sbin/update-route53-dns

# Set to shutdown the instance in 1 minute.
#shutdown -h +1"""    
    
#    print 'Running script:'
#    print init_script


    instance = EC2.run_instances(
        ImageId='ami-07a02fdc0ac2de6f8',
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
    
    print "New liveclass session created."
    instance_id = instance['Instances'][0]['InstanceId']
    print "Instance Id:",instance_id
    
    #sub_domain = "https://"+event['sessionId']+".edvie.com"
    
    sub_domain = event['sessionId']+".edvie.com"
    print "sub_domain :",sub_domain
    
    ins = instance['Instances'][0]
    print "ins is:::::",ins
    
    print "Record Session:",event['recording']
    
    if event['schedule'] == 'true' :
        print "::::::it is a schedule event, need to call API to update instance:::::"
        url = "https://api.reinvent.edvie.com/liveClass/updateLiveClassScheduleByClassUrl"
        jsonEOS = {
                    'classUrl': event['sessionId'],
                    'jitsiUrl': sub_domain,
                    "instanceId":instance_id
                }
        headers = {"Content-Type": "application/json"}
        data = json.dumps(jsonEOS)
        eosresponse = requests.put(url, data, headers=headers)
        print "Data sent to Eos URL ::::::",data
        #print "response after save is:::::",eosresponse
    else :
         print "::::::NO API call needed:::::"
    
    if event['recording'] == 'true' :
        print "::::::Needs recorder, need to call JIBRI CURL API :::::"
        jibriurl = "https://t5ggs1ceha.execute-api.us-west-2.amazonaws.com/jibri-recording-api"
        print "event::::",event['sessionId']
        jsondata = {'sessionId': event['sessionId']}
        print "jsondata::::",jsondata
        headers1 = {"Content-Type": "application/json"}
        jibriresponse = requests.post(jibriurl, data=json.dumps(jsondata),headers=headers1)   
        #print "response after save is:::::",jibriresponse
        print "jibri istance:::",jibriresponse.json()
        dt = jibriresponse.json()
        print "jibri istance:::",dt
        print "jibri istance:::",dt['jibriinstanceId']
        print "jibri istance:::",dt['jibrisubDomain']
   
    else :
         print "::::::NO JIBRI CURL API call needed:::::"
    
    if event['recording'] == 'true' :
        response = {
            "instanceId":instance_id,
            "subDomain":sub_domain,
            "jibriInstanceId":dt['jibriinstanceId'],
            "jibriSubDomain":dt['jibrisubDomain']
        }
    else :
         response = {
            "instanceId":instance_id,
            "subDomain":sub_domain,
            "jibriInstanceId":'',
            "jibriSubDomain":''
        }
    return response
    
def myconverter(o):
    print "hi:::",o
    if isinstance(o, datetime.datetime):
        return o.__str__()
