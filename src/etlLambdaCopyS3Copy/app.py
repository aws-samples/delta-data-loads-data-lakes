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
import time
import os
from datetime import datetime

def addTimestamptoFileName(original_filename_without_path):
    file_time = datetime.now().strftime("%Y%m%d-%H%M%S%f")
    filenamewithoutext=os.path.splitext(original_filename_without_path)[0]
    filextension=os.path.splitext(original_filename_without_path)[1]
    newFileName = file_time + filextension
    return newFileName
def readTableMetaData(tablename,tablekey,keyvalue):
    dynamodb = boto3.resource('dynamodb')
    dynamoTable = dynamodb.Table(tablename)
    response = dynamoTable.get_item(Key={tablekey: keyvalue})
    if 'Item' in response:
        item = response['Item']
        return item
    else:
        print('Metadata Not Found')
def getInputOutoutPath(tablename,targetTableName):
    item=readTableMetaData(tablename,'targetTableName',targetTableName)
    sourceSchema=str(item['sourceSchema'])
    sourceTable=str(item['sourceTable'])
    ouputs3Prefix=str(item['ouputs3Prefix'])
    targetTableName=str(item['targetTableName'])
    sourcePath='etl/raw/' + sourceSchema+'/'+sourceTable
    targetPath=ouputs3Prefix+ '/' + sourceSchema+'/'+targetTableName
    return sourcePath,targetPath

def lambda_handler(event, context):
    try:
        client = boto3.client('s3')
        tablename=os.getenv('DYNAMODBTABLE').strip()
        new_bucket_name = os.getenv('S3_BUCKET').strip()
        DynamoDBKey=event['DYNAMODB_KEY']
        dmstaskarn=event['taskArn']

        bucket_to_copy = new_bucket_name
        targetTableName=DynamoDBKey
        sourcePath,targetPath=getInputOutoutPath(tablename,targetTableName)
        print('sourcePath:'+sourcePath)
        print('targetPath:'+targetPath)
        response=client.list_objects(Bucket=bucket_to_copy,Prefix=sourcePath)
    except Exception as e:
        print("Exception thrown while reading parameters: %s" % str(e))
        return {'result':'FAILED'}
    try:
        keys=response['Contents']
    except Exception as e:
        exceptionstring=str(e)
        print('exception when retrieving content'+ exceptionstring)
        exceptionstring=str(e)
        if exceptionstring =="\'Contents\'":
            print("Exception thrown: when retriving content. No files to copy%s" % str(e))
            return {'result':'SUCCEDED'}
        else:
            return {'result':'FAILED'}
    try:
        for key in keys:
            files = key['Key']
            print('original filename with path:'+files)
            original_filename_without_path=files.split('/')[-1:][0]
            print('original_filename_without_path:'+original_filename_without_path)

            newfilename=addTimestamptoFileName(original_filename_without_path)
            print('newfilename:'+newfilename)
            copy_source={'Bucket': bucket_to_copy, 'Key': files}
            targetKey=targetPath+'/'+newfilename
            print("targetKey:"+targetKey)
            client.copy(copy_source, new_bucket_name, targetKey)
            return_code=response['ResponseMetadata']['HTTPStatusCode']
            print(return_code)
            print(response)
            if return_code != '200':
                {'result':'FAILED'}

        return {"result":"SUCCESS","taskArn":dmstaskarn,"DYNAMODB_KEY":DynamoDBKey,'replicationInstanceArn':event['replicationInstanceArn']}
    except Exception as e:
            print("Exception thrown: %s" % str(e))
            return {'result':'FAILED'}


