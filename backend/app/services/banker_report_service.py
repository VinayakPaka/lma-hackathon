"""
GreenGuard ESG Platform - Banker Report Service
Generates audit-ready JSON and PDF/HTML reports for KPI evaluations.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from app.services.sbti_data_service import sbti_data_service
from app.services.credibility_service import credibility_service
from app.services.yahoo_esg_service import yahoo_esg_service
from app.services.compliance_service import compliance_checker

logger = logging.getLogger(__name__)


@dataclass
class ReportHeader:
    company_name: str
    lei: Optional[str]
    ticker: Optional[str]
    loan_type: str
    facility_amount: str
    tenor_years: int
    margin_adjustment_bps: Optional[int]
    analysis_date: str
    analyst: str = "System Generated"
    review_required: bool = True


@dataclass
class KPITarget:
    metric: str
    baseline_value: float
    baseline_unit: str
    baseline_year: int
    target_value: float
    target_unit: str
    target_year: int
    reduction_percentage: float
    scope: str


class BankerReportService:
    """
    Generate banker-ready reports in JSON and PDF format.
    
    Report Structure:
    1. Header (company, deal, date)
    2. Executive Summary (1 page)
    3. Baseline Assessment
    4. Peer Benchmarking
    5. Achievability & Credibility
    6. Risk Flags & Recommendations
    7. Regulatory Compliance Checklist
    8. Final Recommendation & Conditions
    
    Tone Guidelines:
    - Conservative language ("suggests" not "proves")
    - Explicit uncertainty ("Based on 12 peers, medium confidence")
    - Actionable recommendations
    - Evidence citations with page numbers
    """
    
    RECOMMENDATION_LEVELS = {
        "APPROVE": "Approval - Target meets or exceeds expectations",
        "CONDITIONAL_APPROVAL": "Conditional Approval - Requires specified conditions",
        "NEGOTIATE": "Negotiate - Recommend target enhancement before approval",
        "REJECT": "Reject - Insufficient ambition or credibility"
    }
    
    def generate_full_report(
        self,
        evaluation_data: Dict[str, Any],
        extraction_data: Dict[str, Any],
        ambition_result: Dict[str, Any],
        credibility_result: Dict[str, Any],
        compliance_result: Dict[str, Any],
        esg_scores: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete banker report from all assessment components.
        
        Returns:
            Complete JSON report (source of truth)
        """
        # Build report header
        header = self._build_header(evaluation_data)
        
        # Build primary KPI target info
        kpi_target = self._build_kpi_target(evaluation_data, extraction_data)
        
        # Determine recommendation
        recommendation = self._determine_recommendation(
            ambition_result, credibility_result, compliance_result
        )
        
        # Build risk flags
        risk_flags = self._build_risk_flags(
            ambition_result, credibility_result, esg_scores
        )
        
        # Build audit trail
        audit_trail = self._build_audit_trail(evaluation_data)
        
        report = {
            "schema_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "system_version": "GreenGuard KPI Engine v1.0",
            
            "report_header": {
                "company_name": header.company_name,
                "company_identifiers": {
                    "lei": header.lei,
                    "ticker": header.ticker
                },
                "deal_details": {
                    "loan_type": header.loan_type,
                    "facility_amount": header.facility_amount,
                    "tenor_years": header.tenor_years,
                    "margin_adjustment_bps": header.margin_adjustment_bps
                },
                "analysis_date": header.analysis_date,
                "analyst": header.analyst,
                "review_required": header.review_required
            },
            
            "executive_summary": {
                "primary_kpi": {
                    "metric": kpi_target.metric,
                    "baseline": {
                        "value": kpi_target.baseline_value,
                        "unit": kpi_target.baseline_unit,
                        "year": kpi_target.baseline_year
                    },
                    "target": {
                        "value": kpi_target.target_value,
                        "unit": kpi_target.target_unit,
                        "year": kpi_target.target_year,
                        "reduction_percentage": kpi_target.reduction_percentage
                    },
                    "scope": kpi_target.scope
                },
                "overall_recommendation": recommendation["level"],
                "recommendation_rationale": recommendation["rationale"],
                # AI-generated narrative summary
                "ai_narrative": extraction_data.get("ai_summaries", {}).get("executive_summary", {}).get("narrative", ""),
                "ai_key_points": extraction_data.get("ai_summaries", {}).get("executive_summary", {}).get("key_points", []),
                "key_findings": self._build_key_findings(
                    extraction_data, ambition_result, credibility_result
                ),
                "conditions_for_approval": recommendation["conditions"]
            },
            
            "baseline_assessment": self._build_baseline_assessment(
                evaluation_data, extraction_data
            ),
            
            "peer_benchmarking": {
                "methodology": "SBTi targets dataset, filtered by sector and scope",
                "sector_matching": ambition_result.get("sector_matching", {}),
                "peer_selection": ambition_result.get("filters_applied", {}),
                "peer_statistics": {
                    "peer_count": ambition_result.get("peer_count", 0),
                    "confidence_level": ambition_result.get("confidence_level", "UNKNOWN"),
                    "percentiles": {
                        "median": ambition_result.get("peer_median"),
                        "p75": ambition_result.get("peer_p75")
                    }
                },
                "company_position": {
                    "percentile_rank": ambition_result.get("percentile_rank"),
                    "vs_median": ambition_result.get("gap_to_median"),
                    "vs_p75": ambition_result.get("gap_to_p75"),
                    "classification": ambition_result.get("classification", "UNKNOWN")
                },
                "ambition_classification": {
                    "level": ambition_result.get("classification"),
                    "rationale": ambition_result.get("rationale"),
                    # AI-generated detailed analysis
                    "ai_detailed_analysis": extraction_data.get("ai_summaries", {}).get("ambition_analysis", {}).get("detailed_analysis", ""),
                    "classification_explanation": extraction_data.get("ai_summaries", {}).get("ambition_analysis", {}).get("classification_explanation", "")
                },
                "recommendation": ambition_result.get("recommendation", {}),
                "data_limitations": self._build_data_limitations(ambition_result)
            },
            
            "achievability_assessment": {
                "credibility_level": credibility_result.get("credibility_level", "UNKNOWN"),
                "credibility_rationale": credibility_result.get("credibility_rationale"),
                # AI-generated detailed analysis
                "ai_detailed_analysis": extraction_data.get("ai_summaries", {}).get("credibility_analysis", {}).get("detailed_analysis", ""),
                "signals": credibility_result.get("signals", {}),
                "signal_summary": credibility_result.get("signal_summary", {}),
                "strength_areas": extraction_data.get("ai_summaries", {}).get("credibility_analysis", {}).get("strength_areas", []),
                "improvement_areas": extraction_data.get("ai_summaries", {}).get("credibility_analysis", {}).get("improvement_areas", []),
                "gaps": credibility_result.get("gaps", []),
                # Evidence from documents
                "evidence": {
                    "governance_evidence": extraction_data.get("governance_signals", {}),
                    "verification_evidence": extraction_data.get("verification_status", {}),
                    "past_performance": extraction_data.get("past_performance", {})
                }
            },
            
            "risk_flags": risk_flags,
            
            "esg_risk_context": self._build_esg_context(esg_scores) if esg_scores else None,
            
            "regulatory_compliance": {
                "summary": compliance_checker.generate_compliance_summary(compliance_result),
                "detailed_results": compliance_result.get("results", {}),
                "gaps": compliance_result.get("total_gaps", [])
            },
            
            "final_decision": {
                "recommendation": recommendation["level"],
                "confidence": self._calculate_overall_confidence(
                    ambition_result, credibility_result
                ),
                "conditions": recommendation["condition_details"],
                "next_steps": self._build_next_steps(recommendation["level"])
            },
            
            "audit_trail": audit_trail
        }
        
        return report
    
    def _build_header(self, evaluation_data: Dict) -> ReportHeader:
        """Build report header from evaluation data."""
        return ReportHeader(
            company_name=evaluation_data.get("company_name", "Unknown"),
            lei=evaluation_data.get("lei"),
            ticker=evaluation_data.get("ticker"),
            loan_type=evaluation_data.get("loan_type", "Sustainability-Linked Loan"),
            facility_amount=evaluation_data.get("facility_amount", "Not specified"),
            tenor_years=evaluation_data.get("tenor_years", 0),
            margin_adjustment_bps=evaluation_data.get("margin_adjustment_bps"),
            analysis_date=datetime.now().strftime("%Y-%m-%d"),
            review_required=True
        )
    
    def _build_kpi_target(
        self,
        evaluation_data: Dict,
        extraction_data: Dict
    ) -> KPITarget:
        """Build KPI target object."""
        # Get extracted KPIs or use evaluation input
        kpi_targets = extraction_data.get("kpi_targets", [])
        primary_kpi = kpi_targets[0] if kpi_targets else {}
        
        baseline_value = evaluation_data.get("baseline_value") or primary_kpi.get("baseline_value", 0)
        target_value = evaluation_data.get("target_value") or primary_kpi.get("target_value", 0)
        
        # Calculate reduction percentage
        reduction_pct = 0
        if baseline_value and target_value:
            reduction_pct = round((1 - target_value / baseline_value) * 100, 1)
        
        return KPITarget(
            metric=evaluation_data.get("metric", primary_kpi.get("metric_name", "GHG Emissions")),
            baseline_value=baseline_value,
            baseline_unit=evaluation_data.get("baseline_unit", primary_kpi.get("target_unit", "tCO2e")),
            baseline_year=evaluation_data.get("baseline_year") or primary_kpi.get("baseline_year", 2022),
            target_value=target_value,
            target_unit=evaluation_data.get("target_unit", primary_kpi.get("target_unit", "tCO2e")),
            target_year=evaluation_data.get("timeline_end_year") or primary_kpi.get("target_year", 2030),
            reduction_percentage=reduction_pct,
            scope=evaluation_data.get("emissions_scope", primary_kpi.get("scope", "Scope 1+2"))
        )
    
    def _build_key_findings(
        self,
        extraction_data: Dict,
        ambition_result: Dict,
        credibility_result: Dict
    ) -> List[Dict[str, str]]:
        """Build key findings summary."""
        findings = []
        
        # Baseline quality
        verification = extraction_data.get("verification", {})
        if verification.get("third_party_verified"):
            findings.append({
                "category": "baseline",
                "assessment": "STRONG",
                "detail": f"Baseline externally verified by {verification.get('verifier_name', 'third party')}"
            })
        else:
            findings.append({
                "category": "baseline",
                "assessment": "MODERATE",
                "detail": "Baseline verification status unclear"
            })
        
        # Ambition
        ambition_class = ambition_result.get("classification", "UNKNOWN")
        findings.append({
            "category": "ambition",
            "assessment": ambition_class,
            "detail": ambition_result.get("rationale", "Unable to assess ambition")
        })
        
        # Achievability
        cred_level = credibility_result.get("credibility_level", "UNKNOWN")
        signal_count = credibility_result.get("signal_summary", {}).get("detected_count", 0)
        findings.append({
            "category": "achievability",
            "assessment": cred_level,
            "detail": f"{signal_count} credibility signals present"
        })
        
        # Science alignment
        sbti_aligned = ambition_result.get("sbti_aligned", False)
        findings.append({
            "category": "science_alignment",
            "assessment": "ALIGNED" if sbti_aligned else "NOT_ALIGNED",
            "detail": "SBTi validated" if sbti_aligned else "No SBTi validation"
        })
        
        return findings
    
    def _determine_recommendation(
        self,
        ambition_result: Dict,
        credibility_result: Dict,
        compliance_result: Dict
    ) -> Dict[str, Any]:
        """
        Determine overall recommendation based on assessments.
        
        Logic:
        - APPROVE: Above market + High credibility + All compliant
        - CONDITIONAL_APPROVAL: Any yellow flags but manageable
        - NEGOTIATE: Weak ambition but fixable
        - REJECT: Multiple red flags or low credibility
        """
        ambition_class = ambition_result.get("classification", "UNKNOWN")
        cred_level = credibility_result.get("credibility_level", "UNKNOWN")
        compliance_gaps = len(compliance_result.get("total_gaps", []))
        
        conditions = []
        condition_details = []
        
        # Check for red flags
        red_flags = 0
        
        if ambition_class == "WEAK":
            red_flags += 1
            conditions.append(f"Increase target to ≥{ambition_result.get('peer_median', 'peer median')}%")
            condition_details.append({
                "condition": "Target Enhancement",
                "detail": f"Increase reduction target to at least peer median ({ambition_result.get('peer_median')}%)",
                "priority": "HIGH",
                "negotiable": True
            })
        
        if cred_level == "LOW":
            red_flags += 1
            conditions.append("Strengthen credibility indicators")
            condition_details.append({
                "condition": "Credibility Enhancement",
                "detail": "Provide additional verification or governance evidence",
                "priority": "HIGH",
                "negotiable": True
            })
        
        if compliance_gaps > 0:
            conditions.append("Address regulatory compliance gaps")
            condition_details.append({
                "condition": "Compliance Remediation",
                "detail": f"Address {compliance_gaps} compliance gap(s)",
                "priority": "MEDIUM",
                "negotiable": False
            })
        
        # Add SBTi condition if not validated and above market
        if ambition_class in ["ABOVE_MARKET", "MARKET_STANDARD"] and not ambition_result.get("sbti_aligned"):
            conditions.append("Consider SBTi validation commitment")
            condition_details.append({
                "condition": "SBTi Validation",
                "detail": "Commit to SBTi validation within 18 months",
                "priority": "MEDIUM",
                "negotiable": True
            })
        
        # Determine recommendation level
        if red_flags >= 2:
            level = "NEGOTIATE"
            rationale = "Multiple concerns require negotiation before approval"
        elif red_flags == 1:
            level = "CONDITIONAL_APPROVAL"
            rationale = "Approval subject to specified conditions"
        elif ambition_class in ["ABOVE_MARKET", "SCIENCE_ALIGNED"] and cred_level == "HIGH":
            level = "APPROVE"
            rationale = "Strong ambition and credibility support approval"
            conditions = []  # No conditions for straight approval
            condition_details = []
        else:
            level = "CONDITIONAL_APPROVAL"
            rationale = "Approval recommended with standard conditions"
        
        return {
            "level": level,
            "rationale": rationale,
            "conditions": conditions,
            "condition_details": condition_details
        }
    
    def _build_baseline_assessment(
        self,
        evaluation_data: Dict,
        extraction_data: Dict
    ) -> Dict[str, Any]:
        """Build baseline assessment section."""
        verification = extraction_data.get("verification", {})
        baseline_verification = extraction_data.get("baseline_verification", {})
        
        # Use SBTi-based verification if available (NEW!)
        if baseline_verification.get("level") == "HIGH":
            quality = "EXCELLENT"
            verification_source = baseline_verification.get("source", "SBTi Database")
            verification_rationale = baseline_verification.get("rationale", "SBTi validated baseline")
        elif verification.get("third_party_verified"):
            quality = "EXCELLENT"
            verification_source = verification.get("verifier_name", "Third Party")
            verification_rationale = "Third-party verified baseline"
        elif verification.get("assurance_level") == "limited":
            quality = "GOOD"
            verification_source = "Limited Assurance"
            verification_rationale = "Limited assurance provided"
        else:
            quality = baseline_verification.get("level", "MODERATE")
            verification_source = baseline_verification.get("source", "Self-reported")
            verification_rationale = baseline_verification.get("rationale", "Self-reported baseline, no external verification")
        
        return {
            "data_quality": {
                "score": quality,
                "factors": {
                    "verification": verification_source,
                    "verifier": verification.get("verifier_name") or baseline_verification.get("source"),
                    "assurance_level": verification.get("assurance_level") or baseline_verification.get("level"),
                    "methodology_disclosed": True,  # Assume from CSRD requirement
                    "sbti_validated": baseline_verification.get("level") == "HIGH"
                },
                "rationale": verification_rationale
            },
            "baseline_value": evaluation_data.get("baseline_value"),
            "baseline_year": evaluation_data.get("baseline_year"),
            "evidence": verification.get("evidence_quote") or baseline_verification.get("rationale")
        }
    
    def _build_risk_flags(
        self,
        ambition_result: Dict,
        credibility_result: Dict,
        esg_scores: Optional[Dict]
    ) -> List[Dict[str, str]]:
        """Build risk flags for the report."""
        flags = []
        
        # Ambition flags
        if ambition_result.get("classification") == "WEAK":
            flags.append({
                "severity": "MEDIUM",
                "category": "ambition",
                "issue": "Target below peer median",
                "recommendation": f"Negotiate target increase to ≥{ambition_result.get('peer_median')}%",
                "mitigant": "Strong credibility signals may partially offset"
            })
        
        # Credibility flags
        missing_signals = credibility_result.get("signal_summary", {}).get("missing_signals", [])
        for signal in missing_signals[:2]:  # Limit to top 2
            flags.append({
                "severity": "LOW",
                "category": "credibility",
                "issue": f"No evidence of {signal.replace('_', ' ')}",
                "recommendation": f"Request disclosure of {signal.replace('_', ' ')}"
            })
        
        # ESG risk flags
        if esg_scores:
            flags.extend(yahoo_esg_service.get_risk_flags(esg_scores.get("ticker", "")))
        
        return flags
    
    def _build_esg_context(self, esg_scores: Dict) -> Dict[str, Any]:
        """Build ESG context section."""
        if not esg_scores or not esg_scores.get("available"):
            return {
                "available": False,
                "note": "ESG risk data not available for this company"
            }
        
        return {
            "source": esg_scores.get("data_source"),
            "scores": esg_scores.get("scores", {}),
            "risk_level": esg_scores.get("risk_level"),
            "interpretation": esg_scores.get("interpretation"),
            "delivery_risk_flagged": esg_scores.get("delivery_risk_flag"),
            "caveat": esg_scores.get("caveat")
        }
    
    def _build_data_limitations(self, ambition_result: Dict) -> List[str]:
        """Build list of data limitations."""
        limitations = []
        
        peer_count = ambition_result.get("peer_count", 0)
        if peer_count < 15:
            limitations.append(f"Peer pool limited to {peer_count} companies")
        
        conf_level = ambition_result.get("confidence_level", "")
        if conf_level in ["MEDIUM", "LOW"]:
            limitations.append(f"{conf_level} confidence in percentile estimates")
        
        match_quality = ambition_result.get("match_quality", "")
        if match_quality != "exact":
            limitations.append(f"Sector matching quality: {match_quality}")
        
        return limitations
    
    def _calculate_overall_confidence(
        self,
        ambition_result: Dict,
        credibility_result: Dict
    ) -> str:
        """Calculate overall confidence level."""
        ambition_conf = ambition_result.get("confidence_level", "UNKNOWN")
        cred_level = credibility_result.get("credibility_level", "UNKNOWN")
        
        # Map to numeric for averaging
        level_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0, "INSUFFICIENT": 0}
        
        avg = (level_map.get(ambition_conf, 0) + level_map.get(cred_level, 0)) / 2
        
        if avg >= 2.5:
            return "HIGH"
        elif avg >= 1.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _build_next_steps(self, recommendation: str) -> List[Dict[str, str]]:
        """Build next steps based on recommendation."""
        base_steps = [
            {"step": 1, "action": "Banker review of this assessment", "owner": "Credit Officer"},
        ]
        
        if recommendation in ["CONDITIONAL_APPROVAL", "NEGOTIATE"]:
            base_steps.append(
                {"step": 2, "action": "Company negotiation on conditions", "owner": "Relationship Manager"}
            )
            base_steps.append(
                {"step": 3, "action": "External Second Party Opinion (if required)", "owner": "ESG Team"}
            )
        
        base_steps.append(
            {"step": len(base_steps) + 1, "action": "Final documentation", "owner": "Legal"}
        )
        
        return base_steps
    
    def _build_audit_trail(self, evaluation_data: Dict) -> Dict[str, Any]:
        """Build audit trail section."""
        return {
            "data_sources": [
                {
                    "source": "Borrower Documents",
                    "type": "borrower_document",
                    "document_ids": evaluation_data.get("document_ids", [])
                },
                {
                    "source": "SBTi Companies Dataset",
                    "type": "external_database",
                    "version": "2024-Q4",
                    "query_date": datetime.now().strftime("%Y-%m-%d")
                }
            ],
            "ai_usage": {
                "document_extraction": {
                    "model": "Gemini 1.5 Pro / Perplexity Sonar",
                    "usage": "KPI and governance extraction from PDFs"
                },
                "not_used_for": [
                    "Ambition scoring",
                    "Achievability scoring",
                    "Approval decisions",
                    "Peer benchmark calculations"
                ]
            },
            "calculation_reproducibility": {
                "peer_percentiles": "numpy.percentile on SQL-extracted targets",
                "ambition_classification": "Rule-based thresholds (median, P75)",
                "credibility_score": "Signal counting algorithm"
            }
        }
    
    def generate_pdf(
        self,
        report: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF report from JSON report data.
        
        Args:
            report: The JSON report data
            output_path: Optional file path to save PDF
        
        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor("#1a5f2a")
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor("#2d7a4a")
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        )
        
        story = []
        
        # Title
        header = report.get("report_header", {})
        story.append(Paragraph(
            f"KPI Benchmarking Assessment",
            title_style
        ))
        story.append(Paragraph(
            f"<b>{header.get('company_name', 'Unknown Company')}</b>",
            styles['Heading2']
        ))
        story.append(Paragraph(
            f"{header.get('deal_details', {}).get('loan_type', '')} | {header.get('analysis_date', '')}",
            body_style
        ))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        exec_summary = report.get("executive_summary", {})
        story.append(Paragraph("Executive Summary", header_style))
        
        recommendation = exec_summary.get("overall_recommendation", "PENDING")
        rec_color = {
            "APPROVE": "#22c55e",
            "CONDITIONAL_APPROVAL": "#f59e0b", 
            "NEGOTIATE": "#ef4444",
            "REJECT": "#dc2626"
        }.get(recommendation, "#6b7280")
        
        story.append(Paragraph(
            f"<b>Recommendation:</b> <font color='{rec_color}'>{recommendation}</font>",
            body_style
        ))
        story.append(Paragraph(
            f"{exec_summary.get('recommendation_rationale', '')}",
            body_style
        ))
        story.append(Spacer(1, 10))
        
        # Key Findings table
        findings = exec_summary.get("key_findings", [])
        if findings:
            findings_data = [["Category", "Assessment", "Detail"]]
            for f in findings:
                findings_data.append([
                    f.get("category", "").title(),
                    f.get("assessment", ""),
                    f.get("detail", "")[:60] + "..." if len(f.get("detail", "")) > 60 else f.get("detail", "")
                ])
            
            findings_table = Table(findings_data, colWidths=[80, 80, 280])
            findings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2d7a4a")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(findings_table)
        
        story.append(PageBreak())
        
        # Peer Benchmarking
        story.append(Paragraph("Peer Benchmarking", header_style))
        benchmarking = report.get("peer_benchmarking", {})
        
        bench_text = f"""
        <b>Peer Count:</b> {benchmarking.get('peer_statistics', {}).get('peer_count', 'N/A')}<br/>
        <b>Confidence Level:</b> {benchmarking.get('peer_statistics', {}).get('confidence_level', 'N/A')}<br/>
        <b>Peer Median:</b> {benchmarking.get('peer_statistics', {}).get('percentiles', {}).get('median', 'N/A')}%<br/>
        <b>75th Percentile:</b> {benchmarking.get('peer_statistics', {}).get('percentiles', {}).get('p75', 'N/A')}%<br/>
        <b>Company Position:</b> {benchmarking.get('company_position', {}).get('classification', 'N/A')}
        """
        story.append(Paragraph(bench_text, body_style))
        story.append(Spacer(1, 15))
        
        # Achievability
        story.append(Paragraph("Achievability Assessment", header_style))
        achievability = report.get("achievability_assessment", {})
        story.append(Paragraph(
            f"<b>Credibility Level:</b> {achievability.get('credibility_level', 'N/A')}",
            body_style
        ))
        
        signals = achievability.get("signals", {})
        if signals:
            signal_list = []
            for name, data in signals.items():
                status = "✓" if data.get("detected") else "✗"
                signal_list.append(ListItem(Paragraph(
                    f"{status} {name.replace('_', ' ').title()}",
                    body_style
                )))
            story.append(ListFlowable(signal_list, bulletType='bullet'))
        
        story.append(Spacer(1, 15))
        
        # Evidence & Source Citations (NEW SECTION)
        story.append(Paragraph("Evidence & Source Citations", header_style))
        
        evidence = achievability.get("evidence", {})
        has_evidence = False
        
        # AI Narrative Summary
        ai_narrative = report.get("executive_summary", {}).get("ai_narrative", "")
        if ai_narrative:
            has_evidence = True
            story.append(Paragraph(
                f"<b>AI Analysis Summary:</b> {ai_narrative[:500]}{'...' if len(ai_narrative) > 500 else ''}",
                body_style
            ))
            story.append(Spacer(1, 8))
        
        # Sector Matching Evidence
        sector_matching = report.get("peer_benchmarking", {}).get("sector_matching", {})
        if sector_matching:
            has_evidence = True
            source = sector_matching.get("match_source", "")
            matched_sector = sector_matching.get("matched_sbti_sector", "")
            reasoning = sector_matching.get("match_reasoning", "")
            
            sector_text = f"<b>Sector Classification:</b> {matched_sector}"
            if source == "sbti_direct_lookup":
                sector_text += " (Direct SBTi database match - HIGH confidence)"
            elif reasoning:
                sector_text += f" - {reasoning[:100]}"
            story.append(Paragraph(sector_text, body_style))
            story.append(Spacer(1, 8))
        
        # Governance Evidence
        governance = evidence.get("governance_evidence", {})
        if governance and governance.get("evidence_quote"):
            has_evidence = True
            story.append(Paragraph(
                f"<b>Governance Evidence:</b> \"{governance.get('evidence_quote', '')[:200]}...\"",
                body_style
            ))
            if governance.get("page_number"):
                story.append(Paragraph(
                    f"<i>Source: Page {governance.get('page_number')}</i>",
                    body_style
                ))
            story.append(Spacer(1, 8))
        
        # Verification Evidence
        verification = evidence.get("verification_evidence", {})
        if verification and verification.get("evidence_quote"):
            has_evidence = True
            verifier = verification.get("verifier_name", "Third Party")
            story.append(Paragraph(
                f"<b>Verification Status:</b> Verified by {verifier}",
                body_style
            ))
            story.append(Paragraph(
                f"\"{verification.get('evidence_quote', '')[:200]}...\"",
                body_style
            ))
            story.append(Spacer(1, 8))
        
        # Past Performance Evidence
        past_perf = evidence.get("past_performance", {})
        if past_perf and past_perf.get("evidence_quote"):
            has_evidence = True
            story.append(Paragraph(
                f"<b>Past Target Achievement:</b> \"{past_perf.get('evidence_quote', '')[:200]}...\"",
                body_style
            ))
            story.append(Spacer(1, 8))
        
        if not has_evidence:
            story.append(Paragraph(
                "<i>No document evidence extracted. Upload CSRD or SPT documents for detailed citations.</i>",
                body_style
            ))
        
        story.append(Spacer(1, 15))
        
        # Regulatory Compliance
        story.append(Paragraph("Regulatory Compliance", header_style))
        compliance = report.get("regulatory_compliance", {}).get("summary", {})
        compliance_data = [["Framework", "Status"]]
        for framework, status in compliance.items():
            compliance_data.append([
                framework.replace("_", " ").upper(),
                "✓ Compliant" if status else "✗ Gap"
            ])
        
        compliance_table = Table(compliance_data, colWidths=[200, 150])
        compliance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2d7a4a")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(compliance_table)
        story.append(Spacer(1, 15))
        
        # Conditions (if any)
        conditions = report.get("final_decision", {}).get("conditions", [])
        if conditions:
            story.append(Paragraph("Conditions for Approval", header_style))
            for cond in conditions:
                story.append(Paragraph(f"• {cond.get('detail', cond)}", body_style))
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        
        return pdf_bytes
    
    def generate_executive_summary_text(self, report: Dict[str, Any]) -> str:
        """
        Generate executive summary as plain text for quick review.
        """
        header = report.get("report_header", {})
        exec_summary = report.get("executive_summary", {})
        kpi = exec_summary.get("primary_kpi", {})
        benchmarking = report.get("peer_benchmarking", {})
        
        summary = f"""
**{header.get('company_name', 'Unknown')} – {header.get('deal_details', {}).get('facility_amount', '')} {header.get('deal_details', {}).get('loan_type', '')}**

**KPI Assessment: {kpi.get('metric', 'Emissions Reduction')}**

{header.get('company_name')}'s proposed target of {kpi.get('target', {}).get('reduction_percentage', 0)}% reduction by {kpi.get('target', {}).get('year', 'N/A')} {'is at' if benchmarking.get('company_position', {}).get('classification') != 'WEAK' else 'falls below'} the peer median of {benchmarking.get('peer_statistics', {}).get('percentiles', {}).get('median', 'N/A')}% for {benchmarking.get('peer_selection', {}).get('sector', 'comparable')} companies.

The baseline of {kpi.get('baseline', {}).get('value', 0):,.0f} {kpi.get('baseline', {}).get('unit', 'tCO2e')} ({kpi.get('baseline', {}).get('year', 'N/A')}) is {'externally verified' if report.get('baseline_assessment', {}).get('data_quality', {}).get('verification') == 'third_party_verified' else 'self-reported'}.

While ambition is assessed as **{benchmarking.get('ambition_classification', {}).get('level', 'Unknown')}**, achievability credibility is **{report.get('achievability_assessment', {}).get('credibility_level', 'Unknown')}**.

**Recommendation: {exec_summary.get('overall_recommendation', 'Pending')}**

{exec_summary.get('recommendation_rationale', '')}

*Note: This assessment is based on {benchmarking.get('peer_statistics', {}).get('peer_count', 0)} peer companies ({benchmarking.get('peer_statistics', {}).get('confidence_level', 'unknown')} confidence). Percentile rankings should be interpreted directionally.*
"""
        return summary.strip()


# Singleton instance
banker_report_service = BankerReportService()
