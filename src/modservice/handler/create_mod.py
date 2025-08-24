import grpc

from modservice.grpc import mod_pb2
from modservice.service.service import ModService


def CreateMod(
    service: ModService,
    request: mod_pb2.CreateModRequest,
    _: grpc.ServicerContext,
) -> mod_pb2.CreateModResponse:
    # Генерируем S3-ключ и presigned URL для загрузки
    s3_key, upload_url = service.generate_upload_url(
        author_id=request.author_id,
        filename=request.filename,
        mod_title=request.mod_title,
        expiration=3600,  # 1 час на загрузку
        content_type=None  # Автоматическое определение
    )
    
    # Создаем мод в базе данных
    mod_id, _, _ = service.create_mod(
        request.mod_title,
        request.author_id,
        request.filename,
        request.description,
    )
    
    return mod_pb2.CreateModResponse(
        mod_id=mod_id, 
        upload_url=upload_url, 
        s3_key=s3_key
    )
