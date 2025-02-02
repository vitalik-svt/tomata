from typing import List
import aioboto3
import logging
import base64
import mimetypes


from app.settings import settings


logger = logging.getLogger(__name__)


async def get_s3_client():
    session = aioboto3.Session()
    async with session.client(
            service_name='s3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key
    ) as client:
        return client


async def s3_client_dependency():
    """dependency just in case"""
    async def _get_s3_client():
        return await get_s3_client()
    return _get_s3_client


async def create_bucket(s3_client = None, bucket_name: str = settings.s3_images_bucket):

    if not s3_client:
        s3_client = await get_s3_client()

    response = await s3_client.list_buckets()
    bucket_names = [bucket['Name'] for bucket in response['Buckets']]

    if bucket_name not in bucket_names:
        try:
            await s3_client.create_bucket(Bucket=bucket_name)
        except Exception:
            raise Exception(f"Can't create bucket {bucket_name}")
        return logger.info(f"Bucket {bucket_name} created successfully.")
    else:
        return logger.info(f"Bucket {bucket_name} already exists.")


async def list_files(s3_client, bucket_name: str, prefix: str = '') -> List:

    response = await s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    if 'Contents' in response:
        return [obj['Key'] for obj in response['Contents']]
    else:
        return []


async def upload_to_bucket(s3_client, bucket_name: str, file_name: str, file_data: bytes, prefix: str = '') -> str:

    full_key = f"{prefix}/{file_name}" if prefix else file_name
    try:
        await s3_client.put_object(Bucket=bucket_name, Key=full_key, Body=file_data)
        return f"{bucket_name}/{full_key}"
    except Exception as e:
        raise Exception(f"Error uploading file: {e}")


async def download_from_bucket(s3_client, bucket_name: str, file_name: str, prefix: str = '') -> bytes:

    full_key = f"{prefix}/{file_name}" if prefix else file_name
    try:
        response = await s3_client.get_object(Bucket=bucket_name, Key=full_key)
        file_data = await response['Body'].read()
        return file_data
    except Exception as e:
        raise Exception(f"Error downloading file: {e}")


async def delete_file(s3_client, bucket_name: str, file_name: str, prefix: str = ''):

    full_key = f"{prefix}/{file_name}" if prefix else file_name
    try:
        await s3_client.delete_object(Bucket=bucket_name, Key=full_key)
    except Exception as e:
        raise Exception(f"Error deleting file: {e}")


async def delete_folder(s3_client, bucket_name: str, prefix: str) -> None:
    """Delete all files (objects) under a given prefix in the S3 bucket."""
    try:
        files = await list_files(s3_client, bucket_name, prefix)
        if files:
            for file_key in files:
                await s3_client.delete_object(Bucket=bucket_name, Key=file_key)
        else:
            logging.info(f"No files found under prefix '{prefix}' to delete.")

    except Exception as e:
        raise Exception(f"Error deleting folder with prefix {prefix}: {str(e)}")



async def base64_image_to_s3(base64_string: str, s3_client, bucket_name: str, file_name_wo_ext: str, prefix: str = '') -> str:
    """Upload a base64-encoded image to S3"""
    try:
        # Extract MIME type from base64 string
        header, base64_data = base64_string.split(",", 1)
        mime_type = header.split(";")[0].split(":")[1]

        valid_mime_types = {"image/png", "image/jpeg", "image/gif", "image/webp"}
        if mime_type not in valid_mime_types:
            raise ValueError(f"Unsupported MIME type: {mime_type}")

        ext = mimetypes.guess_extension(mime_type)
        if not ext:
            raise ValueError(f"Could not determine file extension for MIME type: {mime_type}")

        file_name_with_ext = f"{file_name_wo_ext}{ext}"

        image_data = base64.b64decode(base64_data)

        full_key = await upload_to_bucket(
            s3_client=s3_client, bucket_name=bucket_name, file_name=file_name_with_ext, file_data=image_data, prefix=prefix
        )

        logging.info(f"Image uploaded to S3 with key: {full_key}")
        return full_key

    except Exception as e:
        raise Exception(f"Error uploading image {bucket_name}/{prefix}/{file_name_wo_ext}.[ext]: {str(e)}")


async def s3_to_base64_image(s3_client, bucket_name: str, file_name_with_ext: str, prefix: str = '') -> str:
    """Download an image from S3 and convert it to a base64 string."""
    try:
        full_key = f"{prefix}/{file_name_with_ext}" if prefix else file_name_with_ext
        file_data = await download_from_bucket(s3_client=s3_client, bucket_name=bucket_name, file_name=full_key, prefix=prefix)
        base64_string = base64.b64encode(file_data).decode('utf-8')
        mime_type, _ = mimetypes.guess_type(file_name_with_ext)
        mime_type = "application/octet-stream" if not mime_type else mime_type
        data_url = f"data:{mime_type};base64,{base64_string}"
        return data_url

    except Exception as e:
        raise Exception(f"Error downloading image {bucket_name}/{prefix}/{file_name_with_ext}: {str(e)}")

