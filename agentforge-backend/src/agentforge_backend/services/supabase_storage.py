"""
Supabase Storage Service

Handles file storage operations through Supabase Storage including:
- Upload files to buckets
- Generate signed URLs
- Delete files
- List files
- Manage bucket policies
"""
import logging
import mimetypes
import os
from typing import Optional, List, Dict, Any, BinaryIO
from uuid import uuid4
from datetime import timedelta

from supabase import Client
from supabase.lib.client_options import ClientOptions

from ..core.supabase import get_supabase_admin, get_supabase
from ..config.settings import settings
from ..utils.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """Service for managing file storage through Supabase Storage."""
    
    # Default bucket configurations
    BUCKETS = {
        "agent-assets": {
            "public": False,
            "max_size": 50 * 1024 * 1024,  # 50MB
            "allowed_types": ["image/*", "application/pdf", "text/*", "application/json"],
        },
        "workspace-files": {
            "public": False,
            "max_size": 100 * 1024 * 1024,  # 100MB
            "allowed_types": ["*/*"],  # All types
        },
        "avatars": {
            "public": True,
            "max_size": 5 * 1024 * 1024,  # 5MB
            "allowed_types": ["image/*"],
        },
        "documents": {
            "public": False,
            "max_size": 50 * 1024 * 1024,  # 50MB
            "allowed_types": ["application/pdf", "text/*", "application/msword", 
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            "application/vnd.ms-excel",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            "text/csv"],
        },
    }
    
    def __init__(self, use_admin: bool = True):
        """
        Initialize storage service.
        
        Args:
            use_admin: If True, use service role client for admin operations.
        """
        self._use_admin = use_admin
        self._client: Optional[Client] = None
    
    @property
    async def client(self) -> Client:
        """Get the Supabase client."""
        if self._client is None:
            if self._use_admin:
                self._client = await get_supabase_admin()
            else:
                self._client = await get_supabase()
        return self._client
    
    def _get_client_sync(self) -> Client:
        """Get synchronous client for non-async operations."""
        if self._use_admin:
            return get_supabase_admin_sync()
        return get_supabase_sync()
    
    # ==================== Bucket Management ====================
    
    async def ensure_buckets_exist(self) -> Dict[str, bool]:
        """
        Ensure all configured buckets exist.
        
        Returns:
            Dict mapping bucket names to creation status
        """
        client = await self.client
        results = {}
        
        for bucket_name, config in self.BUCKETS.items():
            try:
                # Try to get bucket info
                await client.storage.get_bucket(bucket_name)
                results[bucket_name] = True
                logger.info(f"Bucket '{bucket_name}' already exists")
            except Exception:
                # Bucket doesn't exist, create it
                try:
                    await client.storage.create_bucket(
                        bucket_name,
                        options={
                            "public": config["public"],
                            "allowed_mime_types": config["allowed_types"],
                            "file_size_limit": config["max_size"],
                        }
                    )
                    results[bucket_name] = True
                    logger.info(f"Created bucket '{bucket_name}'")
                except Exception as e:
                    logger.error(f"Failed to create bucket '{bucket_name}': {e}")
                    results[bucket_name] = False
        
        return results
    
    async def create_bucket(
        self,
        name: str,
        public: bool = False,
        allowed_mime_types: Optional[List[str]] = None,
        file_size_limit: Optional[int] = None,
    ) -> bool:
        """
        Create a new storage bucket.
        
        Args:
            name: Bucket name
            public: Whether bucket is public
            allowed_mime_types: List of allowed MIME types
            file_size_limit: Maximum file size in bytes
            
        Returns:
            True if successful
        """
        try:
            client = await self.client
            await client.storage.create_bucket(
                name,
                options={
                    "public": public,
                    "allowed_mime_types": allowed_mime_types or ["*/*"],
                    "file_size_limit": file_size_limit or 50 * 1024 * 1024,
                }
            )
            logger.info(f"Created bucket '{name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to create bucket '{name}': {e}")
            raise DatabaseError(f"Failed to create bucket: {str(e)}") from e
    
    async def delete_bucket(self, name: str) -> bool:
        """
        Delete a storage bucket.
        
        Args:
            name: Bucket name
            
        Returns:
            True if successful
        """
        try:
            client = await self.client
            await client.storage.delete_bucket(name)
            logger.info(f"Deleted bucket '{name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete bucket '{name}': {e}")
            return False
    
    # ==================== File Operations ====================
    
    async def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        upsert: bool = False,
    ) -> Dict[str, Any]:
        """
        Upload a file to a bucket.
        
        Args:
            bucket: Bucket name
            file_path: Path within bucket (e.g., "user_id/filename.pdf")
            file_data: File content as bytes
            content_type: MIME type (auto-detected if not provided)
            upsert: Whether to overwrite existing file
            
        Returns:
            Dict with file info (path, full_path, size, etc.)
        """
        try:
            client = await self.client
            
            # Auto-detect content type
            if content_type is None:
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = "application/octet-stream"
            
            # Validate bucket
            if bucket not in self.BUCKETS:
                logger.warning(f"Bucket '{bucket}' not in configured buckets, allowing anyway")
            
            # Check file size
            max_size = self.BUCKETS.get(bucket, {}).get("max_size", 50 * 1024 * 1024)
            if len(file_data) > max_size:
                raise DatabaseError(f"File size exceeds limit of {max_size} bytes")
            
            # Upload
            response = await client.storage.from_(bucket).upload(
                path=file_path,
                file=file_data,
                file_options={
                    "content-type": content_type,
                    "upsert": upsert,
                },
            )
            
            logger.info(f"Uploaded file to '{bucket}/{file_path}' ({len(file_data)} bytes)")
            
            return {
                "path": file_path,
                "full_path": response.get("fullPath") or file_path,
                "size": len(file_data),
                "content_type": content_type,
                "bucket": bucket,
            }
            
        except Exception as e:
            logger.error(f"Upload error for '{bucket}/{file_path}': {e}")
            raise DatabaseError(f"Upload failed: {str(e)}") from e
    
    async def upload_file_stream(
        self,
        bucket: str,
        file_path: str,
        file_stream: BinaryIO,
        content_type: Optional[str] = None,
        upsert: bool = False,
    ) -> Dict[str, Any]:
        """
        Upload a file from a stream.
        
        Args:
            bucket: Bucket name
            file_path: Path within bucket
            file_stream: File-like object
            content_type: MIME type
            upsert: Whether to overwrite existing
            
        Returns:
            Dict with file info
        """
        file_data = file_stream.read()
        return await self.upload_file(bucket, file_path, file_data, content_type, upsert)
    
    async def download_file(self, bucket: str, file_path: str) -> bytes:
        """
        Download a file from a bucket.
        
        Args:
            bucket: Bucket name
            file_path: Path within bucket
            
        Returns:
            File content as bytes
        """
        try:
            client = await self.client
            response = await client.storage.from_(bucket).download(file_path)
            return response
        except Exception as e:
            logger.error(f"Download error for '{bucket}/{file_path}': {e}")
            raise DatabaseError(f"Download failed: {str(e)}") from e
    
    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Delete a file from a bucket.
        
        Args:
            bucket: Bucket name
            file_path: Path within bucket
            
        Returns:
            True if successful
        """
        try:
            client = await self.client
            await client.storage.from_(bucket).remove([file_path])
            logger.info(f"Deleted file '{bucket}/{file_path}'")
            return True
        except Exception as e:
            logger.error(f"Delete error for '{bucket}/{file_path}': {e}")
            return False
    
    async def delete_files(self, bucket: str, file_paths: List[str]) -> Dict[str, bool]:
        """
        Delete multiple files from a bucket.
        
        Args:
            bucket: Bucket name
            file_paths: List of file paths
            
        Returns:
            Dict mapping paths to deletion status
        """
        try:
            client = await self.client
            await client.storage.from_(bucket).remove(file_paths)
            return {path: True for path in file_paths}
        except Exception as e:
            logger.error(f"Batch delete error: {e}")
            return {path: False for path in file_paths}
    
    async def list_files(
        self,
        bucket: str,
        folder: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List files in a bucket/folder.
        
        Args:
            bucket: Bucket name
            folder: Folder path to list
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of file info dicts
        """
        try:
            client = await self.client
            response = await client.storage.from_(bucket).list(
                path=folder,
                options={
                    "limit": limit,
                    "offset": offset,
                },
            )
            
            files = []
            for item in response:
                if item.get("metadata"):  # It's a file, not a folder
                    files.append({
                        "name": item["name"],
                        "path": f"{folder}/{item['name']}".lstrip("/"),
                        "size": item["metadata"].get("size", 0),
                        "content_type": item["metadata"].get("mimetype"),
                        "created_at": item["metadata"].get("created_at"),
                        "updated_at": item["metadata"].get("updated_at"),
                        "etag": item["metadata"].get("etag"),
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"List files error for '{bucket}/{folder}': {e}")
            raise DatabaseError(f"List failed: {str(e)}") from e
    
    # ==================== Signed URLs ====================
    
    async def create_signed_url(
        self,
        bucket: str,
        file_path: str,
        expires_in: int = 3600,
    ) -> str:
        """
        Create a signed URL for temporary file access.
        
        Args:
            bucket: Bucket name
            file_path: Path within bucket
            expires_in: Expiration time in seconds (default 1 hour)
            
        Returns:
            Signed URL string
        """
        try:
            client = await self.client
            response = await client.storage.from_(bucket).create_signed_url(
                file_path,
                expires_in,
            )
            return response["signedURL"]
        except Exception as e:
            logger.error(f"Signed URL error for '{bucket}/{file_path}': {e}")
            raise DatabaseError(f"Failed to create signed URL: {str(e)}") from e
    
    async def create_signed_urls(
        self,
        bucket: str,
        file_paths: List[str],
        expires_in: int = 3600,
    ) -> Dict[str, str]:
        """
        Create multiple signed URLs at once.
        
        Args:
            bucket: Bucket name
            file_paths: List of file paths
            expires_in: Expiration time in seconds
            
        Returns:
            Dict mapping file paths to signed URLs
        """
        try:
            client = await self.client
            response = await client.storage.from_(bucket).create_signed_urls(
                file_paths,
                expires_in,
            )
            return {item["path"]: item["signedURL"] for item in response}
        except Exception as e:
            logger.error(f"Batch signed URLs error: {e}")
            raise DatabaseError(f"Failed to create signed URLs: {str(e)}") from e
    
    async def create_signed_upload_url(
        self,
        bucket: str,
        file_path: str,
        expires_in: int = 3600,
    ) -> Dict[str, str]:
        """
        Create a signed URL for direct client-side upload.
        
        Args:
            bucket: Bucket name
            file_path: Path within bucket
            expires_in: Expiration time in seconds
            
        Returns:
            Dict with signed URL and token
        """
        try:
            client = await self.client
            response = await client.storage.from_(bucket).create_signed_upload_url(
                file_path,
                expires_in,
            )
            return {
                "url": response["signedURL"],
                "token": response["token"],
            }
        except Exception as e:
            logger.error(f"Signed upload URL error: {e}")
            raise DatabaseError(f"Failed to create signed upload URL: {str(e)}") from e
    
    # ==================== File Info ====================
    
    async def get_file_info(self, bucket: str, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata.
        
        Args:
            bucket: Bucket name
            file_path: Path within bucket
            
        Returns:
            File info dict or None if not found
        """
        try:
            client = await self.client
            response = await client.storage.from_(bucket).list(
                path=os.path.dirname(file_path) or "",
            )
            
            filename = os.path.basename(file_path)
            for item in response:
                if item["name"] == filename and item.get("metadata"):
                    meta = item["metadata"]
                    return {
                        "name": item["name"],
                        "path": file_path,
                        "size": meta.get("size", 0),
                        "content_type": meta.get("mimetype"),
                        "created_at": meta.get("created_at"),
                        "updated_at": meta.get("updated_at"),
                        "etag": meta.get("etag"),
                    }
            return None
        except Exception as e:
            logger.error(f"Get file info error: {e}")
            return None
    
    # ==================== Move/Copy ====================
    
    async def move_file(
        self,
        bucket: str,
        from_path: str,
        to_path: str,
    ) -> bool:
        """
        Move/rename a file within a bucket.
        
        Args:
            bucket: Bucket name
            from_path: Source path
            to_path: Destination path
            
        Returns:
            True if successful
        """
        try:
            client = await self.client
            await client.storage.from_(bucket).move(from_path, to_path)
            return True
        except Exception as e:
            logger.error(f"Move file error: {e}")
            return False
    
    async def copy_file(
        self,
        bucket: str,
        from_path: str,
        to_path: str,
    ) -> bool:
        """
        Copy a file within a bucket.
        
        Args:
            bucket: Bucket name
            from_path: Source path
            to_path: Destination path
            
        Returns:
            True if successful
        """
        try:
            client = await self.client
            await client.storage.from_(bucket).copy(from_path, to_path)
            return True
        except Exception as e:
            logger.error(f"Copy file error: {e}")
            return False
    
    # ==================== Helpers ====================
    
    def get_public_url(self, bucket: str, file_path: str) -> str:
        """
        Get public URL for a file (only works for public buckets).
        
        Args:
            bucket: Bucket name
            file_path: Path within bucket
            
        Returns:
            Public URL string
        """
        client = self._get_client_sync()
        response = client.storage.from_(bucket).get_public_url(file_path)
        return response["publicURL"]
    
    def validate_file_type(self, bucket: str, content_type: str) -> bool:
        """
        Check if content type is allowed for bucket.
        
        Args:
            bucket: Bucket name
            content_type: MIME type
            
        Returns:
            True if allowed
        """
        config = self.BUCKETS.get(bucket, {})
        allowed = config.get("allowed_types", ["*/*"])
        
        for allowed_type in allowed:
            if allowed_type == "*/*":
                return True
            if allowed_type.endswith("/*"):
                if content_type.startswith(allowed_type[:-1]):
                    return True
            if content_type == allowed_type:
                return True
        
        return False
    
    def generate_file_path(
        self,
        user_id: str,
        filename: str,
        folder: str = "",
    ) -> str:
        """
        Generate a secure file path.
        
        Args:
            user_id: User ID
            filename: Original filename
            folder: Optional subfolder
            
        Returns:
            Generated path
        """
        ext = os.path.splitext(filename)[1].lower()
        unique_name = f"{uuid4().hex}{ext}"
        
        parts = []
        if folder:
            parts.append(folder)
        parts.append(user_id)
        parts.append(unique_name)
        
        return "/".join(parts)


# Global service instance
_storage_service: Optional[SupabaseStorageService] = None


async def get_storage_service(use_admin: bool = True) -> SupabaseStorageService:
    """Get or create the storage service."""
    global _storage_service
    
    if _storage_service is None:
        _storage_service = SupabaseStorageService(use_admin=use_admin)
        # Ensure buckets exist
        await _storage_service.ensure_buckets_exist()
    
    return _storage_service