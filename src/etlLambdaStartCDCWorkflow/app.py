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
import os
import botocore
import json

def start_cdc_execution(input_json,statemachinearn):
    client = boto3.client('stepfunctions')
    response = client.start_execution(
    stateMachineArn=statemachinearn,
    input=input_json
    )
    return response

def get_crawlers(dynamodbtablename):
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.scan(TableName=dynamodbtablename)
    items=response['Items']
    return items
def fingTableNames(tablename):
    response=get_crawlers(tablename)
    inputTableNames=[]
    for item in response:
        active_flag=item['activeflag']['S']
        if active_flag=='Y':
            targetTableName=item['targetTableName']['S']
            inputTableNames.append(targetTableName)
    return (inputTableNames)

def lambda_handler(event, context):
    try:
        tablename=os.getenv('DYNAMODBTABLE').strip()
        statemachinearn=os.getenv('STATEMACHINEARN').strip()
        ReplicationInstanceClass = os.getenv('ReplicationInstanceClass').strip()
        inputTableNames=fingTableNames(tablename)
        json_string={"ReplicationInstanceClass": ReplicationInstanceClass, "TableNames": inputTableNames}
        json_array=json.dumps(json_string)
        print("json_array:{}".format(json_array))
        response=start_cdc_execution(json_array,statemachinearn)
        return {"result":"SUCCEEDED"}
    
    except Exception as e:
        print("Exception thrown: %s" % str(e))
        return {"result":"FAILED"}

