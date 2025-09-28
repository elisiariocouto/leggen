"""API routes for backup management."""

from fastapi import APIRouter, HTTPException
from loguru import logger

from leggen.api.models.backup import (
    BackupOperation,
    BackupSettings,
    BackupTest,
    S3Config,
)
from leggen.api.models.common import APIResponse
from leggen.models.config import S3BackupConfig
from leggen.services.backup_service import BackupService
from leggen.utils.config import config
from leggen.utils.paths import path_manager

router = APIRouter()


@router.get("/backup/settings", response_model=APIResponse)
async def get_backup_settings() -> APIResponse:
    """Get current backup settings."""
    try:
        backup_config = config.backup_config

        # Build response safely without exposing secrets
        s3_config = backup_config.get("s3", {})

        settings = BackupSettings(
            s3=S3Config(
                access_key_id="***" if s3_config.get("access_key_id") else "",
                secret_access_key="***" if s3_config.get("secret_access_key") else "",
                bucket_name=s3_config.get("bucket_name", ""),
                region=s3_config.get("region", "us-east-1"),
                endpoint_url=s3_config.get("endpoint_url"),
                path_style=s3_config.get("path_style", False),
                enabled=s3_config.get("enabled", True),
            )
            if s3_config.get("bucket_name")
            else None,
        )

        return APIResponse(
            success=True,
            data=settings,
            message="Backup settings retrieved successfully",
        )

    except Exception as e:
        logger.error(f"Failed to get backup settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get backup settings: {str(e)}"
        ) from e


@router.put("/backup/settings", response_model=APIResponse)
async def update_backup_settings(settings: BackupSettings) -> APIResponse:
    """Update backup settings."""
    try:
        # First test the connection if S3 config is provided
        if settings.s3:
            # Convert API model to config model
            s3_config = S3BackupConfig(
                access_key_id=settings.s3.access_key_id,
                secret_access_key=settings.s3.secret_access_key,
                bucket_name=settings.s3.bucket_name,
                region=settings.s3.region,
                endpoint_url=settings.s3.endpoint_url,
                path_style=settings.s3.path_style,
                enabled=settings.s3.enabled,
            )

            # Test connection
            backup_service = BackupService()
            connection_success = await backup_service.test_connection(s3_config)

            if not connection_success:
                raise HTTPException(
                    status_code=400,
                    detail="S3 connection test failed. Please check your configuration.",
                )

        # Update backup config
        backup_config = {}

        if settings.s3:
            backup_config["s3"] = {
                "access_key_id": settings.s3.access_key_id,
                "secret_access_key": settings.s3.secret_access_key,
                "bucket_name": settings.s3.bucket_name,
                "region": settings.s3.region,
                "endpoint_url": settings.s3.endpoint_url,
                "path_style": settings.s3.path_style,
                "enabled": settings.s3.enabled,
            }

        # Save to config
        if backup_config:
            config.update_section("backup", backup_config)

        return APIResponse(
            success=True,
            data={"updated": True},
            message="Backup settings updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update backup settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update backup settings: {str(e)}"
        ) from e


@router.post("/backup/test", response_model=APIResponse)
async def test_backup_connection(test_request: BackupTest) -> APIResponse:
    """Test backup connection."""
    try:
        if test_request.service != "s3":
            raise HTTPException(
                status_code=400, detail="Only 's3' service is supported"
            )

        # Convert API model to config model
        s3_config = S3BackupConfig(
            access_key_id=test_request.config.access_key_id,
            secret_access_key=test_request.config.secret_access_key,
            bucket_name=test_request.config.bucket_name,
            region=test_request.config.region,
            endpoint_url=test_request.config.endpoint_url,
            path_style=test_request.config.path_style,
            enabled=test_request.config.enabled,
        )

        backup_service = BackupService()
        success = await backup_service.test_connection(s3_config)

        if success:
            return APIResponse(
                success=True,
                data={"connected": True},
                message="S3 connection test successful",
            )
        else:
            return APIResponse(
                success=False,
                message="S3 connection test failed",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test backup connection: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to test backup connection: {str(e)}"
        ) from e


@router.get("/backup/list", response_model=APIResponse)
async def list_backups() -> APIResponse:
    """List available backups."""
    try:
        backup_config = config.backup_config.get("s3", {})

        if not backup_config.get("bucket_name"):
            return APIResponse(
                success=True,
                data=[],
                message="No S3 backup configuration found",
            )

        # Convert config to model
        s3_config = S3BackupConfig(**backup_config)
        backup_service = BackupService(s3_config)

        backups = await backup_service.list_backups()

        return APIResponse(
            success=True,
            data=backups,
            message=f"Found {len(backups)} backups",
        )

    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list backups: {str(e)}"
        ) from e


@router.post("/backup/operation", response_model=APIResponse)
async def backup_operation(operation_request: BackupOperation) -> APIResponse:
    """Perform backup operation (backup or restore)."""
    try:
        backup_config = config.backup_config.get("s3", {})

        if not backup_config.get("bucket_name"):
            raise HTTPException(status_code=400, detail="S3 backup is not configured")

        # Convert config to model with validation
        try:
            s3_config = S3BackupConfig(**backup_config)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid S3 configuration: {str(e)}"
            ) from e

        backup_service = BackupService(s3_config)

        if operation_request.operation == "backup":
            # Backup database
            database_path = path_manager.get_database_path()
            success = await backup_service.backup_database(database_path)

            if success:
                return APIResponse(
                    success=True,
                    data={"operation": "backup", "completed": True},
                    message="Database backup completed successfully",
                )
            else:
                return APIResponse(
                    success=False,
                    message="Database backup failed",
                )

        elif operation_request.operation == "restore":
            if not operation_request.backup_key:
                raise HTTPException(
                    status_code=400,
                    detail="backup_key is required for restore operation",
                )

            # Restore database
            database_path = path_manager.get_database_path()
            success = await backup_service.restore_database(
                operation_request.backup_key, database_path
            )

            if success:
                return APIResponse(
                    success=True,
                    data={"operation": "restore", "completed": True},
                    message="Database restore completed successfully",
                )
            else:
                return APIResponse(
                    success=False,
                    message="Database restore failed",
                )
        else:
            raise HTTPException(
                status_code=400, detail="Invalid operation. Use 'backup' or 'restore'"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform backup operation: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to perform backup operation: {str(e)}"
        ) from e
