from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CRIN_",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://crplatform:crplatform@localhost:5433/crplatform"
    database_url_sync: str = "postgresql://crplatform:crplatform@localhost:5433/crplatform"

    # Redis
    redis_url: str = "redis://localhost:6380/0"

    # S3 / MinIO
    s3_endpoint_url: str = "http://localhost:9010"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "cr-artifacts"
    s3_region: str = "us-east-1"

    # App
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Celery
    celery_broker_url: str = "redis://localhost:6380/0"
    celery_result_backend: str = "redis://localhost:6380/1"

    # Discovery
    rubricator_base_url: str = "https://cr.minzdrav.gov.ru"
    rubricator_list_path: str = "clin-rec"
    rubricator_list_fallback_path: str = "clin_recomend"
    rubricator_view_path: str = "clin-rec/view"
    rubricator_pdf_path: str = "clin-rec/pdf"
    rubricator_api_base_url: str = "https://apicr.minzdrav.gov.ru/api.ashx"
    rubricator_api_list_op: str = "GetJsonClinrecsFilterV2"
    rubricator_api_page_size: int = 100
    rubricator_api_request_delay: float = 1.0
    rubricator_api_user_agent: str = "ClinRecPlatform/1.0 (+https://github.com/kkobanenko/Clin-rec)"
    discovery_concurrency: int = 2
    discovery_request_delay: float = 2.0
    discovery_max_records: int = 20
    discovery_mode: str = "smoke"

    # Sentry
    sentry_dsn: str = ""

    # Streamlit
    streamlit_port: int = 8501

    # Generated output files (memo and filing artifacts) on the local filesystem.
    output_files_dir: str = "var/crin_outputs"


settings = Settings()
