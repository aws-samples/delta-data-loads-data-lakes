# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import json
import boto3
import os
import traceback
from datetime import datetime


def createReplicationInstance(instanceIdentifier,instanceClass,subnetGroupIdentifier,engineVersion,sgId):
    time=datetime.now().strftime("%d%m%Y%H%M%S%f")
    instanceIdentifier=instanceIdentifier+'-'+time
    client=boto3.client('dms')
    response=client.create_replication_instance(
        ReplicationInstanceIdentifier=instanceIdentifier,
        AllocatedStorage=100,
        ReplicationInstanceClass=instanceClass,
        VpcSecurityGroupIds=[
            sgId,
        ],
        ReplicationSubnetGroupIdentifier=subnetGroupIdentifier,
        MultiAZ=False,
        EngineVersion=engineVersion,
        AutoMinorVersionUpgrade=True,
        PubliclyAccessible=False,

    )
    arn= str(response['ReplicationInstance']['ReplicationInstanceArn'])
    return arn

def checkInstanceStatus(replicationIntanceARN):
    client=boto3.client('dms')
    response = client.describe_replication_instances(
        Filters=[
            {
                'Name': 'replication-instance-arn',
                'Values': [
                    replicationIntanceARN,
                ]
            },
        ],
        MaxRecords=99,
        Marker='string'
    )
    status= str(response['ReplicationInstances'][0]['ReplicationInstanceStatus'])
    return status

def lambda_handler(event, context):
    # TODO implement
    createStatus=''
    replicationInstanceArn=''
    replicationInstanceIdentifier=os.environ['ReplicationInstanceIdentifier']
    replicationInstanceClass=event['ReplicationInstanceClass']
    replicationInstanceSubnetGroupIdentifier=os.environ['ReplicationSubnetGroupIdentifier']
    engineVersion=os.environ['EngineVersion']
    sgId=os.environ['VpcSecurityGroupIds']
    try:
        replicationInstanceArn=createReplicationInstance(replicationInstanceIdentifier,replicationInstanceClass,replicationInstanceSubnetGroupIdentifier,engineVersion,sgId)
        print('arn',replicationInstanceArn)
        status=checkInstanceStatus(replicationInstanceArn)
        while (status.lower() in ['deleted','deleting','failed', 'creating','modifying','upgrading','rebooting']):

            status=checkInstanceStatus(replicationInstanceArn)
            # print('Curretn Status:',status)
            if(status.lower() == 'available'):
                createStatus='SUCCESS'
                break

            if(status.lower() in ["deleted","deleting","failed"]):
                createStatus='FAILED'
                break;

        return {
            'createStatus': createStatus,
            'replicationInstanceArn':replicationInstanceArn,
            'TableNames': event['TableNames']
        }
    except:
        createStatus='FAILED'
        traceback.print_exc()
        return {
            'createStatus': createStatus,
            'replicationInstanceArn':replicationInstanceArn,
            'TableNames': event['TableNames']
        }

