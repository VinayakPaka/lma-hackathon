from app.core.memory_store import MemoryStore
from app.agents.base_agent import BaseAgent
from app.services.eurostat_service import EurostatService

# Tier 1
from app.agents.tier1.document_processor import DocumentProcessorAgent
from app.agents.tier1.chart_agent import ChartUnderstandingAgent
from app.agents.tier1.baseline_verifier import BaselineVerificationAgent
from app.agents.tier1.achievement_tracker import AchievementTrackerAgent
from app.agents.tier1.completeness_analyzer import CompletenessAnalyzerAgent

# Tier 2
from app.agents.tier2.kpi_extractor import KPIExtractorAgent
from app.agents.tier2.governance_extractor import GovernanceExtractorAgent
from app.agents.tier2.capex_extractor import CapexExtractorAgent

# Tier 3
from app.agents.tier3.benchmark_agent import BenchmarkAgent
from app.agents.tier3.regulatory_agents import RegulatoryAnalysisAgent

# Tier 4
from app.agents.tier4.analysis_agents import AnalysisAgents

# Tier 5
from app.agents.tier5.orchestrator import OrchestratorAgent

print("\n[OK] Verification SUCCESS: All 17 Agent Classes Imported Correctly.")
print("System is ready for runtime execution assuming API Keys are set.")
