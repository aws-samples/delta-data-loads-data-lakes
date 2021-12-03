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
import json
def delete_task(dmstaskarn):
  client = boto3.client('dms')
  try:

      response = client.delete_replication_task(ReplicationTaskArn=dmstaskarn)
      print(response)
      return "SUCCEDED"
  except Exception as e:
    print("Could not start dms task: %s" % e)
    return "FAILED"


def lambda_handler(event, context):
  try:
      print(event)
      dmstaskarn=event['taskArn']
      DynamoDBKey=event['DYNAMODB_KEY']

      delete_task_response=delete_task(dmstaskarn)
      print(delete_task_response)
      return {"result":delete_task_response,"taskArn":dmstaskarn,"DYNAMODB_KEY":DynamoDBKey}

  except botocore.exceptions.ClientError as e:
      print("Could not start dms task: %s" % e)
      return {"result":"FAILED"}

