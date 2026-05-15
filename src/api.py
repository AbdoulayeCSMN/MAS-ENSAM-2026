"""FastAPI server exposing the orchestrator workflow as an HTTP API."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from graph.state import AgentState, ScanTarget
from graph.workflow import build_workflow

app = FastAPI(title="Multi-Agent Security API", version="0.1.0")

_workflow = build_workflow()
_reports: dict[str, dict] = {}  # in-memory store (will be replaced with Redis in prod)


class ScanRequest(BaseModel):
    repoPath: str
    languages: list[str] | None = None
    maxPatchIterations: int = 3


class ApplyPatchesRequest(BaseModel):
    vuln_ids: list[str]


@app.post("/scan")
async def scan(req: ScanRequest) -> dict:
    repo = Path(req.repoPath)
    if not repo.exists():
        raise HTTPException(status_code=400, detail=f"Path not found: {req.repoPath}")

    scan_id = str(uuid.uuid4())
    initial_state = AgentState(
        repo_root=str(repo.resolve()),
        scan_id=scan_id,
        max_patch_iterations=req.maxPatchIterations,
    )

    final_state: AgentState = _workflow.invoke(initial_state)
    _reports[scan_id] = final_state.report

    return final_state.report


@app.get("/reports/{scan_id}")
async def get_report(scan_id: str) -> dict:
    report = _reports.get(scan_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.post("/reports/{scan_id}/apply")
async def apply_patches(scan_id: str, req: ApplyPatchesRequest) -> dict:
    report = _reports.get(scan_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    applied = []
    for vuln in report.get("vulnerabilities", []):
        if vuln["id"] in req.vuln_ids and vuln.get("patch_diff"):
            # In a real system, apply the patch to disk here
            vuln["patch_applied"] = True
            applied.append(vuln["id"])

    return {"applied": applied}
