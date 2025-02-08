from typing import List
from urllib.parse import urlparse
from contextlib import asynccontextmanager
import aioboto3
import logging
import base64
import mimetypes


from app.settings import settings


logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_s3_client():
    session = aioboto3.Session()
    async with session.client(
            service_name='s3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key
    ) as client:
        yield client


async def s3_client_dependency():
    """dependency just in case"""
    async def _get_s3_client():
        async with get_s3_client() as client:
            return client
    return _get_s3_client



def clean_path(path: str) -> str:
    return path.lstrip('/').rstrip('/')


def get_s3_uri(bucket: str, prefix: str = None, object_key: str = '') -> str:

    """Construct an S3 URI from components"""

    if prefix:
        return f"s3://{clean_path(bucket)}/{clean_path(prefix)}/{clean_path(object_key)}"
    return f"s3://{clean_path(bucket)}/{clean_path(object_key)}"


def parse_s3_uri(s3_uri: str) -> tuple[str, str, str]:

    """Parse an S3 URI into (bucket, prefix, object_key)"""

    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3":
        raise ValueError(f"Invalid S3 URI: {s3_uri}")

    bucket = parsed.netloc
    full_key = clean_path(parsed.path)

    if not full_key:
        return bucket, "", ""

    parts = full_key.rsplit("/", 1)
    prefix = parts[0] if len(parts) > 1 else ""
    object_key = parts[-1]

    return bucket, prefix, object_key


async def create_bucket(bucket_name: str = settings.s3_images_bucket):

    async with get_s3_client() as s3_client:
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


async def list_files(bucket_name: str = settings.s3_images_bucket, prefix: str = '') -> List:

    async with get_s3_client() as s3_client:
        response = await s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if 'Contents' in response:
            return [obj['Key'] for obj in response['Contents']]
        else:
            return []


async def upload_data_to_bucket(file_name: str, file_data: bytes, bucket_name: str = settings.s3_images_bucket, prefix: str = '') -> str:

    async with get_s3_client() as s3_client:
        full_key = f"{prefix}/{file_name}" if prefix else file_name
        try:
            await s3_client.put_object(Bucket=bucket_name, Key=full_key, Body=file_data)
            return get_s3_uri(bucket=bucket_name, object_key=full_key)
        except Exception as e:
            raise Exception(f"Error uploading file: {e}")


async def download_from_bucket(file_key: str, bucket_name: str = settings.s3_images_bucket, prefix: str = '') -> bytes:

    async with get_s3_client() as s3_client:
        full_key = f"{prefix}/{file_key}" if prefix else file_key
        try:
            response = await s3_client.get_object(Bucket=bucket_name, Key=full_key)
            file_data = await response['Body'].read()
            return file_data
        except Exception as e:
            raise Exception(f"Error downloading file: {e}")


async def delete_file(file_name: str, bucket_name: str = settings.s3_images_bucket, prefix: str = ''):

    async with get_s3_client() as s3_client:
        full_key = f"{prefix}/{file_name}" if prefix else file_name
        try:
            await s3_client.delete_object(Bucket=bucket_name, Key=full_key)
        except Exception as e:
            raise Exception(f"Error deleting file: {e}")


async def delete_folder(bucket_name: str, prefix: str) -> int:
    """Delete all files (objects) under a given prefix in the S3 bucket."""

    deleted_files = 0
    async with get_s3_client() as s3_client:
        try:
            files = await list_files(bucket_name=bucket_name, prefix=prefix)
            if files:
                for file_key in files:
                    await s3_client.delete_object(Bucket=bucket_name, Key=file_key)
                    deleted_files += 1
            else:
                logging.info(f"No files found under prefix '{prefix}' to delete.")

        except Exception as e:
            raise Exception(f"Error deleting folder with prefix {prefix}: {str(e)}")

    return deleted_files


async def base64_image_to_s3(file_name_wo_ext: str, base64_string: str, bucket_name: str = settings.s3_images_bucket, prefix: str = '') -> str:
    """Upload a base64-encoded image to S3"""

    try:
        # Extract MIME type from base64 string
        header, base64_data = base64_string.split(",", 1)
        mime_type = header.split(";")[0].split(":")[1]

        valid_mime_types = {"image/png", "image/jpg", "image/jpeg", "image/gif", "image/webp"}
        if mime_type not in valid_mime_types:
            raise ValueError(f"Unsupported MIME type: {mime_type}")

        ext = mimetypes.guess_extension(mime_type)
        if not ext:
            raise ValueError(f"Could not determine file extension for MIME type: {mime_type}")

        file_name_with_ext = f"{file_name_wo_ext}{ext}"

        image_data = base64.b64decode(base64_data)

        s3_uri = await upload_data_to_bucket(
            bucket_name=bucket_name, prefix=prefix, file_name=file_name_with_ext, file_data=image_data
        )

        logging.info(f"Image uploaded to S3: {s3_uri}")
        return s3_uri

    except Exception as e:
        raise Exception(f"Error uploading image {bucket_name}/{prefix}/{file_name_wo_ext}{ext}: {str(e)}")


async def s3_to_base64_image(file_key: str, bucket_name: str = settings.s3_images_bucket, prefix: str = '') -> str:
    """Download an image from S3 and convert it to a base64 string."""

    try:
        file_data = await download_from_bucket(bucket_name=bucket_name, file_key=file_key, prefix=prefix)
        base64_string = base64.b64encode(file_data).decode('utf-8')
        mime_type, _ = mimetypes.guess_type(file_key)
        mime_type = "application/octet-stream" if not mime_type else mime_type
        data = f"data:{mime_type};base64,{base64_string}"
        return data

    except Exception as e:
        logger.error(f"Error downloading image {bucket_name}/{prefix}/{file_key}: {str(e)}. It's not exist!")
        return None

