import boto3
from botocore.exceptions import ClientError
import os
import time

ec2 = boto3.client('ec2', region_name='us-east-1')
ec2r = boto3.resource('ec2', region_name='us-east-1')
client = boto3.client('elbv2', region_name='us-east-1')
autoscale = boto3.client('autoscaling', region_name='us-east-1')

ec2_ohio = boto3.client('ec2', region_name='us-east-2')
ec2r_ohio = boto3.resource('ec2', region_name='us-east-2')

def deleteKeyPair(keyPairName):
    print("Deleting Key Pair:", keyPairName)
    try:
        ec2.delete_key_pair(KeyName = keyPairName)
        print("Key Pair deleted")
    except ClientError as e:
        print(e)

def deleteLoadBalancer(loadBalancerName):
    print("Deleting Load Balancer:", loadBalancerName)
    try:
        loadBalancerARN = client.describe_load_balancers(Names = [loadBalancerName])["LoadBalancers"][0]['LoadBalancerArn']
        waiterLoadBancer = client.get_waiter('load_balancers_deleted')
        client.delete_load_balancer(LoadBalancerArn = loadBalancerARN)	
        waiterLoadBancer.wait(LoadBalancerArns = [loadBalancerARN])
        time.sleep(30)
        print("Load Balancer deleted")

    except ClientError as e:
        print(e)

def deleteTargetGroup(targetGroupName):
    print("Deleting Target Group:", targetGroupName)
    try:
        tg = client.describe_target_groups(Names = [targetGroupName])
        targetGroupARN = tg["TargetGroups"][0]["TargetGroupArn"]
        client.delete_target_group(TargetGroupArn = targetGroupARN)
        print("Target Group deleted")
    except ClientError as e:
        print(e)

def deleteInstances(key, value):
    print("Deleting Instances")
    try:
        ec2r.instances.filter(Filters=[{
            'Name': 'tag:%s' % (key),
            'Values': [value]
        }]).terminate()
        waiter = ec2.get_waiter('instance_terminated')
        waiter.wait(
        Filters=[{
            'Name': 'tag:%s' % (key),
            'Values': [value]
        }])
        print("Instances deleted")
    except ClientError as e:
        print(e)

def deleteSecurityGroup(groupName):
    print("Deleting Security Group:", groupName)
    try:
        ec2.describe_security_groups(GroupNames = [groupName])
        ec2.delete_security_group(GroupName = groupName)
        print('Security Group deleted')
    except ClientError as e:
        print(e)

def deleteAutoScalingGroup(autoScalingName):
    print('Deleting Auto Scaling Group:', autoScalingName)
    try:
        autoscale.delete_auto_scaling_group(
            AutoScalingGroupName = autoScalingName,
            ForceDelete=True
        )

        while True:
            res = autoscale.describe_auto_scaling_groups(
                AutoScalingGroupNames = [autoScalingName]
            )
            if len(res['AutoScalingGroups']) == 0:
                break

            print('waiting')
            time.sleep(10)
        print('Auto Scaling Group deleted')
    except:
        print("Auto Scaling Group not found")

def deleteLaunchConfig(launchName):
    print("Deleting Launch Configuration:", launchName)
    try:
        autoscale.delete_launch_configuration(
            LaunchConfigurationName = launchName,
        )
        print("Launch Configuration deleted")
    except ClientError as e:
        print(e)

def createLoadBalancer(LoadBalancerName, securityGroupID):
    print('Creating Load Balancer:', LoadBalancerName)
    client.create_load_balancer(
        Name = LoadBalancerName,
        Subnets = ['subnet-13fa4b4f',
        'subnet-4d2f5a42',
        'subnet-51976d6f',
        'subnet-54296d1e',
        'subnet-7ebe0d50',
        'subnet-e0f44387'
        ],
        SecurityGroups = [
            securityGroupID,
        ],
        Scheme = 'internet-facing',
        Tags = [
            {
                'Key': 'Owner',
                'Value': 'gui'
            },
        ],
        Type = 'application',
        IpAddressType = 'ipv4'
    )
    print('Load Balancer created')

def createTargetGroup(targetGroupName, port):
    print('Creating Target Group:', targetGroupName)
    response = ec2.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    client.create_target_group(
        Name = targetGroupName,
        Protocol = 'HTTP',
        Port = port,
        VpcId = vpc_id,
        HealthCheckProtocol = 'HTTP',
        HealthCheckPath = '/',
        TargetType = 'instance'
    )
    tg = client.describe_target_groups(
        Names = [
            targetGroupName,
        ]
    )
    targetGroupARN = tg["TargetGroups"][0]["TargetGroupArn"]
    print('Target Group created')
    return targetGroupARN

def createListener(targetGroupARN, loadBalancerName):
    print('Creating Listener:', loadBalancerName)
    loadBalancerARN = client.describe_load_balancers(Names = [loadBalancerName])["LoadBalancers"][0]['LoadBalancerArn']
    client.create_listener(
        DefaultActions = [
            {
                'TargetGroupArn': targetGroupARN,
                'Type': 'forward'
            }],
        LoadBalancerArn = loadBalancerARN,
        Port = 80,
        Protocol = 'HTTP'
    )
    print('Listener created')

def createLaunchConfiguration(launchConfigurationName, keyName, securityGroupID, ip):
    print('Creating Launch Configuration:', launchConfigurationName)
    autoscale.create_launch_configuration(
        LaunchConfigurationName = launchConfigurationName,
        ImageId = 'ami-04b9e92b5572fa0d1',
        KeyName = keyName,
        SecurityGroups = [
            securityGroupID,
        ],
        InstanceType = 't2.micro',
        InstanceMonitoring = {
            'Enabled': True
        },
        UserData = '''#! /bin/bash
                    sudo apt-get update
                    sudo apt-get -y install python3-pip
                    pip3 install fastapi
                    pip3 install uvicorn
                    pip3 install pydantic
                    cd home/ubuntu
                    git clone https://github.com/guigs10mil/Projeto-Cloud.git
                    cd Projeto-Cloud
                    export toOhioWebserverIp=%s
                    uvicorn webserver:app --host "0.0.0.0"
                            ''' % (ip)
    )
    print('Launch Configuration created')

def createAutoScalingGroup(autoScalingName, launchName, targetGroupARN):
    print('Creating Auto Scaling Group:', autoScalingName)
    autoscale.create_auto_scaling_group(
        AutoScalingGroupName = autoScalingName,
        LaunchConfigurationName = launchName,
        MinSize = 1,
        MaxSize = 3,
        DesiredCapacity = 1,
        DefaultCooldown = 100,

        TargetGroupARNs = [
            targetGroupARN,
        ],
        AvailabilityZones = ["us-east-1a"],
        HealthCheckGracePeriod = 60
    )
    print('Auto Scaling Group created')

def createSecurityGroup(groupName, ports): 
    print('Create Security Group:', groupName)
    response = ec2.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    try:
        response = ec2.create_security_group(GroupName = groupName, Description = 'Security Group', VpcId = vpc_id)
        security_group_id = response['GroupId']
        ipPermissions = []
        for port in ports:
            ipPermissions.append({'IpProtocol': 'tcp', 'FromPort': port, 'ToPort': port, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]})
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=ipPermissions
        )
        print('Security Group created')
        return security_group_id
        
    except ClientError as e:
        response = ec2.describe_security_groups(
            Filters=[{'Name': 'group-name', 'Values': [groupName]}]
        )
        print(e)

    id = response['SecurityGroups'][0]['GroupId']
    return id

def createInstance(instanceName, groupName, keyName, publicip):
    print('Creating Instance:', instanceName)
    keyresponse = ec2.describe_key_pairs(KeyNames = [keyName])
    key = keyresponse["KeyPairs"][0]["KeyName"]
    GroupResponce = ec2.describe_security_groups(GroupNames = [groupName])
    Groupid = GroupResponce["SecurityGroups"][0]['GroupId']
    instance = ec2r.create_instances(DryRun = False,
        ImageId = 'ami-04b9e92b5572fa0d1',
        MinCount = 1,
        MaxCount = 1,
        KeyName = key,
        Placement = {'AvailabilityZone': 'us-east-1a'},
        SecurityGroupIds = [Groupid],
        InstanceType = 't2.micro',
        TagSpecifications = [{
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Owner',
                    'Value': 'gui'
                },
                {
                    'Key': 'Name',
                    'Value': instanceName
                }
            ]
        }],
        UserData='''#! /bin/bash
                    sudo apt-get update
                    sudo apt-get -y install python3-pip
                    pip3 install fastapi
                    pip3 install uvicorn
                    pip3 install pydantic
                    cd home/ubuntu
                    git clone https://github.com/guigs10mil/Projeto-Cloud.git
                    cd Projeto-Cloud
                    export mongodbWebserverIp=%s
                    uvicorn webserver-redirect-to-ohio:app --host "0.0.0.0"
                            ''' % (publicip)
    )
    waiter = ec2.get_waiter('instance_status_ok')
    waiter.wait(InstanceIds = [instance[0].id])
    print("Instance created")
    return instance

def createKeyPair(keyPairName):
    print('Creating Key Pair:', keyPairName)
    response = ec2.create_key_pair(KeyName = keyPairName)
    keyName = "%s.pem" % keyPairName
    try:
        os.chmod(keyName, 0o777)
    except:
        pass
    with open(keyName, "w") as text_file:
        text_file.write(response['KeyMaterial'])
    os.chmod(keyName, 0o400)
    print('Key Pair created')


def deleteKeyPairOhio(keyPairName):
    print("Deleting Key Pair:", keyPairName)
    try:
        ec2_ohio.delete_key_pair(KeyName = keyPairName)
        print("Key Pair deleted")
    except ClientError as e:
        print(e)

def deleteInstancesOhio(key, value):
    print('Deleting Instances')
    # response = ec2_ohio.describe_instances(
    # Filters=[
    #     {
    #         'Name': 'tag:%s' % (key),
    #         'Values': [value]
    #     },
    # ],
    # DryRun = False,
    # MaxResults = 5)
    # ifnull = response["Reservations"]
    # if ifnull != []:
    try:
        ec2r_ohio.instances.filter(Filters=[{
            'Name': 'tag:%s' % (key),
            'Values': [value]
        }]).terminate()
        waiter = ec2_ohio.get_waiter('instance_terminated')
        waiter.wait(
        Filters=[{
            'Name': 'tag:%s' % (key),
            'Values': [value]
        }])
        print("Instances deleted")
    except ClientError as e:
        print(e)

def deleteSecurityGroupOhio(groupName):
    print("Deleting Security Group:", groupName)
    try:
        ec2_ohio.delete_security_group(GroupName = groupName)
        print('Security Group deleted')
    except ClientError as e:
        print(e)

def createInstanceMongo(instanceName, groupName, keyName):
    print('Create Instance:', instanceName)
    keyresponse = ec2_ohio.describe_key_pairs(KeyNames = [keyName])
    key = keyresponse["KeyPairs"][0]["KeyName"]
    GroupResponce = ec2_ohio.describe_security_groups(GroupNames = [groupName])
    Groupid = GroupResponce["SecurityGroups"][0]['GroupId']
    instance = ec2r_ohio.create_instances(DryRun = False,
    ImageId = 'ami-0d5d9d301c853a04a',
    MinCount = 1,
    MaxCount = 1,
    KeyName = key,
    SecurityGroupIds = [Groupid],
    InstanceType = 't2.micro',
    TagSpecifications = [{
        'ResourceType':'instance',
        'Tags': [
            {
                'Key': 'Owner',
                'Value': 'gui'
            },
            {
                'Key': 'Name',
                'Value': instanceName
            }
        ]
    }],
    UserData = '''#! /bin/bash
                sudo apt update -y
                sudo apt-get install gnupg
                wget -qO - https://www.mongodb.org/static/pgp/server-4.2.asc | sudo apt-key add -
                echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/4.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.2.list
                sudo apt-get update -y
                sudo apt-get install -y mongodb-org
                echo "mongodb-org hold" | sudo dpkg --set-selections
                echo "mongodb-org-server hold" | sudo dpkg --set-selections
                echo "mongodb-org-shell hold" | sudo dpkg --set-selections
                echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
                echo "mongodb-org-tools hold" | sudo dpkg --set-selections
                sudo service mongod start,
                sudo sed -i "s/127.0.0.1/0.0.0.0/g" /etc/mongod.conf
                sudo service mongod restart
                        '''
    )
    waiter = ec2_ohio.get_waiter('instance_status_ok')
    waiter.wait(InstanceIds = [instance[0].id])
    print("Instance created")
    return instance

def createInstanceOhio(instanceName, groupName, keyName, privateip):
    print('Create Instance:', instanceName)
    keyresponse = ec2_ohio.describe_key_pairs(KeyNames = [keyName])
    key = keyresponse["KeyPairs"][0]["KeyName"]
    GroupResponce = ec2_ohio.describe_security_groups(GroupNames = [groupName])
    Groupid = GroupResponce["SecurityGroups"][0]['GroupId']
    instance = ec2r_ohio.create_instances(DryRun = False,
    ImageId = 'ami-0d5d9d301c853a04a',
    MinCount = 1,
    MaxCount = 1,
    KeyName = key,
    SecurityGroupIds = [Groupid],
    InstanceType = 't2.micro',
    TagSpecifications = [{
        'ResourceType':'instance',
        'Tags': [
            {
                'Key': 'Owner',
                'Value': 'gui'
            },
            {
                'Key': 'Name',
                'Value': instanceName
            }
        ]
    }],
    UserData='''#! /bin/bash
                git clone https://github.com/guigs10mil/Projeto-Cloud.git
                cd /Projeto-Cloud/db
                sudo apt-get update
                sudo apt-get install npm -y
                sudo npm install -g typescript ts-node -y
                sudo npm install
                sudo npm install --save @types/express express body-parser mongoose nodemon
                export dbIp=%s
                ts-node ./lib/server.ts
                        ''' % (privateip)
    )
    waiter = ec2_ohio.get_waiter('instance_status_ok')
    waiter.wait(InstanceIds = [instance[0].id])
    print("Instance created")
    return instance

def createKeyPairOhio(keyPairName):
    print('Creating Key Pair:', keyPairName)
    response = ec2_ohio.create_key_pair(KeyName = keyPairName)
    keyName = "%s.pem" % keyPairName
    try:
        os.chmod(keyName, 0o777)
    except:
        pass
    with open(keyName, "w") as text_file:
        text_file.write(response['KeyMaterial'])
    os.chmod(keyName, 0o400)
    print('Key Pair created')

def createSecurityGroupOhio(groupName, ports): 
    print('Creating Security Group:', groupName)
    response = ec2_ohio.describe_vpcs()
    vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
    try:
        response = ec2_ohio.create_security_group(GroupName = groupName, Description = 'Security Group', VpcId = vpc_id)
        security_group_id = response['GroupId']
        ipPermissions = []
        for port in ports:
            ipPermissions.append({'IpProtocol': 'tcp', 'FromPort': port, 'ToPort': port, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]})

        ec2_ohio.authorize_security_group_ingress(
            GroupId = security_group_id,
            IpPermissions = ipPermissions
        )
        print('Security Group created')
        return security_group_id
        
    except ClientError as e:
        response = ec2_ohio.describe_security_groups(
            Filters=[{'Name': 'group-name', 'Values': [groupName]}]
        )
        print(e)

    id = response['SecurityGroups'][0]['GroupId']
    return id




# -- OHIO -- #
print()
print('# -- OHIO -- #')
print()

keypair_name_ohio = 'key-guigui-ohio'
sec_group_name_mongo = 'secgroup-guigui-mongo'
sec_group_name_ohio = 'secgroup-guigui-ohio'

deleteKeyPairOhio(keypair_name_ohio)
deleteInstancesOhio("Owner", 'gui')
deleteSecurityGroupOhio(sec_group_name_mongo)
deleteSecurityGroupOhio(sec_group_name_ohio)

createKeyPairOhio(keypair_name_ohio)
createSecurityGroupOhio(sec_group_name_mongo, [22, 27017])
mongoInstance = createInstanceMongo('mongodb-gui-ohio', sec_group_name_mongo, keypair_name_ohio)
r = ec2_ohio.describe_instances()
ip = 0
for i in r['Reservations']:
    for j in i['Instances']:
        for k in j['SecurityGroups']:
            if k['GroupName'] == sec_group_name_mongo:
                ip = j['PrivateIpAddress']
print('Mongodb Instance Private IP = ', ip)
createSecurityGroupOhio(sec_group_name_ohio, [22, 27017, 3000])
createInstanceOhio('webserver-gui-ohio', sec_group_name_ohio, keypair_name_ohio, ip)



# -- DELETE N. VIRGINIA -- #
print()
print('# -- DELETE N. VIRGINIA -- #')
print()

keypair_name = 'key-guigui'
sec_group_name = 'secgroup-guigui'
sec_group_to_ohio_name = 'secgroup-to-ohio-guigui'
lb_sec_group_name = 'lb-secgroup-guigui'
lb_name = 'lb-guigui'
tg_name = 'tg-guigui'
launch_name = 'launchConfig-guigui'
autoscaling_name = 'autoscaling-guigui'

deleteInstances("Owner", 'gui')
deleteAutoScalingGroup(autoscaling_name)
deleteLaunchConfig(launch_name)
deleteLoadBalancer(lb_name)
deleteTargetGroup(tg_name)
deleteKeyPair(keypair_name)
deleteSecurityGroup(sec_group_name)
deleteSecurityGroup(lb_sec_group_name)
deleteSecurityGroup(sec_group_to_ohio_name)



# -- REDIRECT TO OHIO -- #
print()
print('# -- REDIRECT TO OHIO -- #')
print()


createKeyPair(keypair_name)
createSecurityGroup(sec_group_to_ohio_name, [22, 8000, 3000])
r = ec2_ohio.describe_instances()
for i in r['Reservations']:
    for j in i['Instances']:
        for k in j['SecurityGroups']:
            if k['GroupName'] == sec_group_name_ohio:
                ip = j['PublicIpAddress']
print('Ohio Webserver Instance Public IP = ', ip)
createInstance('webserver-to-ohio-gui', sec_group_to_ohio_name, keypair_name, ip)



# -- AUTO SCALING -- #
print()
print('# -- AUTO SCALING -- #')
print()

r = ec2.describe_instances()
for i in r['Reservations']:
    for j in i['Instances']:
        for k in j['SecurityGroups']:
            if k['GroupName'] == sec_group_to_ohio_name:
                ip = j['PrivateIpAddress']
print('To Ohio Webserver Instance Private IP = ', ip)

securityGroupID = createSecurityGroup(sec_group_name, [22, 8000])
LBsecurityGroupID = createSecurityGroup(lb_sec_group_name, [80])
createLoadBalancer(lb_name, LBsecurityGroupID)
tg_arn = createTargetGroup(tg_name, 8000)
createListener(tg_arn, lb_name)
createLaunchConfiguration(launch_name, keypair_name, securityGroupID, ip)
createAutoScalingGroup(autoscaling_name, launch_name, tg_arn)