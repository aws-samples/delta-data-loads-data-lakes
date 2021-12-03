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
import json
import os
from datetime import datetime
import decimal
from boto3.dynamodb.conditions import Key, Attr
def read_table_configuration(tablename,key):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(tablename)
    response = table.query(KeyConditionExpression=Key('targetTableName').eq(key))
    return response
tablemapping='{"rules": [{"rule-type": "selection","rule-id": "1","rule-name": "1","object-locator": {"schema-name": "SchemaName","table-name": "TableName"},"rule-action": "include","filters": [{"filter-type": "source","column-name": "FilterColumnName","filter-conditions": [{"filter-operator": "FilterColumnOperator","value": "StartValue"}]}]}]}'
tablemappingbetween='{"rules": [{"rule-type": "selection","rule-id": "1","rule-name": "1","object-locator": {"schema-name": "SchemaName","table-name": "TableName"},"rule-action": "include","filters": [{"filter-type": "source","column-name": "FilterColumnName","filter-conditions": [{"filter-operator": "FilterColumnOperator","start-value": "StartValue","end-value": "EndValue"}]}]}]}'
tmsimple='{"rules": [{"rule-type": "selection","rule-id": "1","rule-name": "1","object-locator": {"schema-name": "SchemaName","table-name": "TableName"},"rule-action": "include"}]}'
def create_replication_task_for_table(tablename,DynamoDBKey,tablemapping,SourceEndpointArn,TargetEndpointArn,ReplicationInstanceArn,ReplicationTaskIdentifier):
    c=boto3.client('dms')
    replication_task_settings = '{"Logging": {"EnableLogging": true,"LogComponents": [{"Id": "SOURCE_UNLOAD","Severity": "LOGGER_SEVERITY_DEFAULT"},{"Id": "SOURCE_CAPTURE","Severity": "LOGGER_SEVERITY_DEFAULT"},{"Id": "TARGET_LOAD","Severity": "LOGGER_SEVERITY_DEFAULT"},{"Id": "TARGET_APPLY","Severity": "LOGGER_SEVERITY_INFO"},{"Id": "TASK_MANAGER","Severity": "LOGGER_SEVERITY_DEBUG"}]},}'
    response=c.create_replication_task(
    ReplicationTaskIdentifier=ReplicationTaskIdentifier,
    SourceEndpointArn=SourceEndpointArn,
    TargetEndpointArn=TargetEndpointArn,
    ReplicationInstanceArn=ReplicationInstanceArn,
    MigrationType='full-load',
    ReplicationTaskSettings=replication_task_settings,
    TableMappings=tablemapping,)
    return response
def lambda_handler(event, context):
    try:
        SArn=os.getenv('SOURCE_ENDPOINT_ARN')
        TArn=os.getenv('TARGET_ENDPOINT_ARN')
        InstanceArn=os.getenv('REPLICATION_INSTANCE_ARN')
        table=os.getenv('DYNAMODBTABLE').strip()
        DDKey=event['DYNAMODB_KEY']
        table_config=read_table_configuration(table,DDKey)
        startvalue=''
        filtercolumn=''
        filteroperator=''
        t=''
        for i in table_config['Items']:
            activeflag=i['activeflag']
            schemaname=i['sourceSchema']
            tablename=i['sourceTable']
            try:
                startvalue=i['startvalue']
                filtercolumn=i['filtercolumn']
                filteroperator=i['filteroperator']
            except Exception as e:
                print("assuming full load: %s" % str(e))
                startvalue=''
        TaskId=schemaname+"-"+tablename.replace('_','-')+"-TaskIdentifer"
        if activeflag=='Y':
            if filteroperator=='gte' or filteroperator=='lte' or filteroperator=='eq' :
                t=tablemapping
                t=t.replace('StartValue',startvalue).replace('FilterColumnName',filtercolumn).replace('FilterColumnOperator',filteroperator).replace('SchemaName',schemaname).replace('TableName',tablename)
            elif filteroperator=='between':
                t=tablemappingbetween
                sValue = startvalue.split(',')[0]
                eValue = startvalue.split(',')[1]
                t=t.replace('StartValue',sValue).replace('EndValue',eValue).replace('FilterColumnName',filtercolumn).replace('FilterColumnOperator',filteroperator).replace('SchemaName',schemaname).replace('TableName',tablename)
            else:
                t=tmsimple
                t=t.replace('SchemaName',schemaname).replace('TableName',tablename)
            print(t)
            response=create_replication_task_for_table(table,DDKey,t,SArn,TArn,InstanceArn,TaskId)
        return {'result':'SUCCEEDED','taskArn':response['ReplicationTask']['ReplicationTaskArn'],"DYNAMODB_KEY":DDKey}
    except Exception as e:
        print("Exception thrown: %s" % str(e))
        return {'result':'FAILED'}
