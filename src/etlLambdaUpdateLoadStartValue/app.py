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

from __future__ import print_function
import boto3
import os
import cx_Oracle
import base64
import json
import boto3

def update_attribute_value_dyndb(rowKeyFieldName,rowKey,attributeName,attributeValue,tableName):
    print('update dynamoDb Metadata : ',rowKeyFieldName,rowKey,attributeName,attributeValue,tableName)
    dynamodb = boto3.resource('dynamodb')
    dynamoTable = dynamodb.Table(tableName)
    response = dynamoTable.update_item(
        Key={rowKeyFieldName : rowKey},
        AttributeUpdates={
            attributeName: {
                'Value': attributeValue,
                'Action': 'PUT'
            }
        }
    )

def update_value_dyndb(rowKeyFieldName,rowKey,attributeName,attributeValue,tableName):
    dynamodb = boto3.client('dynamodb')
    statement="UPDATE "+tableName+" SET "+attributeName+ " = '"+attributeValue + "' WHERE "+rowKeyFieldName+" ='"+rowKey+"'"
    print(statement)
    response=dynamodb.execute_statement(Statement=statement)
    print(response)


def readTableMetaData(tablename,tablekey,keyvalue):
    # Get the service resource.
    print('readTableMetaData : ',tablename,tablekey,keyvalue)
    dynamodb = boto3.resource('dynamodb')
    dynamoTable = dynamodb.Table(tablename)
    response = dynamoTable.get_item(Key={tablekey: keyvalue})
    if 'Item' in response:
        item = response['Item']
        return item
    else:
        print('Metadata Not Found')

def OracleConnection(SrcDbName,Username,Password):
    connection = cx_Oracle.connect(Username, Password, SrcDbName)
    print("Database connected!")
    return connection

def executeQuery(connection,sql):
    return connection.cursor().execute(sql)

def get_secret(dbsecret):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager'
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=dbsecret
    )

    if 'SecretString' in get_secret_value_response:
        text_secret_data = get_secret_value_response['SecretString']
    else:
        text_secret_data = get_secret_value_response['SecretBinary']

    secret_json = json.loads(text_secret_data)
    return secret_json['password']

def lambda_handler(event, context):

    try:
        DynTable=os.getenv('DYNAMODBTABLE').strip()
        UserName=os.getenv('SrcDbUserName').strip()
        Password=get_secret(os.getenv('SrcDbSecret').strip())
        SrcDbName=os.getenv('SrcDbName').strip()
        SrcDbPortNumber=os.getenv('SrcDbPortNumber').strip()
        SrcServerName=os.getenv('SrcServerName').strip()
        DDKey=event['DYNAMODB_KEY']
        connectUrl=SrcServerName+':'+SrcDbPortNumber+'/'+SrcDbName
        connection=OracleConnection(connectUrl,UserName,Password)
        item=readTableMetaData(DynTable,'targetTableName',DDKey)
        print("DynamoDb Metadata Record Found!")
        query = "SELECT max("+item['filtercolumn']+") FROM "+ item['sourceSchema']+"."+item['sourceTable']
        print('Executing Query on database:',query)
        result=executeQuery(connection,query).fetchone()[0]
        endvalue=str(item['endvalue']).strip()
        filteroperator=str(item['endvalue']).strip()
        if filteroperator=='gte' or filteroperator=='lte' or filteroperator=='eq' or filteroperator=='noteq':
            print("Updating start value only")
            update_attribute_value_dyndb('targetTableName',DDKey,'startvalue',str(result).strip(),DynTable)
        elif filteroperator=='between' or filteroperator=='notbetween':
            print("Updating start and end value")
            startvalue = endvalue
            end_value=str(result).strip()
            update_attribute_value_dyndb('targetTableName',DDKey,'startvalue',startvalue,DynTable)
            update_attribute_value_dyndb('targetTableName',DDKey,'endvalue',end_value,DynTable)
        return {'result':'SUCCEEDED','DYNAMODB_KEY':DDKey,'replicationInstanceArn':event['replicationInstanceArn']}
    except Exception as e:
        print("Exception thrown: %s" % str(e))
        return {'result':'FAILED'}
