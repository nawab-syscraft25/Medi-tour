from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path


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
    
    max_upload_size: int = 5242880  # 5MB
    allowed_image_extensions: str = "jpg,jpeg,png,webp,gif"
    allowed_doc_extensions: str = "pdf,doc,docx"
    max_images_per_owner: int = 4
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 30
    
    # Razorpay Configuration
    razorpay_key_id: Optional[str] = None
    razorpay_key_secret: Optional[str] = None
    
    # SMTP Email Configuration
    smtp_server: Optional[str] = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    
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
        # Look for .env file in the project root directory
        env_file = Path(__file__).parent.parent.parent / ".env"
        env_file_encoding = 'utf-8'


settings = Settings()