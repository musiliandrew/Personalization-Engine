from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from services.mission_control import MissionControlService
from services.company_intelligence import CompanyIntelligenceService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/mission-control/{user_id}")
async def get_mission_control(user_id: str):
    """
    Returns the unified Mission Control payload for the frontend.
    """
    try:
        # Run synchronous Django ORM operations in a threadpool to prevent blocking the event loop
        response = await run_in_threadpool(MissionControlService.build, user_id)
        if "error" in response:
            raise HTTPException(status_code=404, detail=response["error"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/company-intelligence/{user_id}/{company_id}")
async def get_company_intelligence(user_id: str, company_id: str):
    """
    Returns the dynamic Company Intelligence Roadmap.
    """
    try:
        response = await run_in_threadpool(CompanyIntelligenceService.build, user_id, company_id)
        if "error" in response:
            raise HTTPException(status_code=404, detail=response["error"])
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommended-jobs/{user_id}")
async def get_recommended_jobs(user_id: str, q: str = ""):
    """
    Returns semantically recommended jobs using Vertex AI Vector Search.
    """
    from services.vertex_search import embed_text, find_neighbors
    from Oauth.models import Profile
    
    try:
        def fetch_skills():
            try:
                profile = Profile.objects.get(user_id=user_id)
                skills_qs = profile.skills.all().values_list("skill_name", flat=True)
                return ", ".join(skills_qs)
            except Profile.DoesNotExist:
                return ""
        
        skills_text = await run_in_threadpool(fetch_skills)
        base_text = f"Skills: {skills_text}"
        if q:
            base_text += f"\nQuery: {q}"
            
        vector = embed_text(base_text)
        results = find_neighbors(vector, top_k=20)
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
