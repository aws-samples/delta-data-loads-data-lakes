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

def check_task_status(dmstaskarn):
      client = boto3.client('dms')
      print("****before calling api")
      response = client.describe_replication_tasks(
          Filters=[
              {
                  'Name': 'replication-task-arn',
                  'Values': [
                      dmstaskarn
                  ]
              }
          ], WithoutSettings=True

      )

      print("****after calling api")
      print(response)
      task=response['ReplicationTasks'][0]
      print(task)
      status = task['Status']
      print("*****status:"+status)
      stop_reason=''
      if status == 'starting' or status == 'modifying' or status =='creating' or status =='running' or status =='stopping' or status == 'deleting':
        result ='RUNNING'
      elif status == 'stopped':
          stop_reason = task['StopReason']
          if stop_reason == 'Stop Reason FULL_LOAD_ONLY_FINISHED':
            result ='SUCCEEDED'
          else:
            result = 'FAILED'
      else:
        result = 'FAILED'
      print("*****result:"+result)
      #Starting Modifying Creating Running Stopping Deleting

      #Stopped Deleting
      return result

def lambda_handler(event, context):
  try:

      dmstaskarn=event['taskArn']
      print('DMSTASKARN:'.format(dmstaskarn))
      status=check_task_status(dmstaskarn)
      print("Response from check_dms_status{}".format(status))
      DynamoDBKey=event["DYNAMODB_KEY"]
      return {"result":status,"taskArn":dmstaskarn,"DYNAMODB_KEY":DynamoDBKey,'replicationInstanceArn':event['replicationInstanceArn']}

  except botocore.exceptions.ClientError as e:
      print("Could not start dms task: %s" % e)
      return {"result":"FAILED"}
