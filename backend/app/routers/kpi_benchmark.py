"""
GreenGuard ESG Platform - KPI Benchmarking Router
"""
import logging
from fastapi import APIRouter, Depends
from app.schemas.kpi_schema import KPIBenchmarkResponse
from app.services.kpi_service import kpi_service
from app.models.user import User
from app.utils.jwt_handler import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sectors")
async def get_sectors(current_user: User = Depends(get_current_user)):
    return {"sectors": kpi_service.get_sectors()}


@router.get("/metrics/{sector}")
async def get_metrics(sector: str, current_user: User = Depends(get_current_user)):
    return {"sector": sector, "metrics": kpi_service.get_metrics(sector)}


@router.get("/benchmark/{sector}/{metric}", response_model=KPIBenchmarkResponse)
async def get_benchmark(
    sector: str,
    metric: str,
    current_user: User = Depends(get_current_user)
):
    result = kpi_service.get_benchmark(sector, metric)
    if not result:
        return KPIBenchmarkResponse(
            sector=sector,
            metric=metric,
            baseline_range={"min": 0, "max": 0},
            market_average=0,
            ambitious_target=0,
            recommendation="No benchmark data available for this sector/metric combination"
        )
    return KPIBenchmarkResponse(**result)

