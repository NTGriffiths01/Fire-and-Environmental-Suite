"""
AWS S3 Service for Fire and Environmental Safety Suite
Handles file upload, storage, and lifecycle management with 7-year retention
"""
import boto3
import asyncio
import aiofiles
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from botocore.exceptions import ClientError, NoCredentialsError
import mimetypes
import hashlib
import logging
from pathlib import Path
import json
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

class S3Service:
    """AWS S3 service with 7-year retention and compliance features"""
    
    def __init__(self):
        self.bucket_name = os.environ.get('AWS_S3_BUCKET', 'fire-safety-files')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.retention_days = 2555  # 7 years
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name=self.region
            )
        except NoCredentialsError:
            logger.error("AWS credentials not configured")
            raise HTTPException(status_code=500, detail="AWS credentials not configured")
    
    async def upload_file(self, 
                         file: UploadFile, 
                         file_type: str = "inspection_attachment",
                         facility_id: str = None,
                         inspection_id: str = None,
                         user_id: str = None) -> Dict[str, Any]:
        """
        Upload file to S3 with proper tagging and retention
        
        Args:
            file: FastAPI UploadFile object
            file_type: Type of file (inspection_attachment, report, template, etc.)
            facility_id: ID of the facility
            inspection_id: ID of the inspection
            user_id: ID of the user uploading
            
        Returns:
            Dictionary with file information
        """
        try:
            # Generate unique file key
            file_key = self._generate_file_key(file.filename, file_type, facility_id, inspection_id)
            
            # Read file content
            content = await file.read()
            
            # Calculate file hash for integrity
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Get file metadata
            content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            file_size = len(content)
            
            # Prepare tags for compliance
            tags = self._prepare_tags(file_type, facility_id, inspection_id, user_id, file_hash)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=content,
                ContentType=content_type,
                ServerSideEncryption='AES256',
                Tagging=self._format_tags(tags),
                Metadata={
                    'original_filename': file.filename,
                    'file_type': file_type,
                    'upload_timestamp': datetime.utcnow().isoformat(),
                    'file_hash': file_hash,
                    'uploaded_by': user_id or 'unknown',
                    'facility_id': facility_id or 'unknown',
                    'inspection_id': inspection_id or 'unknown'
                }
            )
            
            # Set lifecycle policy for 7-year retention
            await self._set_object_lifecycle(file_key)
            
            logger.info(f"File uploaded successfully: {file_key}")
            
            return {
                "file_key": file_key,
                "file_name": file.filename,
                "file_size": file_size,
                "content_type": content_type,
                "file_hash": file_hash,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "retention_until": (datetime.utcnow() + timedelta(days=self.retention_days)).isoformat(),
                "tags": tags,
                "s3_url": f"s3://{self.bucket_name}/{file_key}"
            }
            
        except ClientError as e:
            logger.error(f"AWS S3 error: {e}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {e}")
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
    
    async def download_file(self, file_key: str) -> Dict[str, Any]:
        """
        Download file from S3
        
        Args:
            file_key: S3 object key
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            content = response['Body'].read()
            
            return {
                "content": content,
                "content_type": response.get('ContentType', 'application/octet-stream'),
                "file_size": response.get('ContentLength', 0),
                "last_modified": response.get('LastModified'),
                "metadata": response.get('Metadata', {}),
                "tags": await self._get_object_tags(file_key)
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail="File not found")
            logger.error(f"AWS S3 error: {e}")
            raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")
    
    async def delete_file(self, file_key: str, user_id: str = None) -> bool:
        """
        Delete file from S3 (with audit logging)
        
        Args:
            file_key: S3 object key
            user_id: ID of user performing deletion
            
        Returns:
            True if successful
        """
        try:
            # Get file metadata before deletion for audit
            try:
                response = self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                metadata = response.get('Metadata', {})
            except ClientError:
                metadata = {}
            
            # Delete the object
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            # Log deletion for audit
            logger.info(f"File deleted: {file_key} by user: {user_id}")
            
            return True
            
        except ClientError as e:
            logger.error(f"AWS S3 error during deletion: {e}")
            raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")
    
    async def list_files(self, 
                        prefix: str = None,
                        facility_id: str = None,
                        inspection_id: str = None,
                        file_type: str = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        List files in S3 bucket with filtering
        
        Args:
            prefix: S3 key prefix to filter by
            facility_id: Filter by facility ID
            inspection_id: Filter by inspection ID
            file_type: Filter by file type
            limit: Maximum number of files to return
            
        Returns:
            List of file metadata
        """
        try:
            # Build prefix based on filters
            if not prefix:
                prefix = self._build_prefix(facility_id, inspection_id, file_type)
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                # Get object metadata and tags
                metadata = await self._get_object_metadata(obj['Key'])
                tags = await self._get_object_tags(obj['Key'])
                
                files.append({
                    "file_key": obj['Key'],
                    "file_name": metadata.get('original_filename', obj['Key'].split('/')[-1]),
                    "file_size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat(),
                    "file_type": metadata.get('file_type', 'unknown'),
                    "facility_id": metadata.get('facility_id'),
                    "inspection_id": metadata.get('inspection_id'),
                    "uploaded_by": metadata.get('uploaded_by'),
                    "file_hash": metadata.get('file_hash'),
                    "tags": tags
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"AWS S3 error: {e}")
            raise HTTPException(status_code=500, detail=f"File listing failed: {str(e)}")
    
    async def get_file_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Generate presigned URL for file access
        
        Args:
            file_key: S3 object key
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"AWS S3 error: {e}")
            raise HTTPException(status_code=500, detail=f"URL generation failed: {str(e)}")
    
    def _generate_file_key(self, 
                          filename: str, 
                          file_type: str, 
                          facility_id: str = None,
                          inspection_id: str = None) -> str:
        """Generate unique S3 key for file"""
        # Create hierarchical structure
        year = datetime.utcnow().year
        month = datetime.utcnow().month
        day = datetime.utcnow().day
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Clean filename
        clean_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        # Build key
        key_parts = [
            "fire-safety-suite",
            str(year),
            f"{month:02d}",
            f"{day:02d}",
            file_type
        ]
        
        if facility_id:
            key_parts.append(f"facility_{facility_id}")
        
        if inspection_id:
            key_parts.append(f"inspection_{inspection_id}")
        
        key_parts.append(f"{timestamp}_{clean_filename}")
        
        return "/".join(key_parts)
    
    def _prepare_tags(self, 
                     file_type: str, 
                     facility_id: str = None,
                     inspection_id: str = None,
                     user_id: str = None,
                     file_hash: str = None) -> Dict[str, str]:
        """Prepare tags for S3 object"""
        tags = {
            "FileType": file_type,
            "UploadDate": datetime.utcnow().strftime('%Y-%m-%d'),
            "Department": "MassachusettsDOC",
            "Application": "FireSafetySuite",
            "Retention": "7years",
            "RetentionUntil": (datetime.utcnow() + timedelta(days=self.retention_days)).strftime('%Y-%m-%d'),
            "ComplianceRequired": "true"
        }
        
        if facility_id:
            tags["FacilityID"] = facility_id
        
        if inspection_id:
            tags["InspectionID"] = inspection_id
        
        if user_id:
            tags["UploadedBy"] = user_id
        
        if file_hash:
            tags["FileHash"] = file_hash
        
        return tags
    
    def _format_tags(self, tags: Dict[str, str]) -> str:
        """Format tags for S3 API"""
        tag_pairs = []
        for key, value in tags.items():
            tag_pairs.append(f"{key}={value}")
        return "&".join(tag_pairs)
    
    async def _set_object_lifecycle(self, file_key: str):
        """Set lifecycle policy for individual object"""
        try:
            # Note: Individual object lifecycle is managed through bucket policy
            # This is a placeholder for additional object-specific lifecycle management
            pass
        except Exception as e:
            logger.warning(f"Could not set lifecycle for {file_key}: {e}")
    
    async def _get_object_metadata(self, file_key: str) -> Dict[str, Any]:
        """Get object metadata from S3"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return response.get('Metadata', {})
        except ClientError:
            return {}
    
    async def _get_object_tags(self, file_key: str) -> Dict[str, str]:
        """Get object tags from S3"""
        try:
            response = self.s3_client.get_object_tagging(
                Bucket=self.bucket_name,
                Key=file_key
            )
            tags = {}
            for tag in response.get('TagSet', []):
                tags[tag['Key']] = tag['Value']
            return tags
        except ClientError:
            return {}
    
    def _build_prefix(self, 
                     facility_id: str = None,
                     inspection_id: str = None,
                     file_type: str = None) -> str:
        """Build S3 prefix for filtering"""
        prefix_parts = ["fire-safety-suite"]
        
        if facility_id:
            prefix_parts.append(f"facility_{facility_id}")
        
        if inspection_id:
            prefix_parts.append(f"inspection_{inspection_id}")
        
        if file_type:
            prefix_parts.append(file_type)
        
        return "/".join(prefix_parts)
    
    async def cleanup_expired_files(self):
        """Clean up files that have exceeded retention period"""
        try:
            # List all objects
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="fire-safety-suite/"
            )
            
            expired_files = []
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    expired_files.append(obj['Key'])
            
            # Delete expired files
            for file_key in expired_files:
                await self.delete_file(file_key, user_id="system_cleanup")
            
            logger.info(f"Cleaned up {len(expired_files)} expired files")
            return len(expired_files)
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
    
    async def verify_file_integrity(self, file_key: str) -> bool:
        """Verify file integrity using stored hash"""
        try:
            # Get file content and metadata
            file_data = await self.download_file(file_key)
            stored_hash = file_data['metadata'].get('file_hash')
            
            if not stored_hash:
                logger.warning(f"No hash found for file {file_key}")
                return False
            
            # Calculate current hash
            current_hash = hashlib.sha256(file_data['content']).hexdigest()
            
            # Compare hashes
            if stored_hash == current_hash:
                logger.info(f"File integrity verified: {file_key}")
                return True
            else:
                logger.error(f"File integrity check failed: {file_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying file integrity: {e}")
            return False
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage statistics for reporting"""
        try:
            # Get bucket statistics
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix="fire-safety-suite/"
            )
            
            total_files = 0
            total_size = 0
            file_types = {}
            
            for obj in response.get('Contents', []):
                total_files += 1
                total_size += obj['Size']
                
                # Get file type from metadata
                try:
                    metadata = await self._get_object_metadata(obj['Key'])
                    file_type = metadata.get('file_type', 'unknown')
                    file_types[file_type] = file_types.get(file_type, 0) + 1
                except:
                    file_types['unknown'] = file_types.get('unknown', 0) + 1
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "average_file_size": round(total_size / total_files, 2) if total_files > 0 else 0,
                "bucket_name": self.bucket_name,
                "retention_days": self.retention_days
            }
            
        except Exception as e:
            logger.error(f"Error getting storage statistics: {e}")
            return {}