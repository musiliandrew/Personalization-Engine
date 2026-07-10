import os
import json
import requests
from typing import Dict, Any, List

from shared.contracts.requests.evaluate_match import EvaluateMatchRequest, JobRequirementSnapshot
from shared.contracts.responses.mission import IntelligenceSnapshot
from shared.contracts.responses.decision_result import DecisionResult

class ExplainMatchScoreResult:
    """
    Adapter to mimic the old ExplainMatchScore outcome format.
    The caller expects:
    1. result.conclusion: a dict with 'overall_score', 'matched_skills', 'missing_skills'
    2. result.confidence: a float
    3. result.evidence_used: a list of strings
    """
    def __init__(self, overall_score: float, matched_skills: List[str], missing_skills: List[str], confidence: float, evidence_used: List[str]):
        self.conclusion = {
            "overall_score": overall_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        }
        self.confidence = confidence
        self.evidence_used = evidence_used

class ExplainMatchScore:
    """
    Integrates personalization-system with the decision-engine service.
    """
    def __init__(self):
        # Allow configuring URL, default to localhost for development
        self.decision_engine_url = os.getenv("DECISION_ENGINE_URL", "http://localhost:8003")

    def execute(self, twin: Dict[str, Any], required_skills: List[str] = None) -> ExplainMatchScoreResult:
        if required_skills is None:
            required_skills = []

        # 1. Build request payload
        # Map Career Twin fields to IntelligenceSnapshot
        goals = twin.get("goals", {})
        target_role = goals.get("target_role") or "Software Engineer"
        
        profile_snapshot = IntelligenceSnapshot(
            version=1,
            target_role=target_role,
            career_readiness=0.0,  # Computed upstream
            capabilities=[],
            navigator_plan=[]
        )
        
        job_snapshot = JobRequirementSnapshot(
            title=target_role, 
            company_name="Target Company",
            required_skills=required_skills,
            nice_to_have_skills=[],
            description="Role evaluation"
        )
        
        request_obj = EvaluateMatchRequest(
            profile_snapshot=profile_snapshot,
            job_snapshot=job_snapshot,
            relevant_evidence=[]
        )

        # 2. Make the HTTP call to decision-engine
        url = f"{self.decision_engine_url}/api/v1/reasoning/evaluate_match"
        try:
            # Safe conversion of UUIDs and other fields to JSON-safe dict
            payload = json.loads(request_obj.model_dump_json())
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            # 3. Parse and adapt the output
            data = response.json()
            decision_result = DecisionResult(**data)
            
            # The decision result gives overall_readiness (out of 100), missing_capabilities, strengths, explanations.
            # Convert overall_readiness back to a 0.0-1.0 float score.
            overall_score = decision_result.overall_readiness / 100.0
            
            matched_skills = decision_result.strengths
            if not matched_skills:
                # Fallback to simple intersection if Decision Engine returns empty
                twin_skills = [s.get("skill_name") for s in twin.get("skills", [])]
                matched_skills = list(set(required_skills).intersection(set(twin_skills)))
                
            missing_skills = decision_result.missing_capabilities
            if not missing_skills:
                # Fallback
                matched_set = set(matched_skills)
                missing_skills = [s for s in required_skills if s not in matched_set]
                
            explanation = decision_result.explanations[0] if decision_result.explanations else None
            confidence = explanation.confidence if explanation else 0.8
            
            # If the backend returns a trace or explanation, use it
            evidence_used = [explanation.reasoning_trace] if explanation else ["Match evaluated successfully."]

            return ExplainMatchScoreResult(
                overall_score=overall_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                confidence=confidence,
                evidence_used=evidence_used
            )
            
        except Exception as e:
            # If the service call fails (e.g. not running, network issue), we degrade gracefully
            # to a deterministic offline calculation to keep the UI functional
            print(f"Failed to communicate with Decision Engine: {e}")
            
            twin_skills = {s.get("skill_name").lower() for s in twin.get("skills", []) if s.get("skill_name")}
            matched = [s for s in required_skills if s.lower() in twin_skills]
            missing = [s for s in required_skills if s.lower() not in twin_skills]
            score = len(matched) / len(required_skills) if required_skills else 1.0
            
            return ExplainMatchScoreResult(
                overall_score=score,
                matched_skills=matched,
                missing_skills=missing,
                confidence=0.5,
                evidence_used=[f"Offline fallback match: {len(matched)}/{len(required_skills)} skills matched. (Error: {e})"]
            )
