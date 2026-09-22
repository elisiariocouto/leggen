"""API routes for backup management."""

from fastapi import APIRouter
from pydantic import ValidationError

from leggen.api.models.backup import (
    BackupInfo,
    BackupOperation,
    BackupSettings,
    BackupTest,
    S3Config,
)
from leggen.errors import BadRequestError, LeggenError
from leggen.models.config import S3BackupConfig
from leggen.services.backup_service import BackupService
from leggen.utils.config import config
from leggen.utils.masking import mask_secret, resolve_secret
from leggen.utils.paths import path_manager

router = APIRouter()


@router.get("/backup/settings")
async def get_backup_settings() -> BackupSettings:
    """Get current backup settings."""
    backup_config = config.backup_config

    # Build response safely without exposing secrets
    s3_config = backup_config.get("s3", {})

    return BackupSettings(
        s3=S3Config(
            access_key_id=mask_secret(s3_config.get("access_key_id")),
            secret_access_key=mask_secret(s3_config.get("secret_access_key")),
            bucket_name=s3_config.get("bucket_name", ""),
            region=s3_config.get("region", "us-east-1"),
            endpoint_url=s3_config.get("endpoint_url"),
            path_style=s3_config.get("path_style", False),
            enabled=s3_config.get("enabled", True),
        )
        if s3_config.get("bucket_name")
        else None,
    )


@router.put("/backup/settings", status_code=204)
async def update_backup_settings(settings: BackupSettings) -> None:
    """Update backup settings."""
    if settings.s3 is None:
        # Reporting success for a request that changes nothing hides the
        # mistake; removing the configuration has its own endpoint.
        raise BadRequestError(
            "s3 configuration is required. Use DELETE /backup/settings to remove it."
        )

    # Clients echo back masked secrets from GET to mean "keep current value";
    # a mask with nothing stored raises MaskedSecretError, a 400.
    stored_s3 = config.backup_config.get("s3", {})
    access_key_id = resolve_secret(
        settings.s3.access_key_id, stored_s3.get("access_key_id"), "S3 access key ID"
    )
    secret_access_key = resolve_secret(
        settings.s3.secret_access_key,
        stored_s3.get("secret_access_key"),
        "S3 secret access key",
    )

    s3_config = settings.s3.model_copy(
        update={"access_key_id": access_key_id, "secret_access_key": secret_access_key}
    )

    # Test connection, unless the config is being disabled —
    # turning S3 off must not require working credentials
    if s3_config.enabled:
        backup_service = BackupService()
        connection_success = await backup_service.test_connection(s3_config)

        if not connection_success:
            raise BadRequestError(
                "S3 connection test failed. Please check your configuration."
            )

    config.update_section("backup", {"s3": s3_config.model_dump()})


@router.delete("/backup/settings", status_code=204)
async def delete_backup_settings() -> None:
    """Remove the S3 backup configuration, including its stored credentials."""
    config.update_section("backup", {})


@router.post("/backup/test", status_code=204)
async def test_backup_connection(test_request: BackupTest) -> None:
    """Test backup connection."""
    # Clients may submit masked secrets meaning "test with the stored value"
    stored_s3 = config.backup_config.get("s3", {})
    access_key_id = resolve_secret(
        test_request.config.access_key_id,
        stored_s3.get("access_key_id"),
        "S3 access key ID",
    )
    secret_access_key = resolve_secret(
        test_request.config.secret_access_key,
        stored_s3.get("secret_access_key"),
        "S3 secret access key",
    )

    s3_config = test_request.config.model_copy(
        update={"access_key_id": access_key_id, "secret_access_key": secret_access_key}
    )

    backup_service = BackupService()
    success = await backup_service.test_connection(s3_config)

    if not success:
        raise BadRequestError("S3 connection test failed")


@router.get("/backup/list", response_model=list[BackupInfo])
async def list_backups() -> list[dict]:
    """List available backups."""
    backup_config = config.backup_config.get("s3", {})

    if not backup_config.get("bucket_name"):
        return []

    # Convert config to model
    s3_config = S3BackupConfig(**backup_config)
    backup_service = BackupService(s3_config)

    return await backup_service.list_backups()


@router.post("/backup/operation", status_code=204)
async def backup_operation(operation_request: BackupOperation) -> None:
    """Perform backup operation (backup or restore)."""
    backup_config = config.backup_config.get("s3", {})

    if not backup_config.get("bucket_name"):
        raise BadRequestError("S3 backup is not configured")

    # Convert config to model with validation
    try:
        s3_config = S3BackupConfig(**backup_config)
    except ValidationError as e:
        raise BadRequestError("Invalid S3 configuration.") from e

    backup_service = BackupService(s3_config)

    if operation_request.operation == "backup":
        # Backup database
        database_path = path_manager.get_database_path()
        success = await backup_service.backup_database(database_path)

        if not success:
            raise LeggenError("Database backup failed")

    else:
        if not operation_request.backup_key:
            raise BadRequestError("backup_key is required for restore operation")

        # Restore database
        database_path = path_manager.get_database_path()
        success = await backup_service.restore_database(
            operation_request.backup_key, database_path
        )

        if not success:
            raise LeggenError("Database restore failed")
