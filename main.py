from google.cloud import storage

storage_client = storage.Client()

def gcsFileInterface(bucketName, fileName):
    bucket = storage_client.get_bucket(bucketName)
    blob = bucket.blob(fileName)
    contents = blob.download_as_string()
    return contents

def hello_gcs(event, context):
    # print('Updated: {}'.format(event['updated']))   
    source = gcs_file_interface(event['bucket'], event['name'])
    print(len(contents))