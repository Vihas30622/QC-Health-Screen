from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


class DiseaseInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    key: str
    display_name: str
    description: str
    model_status: str


class DiseaseListResponse(BaseModel):
    diseases: List[DiseaseInfo]


class HealthResponse(BaseModel):
    status: str
    version: str
