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

import boto3
import botocore
import os
import time

def checkConnection(replicationInstanceArn,endpointArn):
    client=boto3.client('dms')
    response = client.test_connection(ReplicationInstanceArn=replicationInstanceArn,EndpointArn=endpointArn)
    return response

def describeconnection(replicationInstanceArn,EndpointArn):
    client=boto3.client('dms')
    response = client.describe_connections(Filters=[{'Name': 'replication-instance-arn','Values': [replicationInstanceArn]},{'Name': 'endpoint-arn','Values': [EndpointArn]}])
    return response


def lambda_handler(event, context):
    try:
        print(event)
        replicationInstanceArn=event['replicationInstanceArn']
        dbEndpointArn=os.environ['etlDatabaseEndpointArn']
        S3EndpointArn=os.environ['etlS3EndpointArn']
        time.sleep(30)
        print('Testing DB EndPoint')
        checkConnectionResponse=checkConnection(replicationInstanceArn,dbEndpointArn)
        print(checkConnectionResponse)
        status=checkConnectionResponse['Connection']['Status']
        while (status.lower() in ['testing','successful','failed', 'deleting']):
            time.sleep(20)
            connections=describeconnection(replicationInstanceArn,dbEndpointArn)['Connections'][0]
            status=connections['Status']
            if(status.lower() == 'successful'):
                createStatus='SUCCESS'
                break;
            if(status.lower() in ["failed","deleting"]):
                createStatus='FAILED'
                break;
        print('End Point Connection Status',createStatus)
        if(createStatus == 'FAILED'):
            return {"result":"FAILED"}

        print('Testing S3 EndPoint')
        checkConnectionResponse=checkConnection(replicationInstanceArn,S3EndpointArn)
        print(checkConnectionResponse)

        status=checkConnectionResponse['Connection']['Status']
        while (status.lower() in ['testing','successful','failed', 'deleting']):
            time.sleep(20)
            connections=describeconnection(replicationInstanceArn,S3EndpointArn)['Connections'][0]
            status=connections['Status']
            print(status)
            if(status.lower() == 'successful'):
                createStatus='SUCCESS'
                break;
            if(status.lower() in ["failed","deleting"]):
                createStatus='FAILED'
                break;
        print('End Point Connection Status',createStatus)
        if(createStatus == 'FAILED'):
            return {"result":"FAILED"}

        return {"result":"SUCCESS",'replicationInstanceArn':event['replicationInstanceArn'],'TableNames':event['TableNames']}
    except botocore.exceptions.ClientError as e:
        print("Could not start dms task: %s" % e)
        return {"result":"FAILED"}

