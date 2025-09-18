from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Environment
    debug: bool = False
    environment: str = "development"
    
    # S3 Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket_name: Optional[str] = None
    s3_region: str = "us-east-1"
    s3_base_url: Optional[str] = None
    
    # Upload settings
    max_upload_size: int = 5242880  # 5MB
    allowed_image_extensions: str = "jpg,jpeg,png,webp,gif"
    allowed_doc_extensions: str = "pdf,doc,docx"
    max_images_per_owner: int = 4
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def allowed_image_ext_list(self) -> List[str]:
        return [ext.strip() for ext in self.allowed_image_extensions.split(",")]
    
    @property
    def allowed_doc_ext_list(self) -> List[str]:
        return [ext.strip() for ext in self.allowed_doc_extensions.split(",")]
    
    class Config:
        env_file = ".env"


settings = Settings()