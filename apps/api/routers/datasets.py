from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from apps.api.db.connection import get_db_connection

router = APIRouter(tags=["datasets"])


class DatasetCreate(BaseModel):
    """Schema for registering a new dataset."""

    name: str = Field(..., min_length=1, description="Dataset name")
    description: str | None = Field(default=None, description="Dataset description")
    source: str | None = Field(default=None, description="Dataset source or origin")


class DatasetResponse(BaseModel):
    """Schema for dataset response."""

    id: UUID
    name: str
    description: str | None = None
    source: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


@router.get("/api/v1/datasets", response_model=list[DatasetResponse])
def list_datasets() -> list[DatasetResponse]:
    """Retrieve all datasets from PostgreSQL."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT id, name, description, source, status, created_at, updated_at
                    FROM datasets
                    ORDER BY created_at DESC;
                    """
                )
                rows = cur.fetchall()
                return [DatasetResponse(**row) for row in rows]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve datasets from database",
        ) from e


@router.post(
    "/api/v1/datasets",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dataset(payload: DatasetCreate) -> DatasetResponse:
    """Insert a new dataset record into PostgreSQL."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    INSERT INTO datasets (name, description, source)
                    VALUES (%s, %s, %s)
                    RETURNING
                        id, name, description, source, status, created_at, updated_at;
                    """,
                    (payload.name, payload.description, payload.source),
                )
                row = cur.fetchone()
                conn.commit()

                if row is None:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to insert dataset record",
                    )
                return DatasetResponse(**row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to create dataset in database",
        ) from e
