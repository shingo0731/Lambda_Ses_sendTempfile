import boto3
import base64
import email
import urllib.parse
import json
import os
from logging import getLogger, INFO

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = getLogger(__name__)
logger.setLevel(INFO)

s3 = boto3.resource('s3')

#メアド
SRC_MAIL = ""
DST_MAIL = ""
REGION = ""

#メール送信
def send_email(source, to, subject):
    client = boto3.client('ses', region_name=REGION)
    
    msg = MIMEMultipart()
    
    filepath="/tmp/test.csv"
    part = MIMEApplication(open(filepath, "rb").read())
    
    part.add_header("Content-Disposition", "attachment", filename="test.csv")
    msg.attach(part)
    
    part = MIMEText("添付ファイルやで～")
    msg.attach(part)

    response = client.send_raw_email(
        Source=source,
        Destinations=[
            to
        ],
        RawMessage={
            "Data": msg.as_string(),
        },
    )
    
    return response

def lambda_handler(event, context):
    print("--------- logger.info の出力 ---------")
    logger.info(json.dumps(event))
    
    # S3のデータ取得
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    messageid = key.split("/")[1]
    
    try:
        response = s3.meta.client.get_object(Bucket=bucket, Key=key)
        email_body = response['Body'].read().decode('utf-8')
        email_object = email.message_from_string(email_body)

        #メールから添付ファイルを抜き出す
        for part in email_object.walk():
            print("maintype : " + part.get_content_maintype())
            if part.get_content_maintype() == 'multipart':
                continue
            # ファイル名の取得
            attach_fname = part.get_filename()
            print(attach_fname)

            # ファイルの場合
            if attach_fname:
                # fileに添付ファイルを保存する
                attach_data = part.get_payload(decode=True)
                bucket_source = s3.Bucket(bucket)
                bucket_source.put_object(ACL='private', Body=attach_data,
                                         Key='file' + "/" + attach_fname, ContentType='text/plain')
                                         
                #tmp配下に保存
                with open("/tmp/test.csv", "a") as attach_data:
                    print("Write data to testFile", file=attach_data)
                
                                         
        #メール送信
        e = "ミスやで～"
        r = send_email(SRC_MAIL, DST_MAIL, e)

        return 'end'
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
