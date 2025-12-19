"""
Supabase Service - Manages Supabase Storage operations for image uploads.
"""
import logging
import uuid
from typing import Optional
from pathlib import Path

from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from app.config import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service for Supabase Storage operations."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.bucket_name = settings.SUPABASE_BUCKET_NAME
        self.initialized = False
    
    def _ensure_initialized(self) -> None:
        """Ensure Supabase client is initialized."""
        if self.initialized and self.client:
            return
        
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_KEY
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "Supabase is not configured. Please set SUPABASE_URL and SUPABASE_KEY "
                "in your environment variables."
            )
        
        try:
            self.client = create_client(
                supabase_url,
                supabase_key,
                options=ClientOptions(
                    auto_refresh_token=True,
                    persist_session=False
                )
            )
            self.initialized = True
            logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            raise
    
    def upload_image(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload an image to Supabase Storage and return the public URL.
        
        Args:
            file_bytes: Image file bytes
            filename: Original filename (will be used to determine extension)
            content_type: MIME type of the image (default: "image/jpeg")
            
        Returns:
            Public URL of the uploaded image
            
        Raises:
            ValueError: If Supabase is not configured
            Exception: If upload fails
        """
        self._ensure_initialized()
        
        # Generate unique filename to avoid conflicts
        file_ext = Path(filename).suffix or self._get_extension_from_content_type(content_type)
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = f"{unique_filename}"
        
        try:
            # Upload to Supabase Storage
            self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options={
                    "content-type": content_type,
                    "upsert": "true"  # Overwrite if exists
                }
            )
            
            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            
            logger.info(f"Image uploaded successfully: {file_path}")
            return public_url
            
        except Exception as e:
            logger.error(f"Error uploading image to Supabase: {e}")
            raise
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete an image from Supabase Storage.
        
        Args:
            image_url: Public URL of the image to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        self._ensure_initialized()
        
        try:
            # Extract file path from URL
            # URL format: https://xxx.supabase.co/storage/v1/object/public/bucket-name/path/to/file.jpg
            file_path = self._extract_path_from_url(image_url)
            
            if not file_path:
                logger.warning(f"Could not extract file path from URL: {image_url}")
                return False
            
            # Delete from Supabase Storage
            self.client.storage.from_(self.bucket_name).remove([file_path])
            
            logger.info(f"Image deleted successfully: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting image from Supabase: {e}")
            return False
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type."""
        content_type_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        return content_type_map.get(content_type.lower(), ".jpg")
    
    def _extract_path_from_url(self, url: str) -> Optional[str]:
        """Extract file path from Supabase Storage public URL."""
        try:
            # URL format: https://xxx.supabase.co/storage/v1/object/public/bucket-name/path/to/file.jpg
            parts = url.split("/storage/v1/object/public/")
            if len(parts) != 2:
                return None
            
            path_with_bucket = parts[1]
            # Remove bucket name from path
            if path_with_bucket.startswith(f"{self.bucket_name}/"):
                return path_with_bucket[len(f"{self.bucket_name}/"):]
            elif path_with_bucket == self.bucket_name:
                # URL might not have a path after bucket name
                return None
            else:
                # Bucket name might be different, try to extract just the filename
                return path_with_bucket.split("/", 1)[-1] if "/" in path_with_bucket else path_with_bucket
        except Exception as e:
            logger.error(f"Error extracting path from URL: {e}")
            return None


# Global Supabase service instance
supabase_service = SupabaseService()

