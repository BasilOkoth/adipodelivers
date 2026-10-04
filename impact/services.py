"""AWS media helpers.

These are deliberately credentials-free. boto3 uses the runtime IAM role or standard
AWS environment configuration. Call submit_mediaconvert_job after an original video
has been uploaded to S3 and original_s3_key is known.
"""
from pathlib import PurePosixPath
from django.conf import settings

def submit_mediaconvert_job(media):
    if not all([settings.AWS_STORAGE_BUCKET_NAME, settings.AWS_MEDIACONVERT_ROLE_ARN, media.original_s3_key]):
        return None
    import boto3
    bucket=settings.AWS_STORAGE_BUCKET_NAME
    stem=PurePosixPath(media.original_s3_key).stem
    out_prefix=f"processed/{media.project.record_id}/{media.pk}/{stem}"
    mc=boto3.client('mediaconvert', region_name=settings.AWS_S3_REGION_NAME)
    job={
      'Role': settings.AWS_MEDIACONVERT_ROLE_ARN,
      'Settings': {
        'Inputs':[{'FileInput':f's3://{bucket}/{media.original_s3_key}','AudioSelectors':{'Audio Selector 1':{'DefaultSelection':'DEFAULT'}},'VideoSelector':{}}],
        'OutputGroups':[
          {'Name':'HLS','OutputGroupSettings':{'Type':'HLS_GROUP_SETTINGS','HlsGroupSettings':{'Destination':f's3://{bucket}/{out_prefix}/hls/','SegmentLength':6}},'Outputs':[
            {'NameModifier':'_1080','ContainerSettings':{'Container':'M3U8','M3u8Settings':{}},'VideoDescription':{'Width':1920,'Height':1080,'CodecSettings':{'Codec':'H_264','H264Settings':{'RateControlMode':'QVBR','MaxBitrate':6000000,'QvbrSettings':{'QvbrQualityLevel':8}}}},'AudioDescriptions':[{'CodecSettings':{'Codec':'AAC','AacSettings':{'Bitrate':96000,'CodingMode':'CODING_MODE_2_0','SampleRate':48000}}}]},
            {'NameModifier':'_720','ContainerSettings':{'Container':'M3U8','M3u8Settings':{}},'VideoDescription':{'Width':1280,'Height':720,'CodecSettings':{'Codec':'H_264','H264Settings':{'RateControlMode':'QVBR','MaxBitrate':3500000,'QvbrSettings':{'QvbrQualityLevel':8}}}},'AudioDescriptions':[{'CodecSettings':{'Codec':'AAC','AacSettings':{'Bitrate':96000,'CodingMode':'CODING_MODE_2_0','SampleRate':48000}}}]},
            {'NameModifier':'_480','ContainerSettings':{'Container':'M3U8','M3u8Settings':{}},'VideoDescription':{'Width':854,'Height':480,'CodecSettings':{'Codec':'H_264','H264Settings':{'RateControlMode':'QVBR','MaxBitrate':1600000,'QvbrSettings':{'QvbrQualityLevel':7}}}},'AudioDescriptions':[{'CodecSettings':{'Codec':'AAC','AacSettings':{'Bitrate':64000,'CodingMode':'CODING_MODE_2_0','SampleRate':48000}}}]}
          ]},
          {'Name':'MP4 Fallback','OutputGroupSettings':{'Type':'FILE_GROUP_SETTINGS','FileGroupSettings':{'Destination':f's3://{bucket}/{out_prefix}/mp4/'}},'Outputs':[{'NameModifier':'_1080','ContainerSettings':{'Container':'MP4','Mp4Settings':{}},'VideoDescription':{'Width':1920,'Height':1080,'CodecSettings':{'Codec':'H_264','H264Settings':{'RateControlMode':'QVBR','MaxBitrate':6000000,'QvbrSettings':{'QvbrQualityLevel':8}}}},'AudioDescriptions':[{'CodecSettings':{'Codec':'AAC','AacSettings':{'Bitrate':96000,'CodingMode':'CODING_MODE_2_0','SampleRate':48000}}}]}]}
        ]
      },
      'UserMetadata':{'project_record_id':media.project.record_id,'media_id':str(media.pk)}
    }
    if settings.AWS_MEDIACONVERT_QUEUE_ARN: job['Queue']=settings.AWS_MEDIACONVERT_QUEUE_ARN
    return mc.create_job(**job)
