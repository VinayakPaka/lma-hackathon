"""
GreenGuard ESG Platform - KPI Benchmarking Router
"""
import logging
from fastapi import APIRouter
from app.schemas.kpi_schema import KPIBenchmarkResponse
from app.services.kpi_service import kpi_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sectors")
async def get_sectors():
    return {"sectors": kpi_service.get_sectors()}


@router.get("/metrics/{sector}")
async def get_metrics(sector: str):
    return {"sector": sector, "metrics": kpi_service.get_metrics(sector)}


@router.get("/benchmark/{sector}/{metric}", response_model=KPIBenchmarkResponse)
async def get_benchmark(sector: str, metric: str):
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
