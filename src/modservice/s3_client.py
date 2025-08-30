from botocore.session import get_session


class S3Client:
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        bucket_name: str,
        verify: bool,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "verify": verify,
        }
        self.bucket_name = bucket_name
        self.session = get_session()

    def get_client(self):
        return self.session.create_client("s3", **self.config)

    def upload_file(self, file_path: str):
        object_name = file_path.split("/")[-1]
        client = self.get_client()
        with open(file_path, "rb") as file:
            client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file,
            )

    def generate_presigned_put_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        content_type: (
            str | None
        ) = None,  # Keep parameter for compatibility but ignore it
    ) -> str:
        client = self.get_client()
        params = {
            "Bucket": self.bucket_name,
            "Key": s3_key,
        }
        # NEVER add ContentType to avoid signature mismatch issues

        try:
            presigned_url = client.generate_presigned_url(
                "put_object", Params=params, ExpiresIn=expiration
            )
            return presigned_url
        except Exception as e:
            raise Exception(
                f"Ошибка при генерации presigned PUT URL: {e!s}"
            ) from e

    def generate_presigned_get_url(
        self,
        s3_key: str,
        expiration: int = 3600,
    ) -> str:
        client = self.get_client()
        params = {
            "Bucket": self.bucket_name,
            "Key": s3_key,
        }

        try:
            presigned_url = client.generate_presigned_url(
                "get_object", Params=params, ExpiresIn=expiration
            )
            return presigned_url
        except Exception as e:
            raise Exception(
                f"Ошибка при генерации presigned GET URL: {e!s}"
            ) from e
