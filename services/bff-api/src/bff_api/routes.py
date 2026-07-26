"""Domain route surface for the NovaSteel BFF v1 contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import Body, Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .auth import (
    READER_ROLES,
    UserContext,
    current_user,
    require_any_role,
    require_reader,
    require_site,
)
from .capacity import CapacityError, CapacityUpstreamError
from .contracts import ErrorCode, utc_now
from .errors import ApiError
from .idempotency import IdempotencyStore
from .services import OptimizationError, ScoringError
from .table import apply_table_query

from scoring_worker.metrics import record_quality_metrics  # noqa: E402


def register_routes(app: FastAPI) -> None:
    """Register the complete BFF domain surface against one app-local service graph."""

    @app.get("/v1/me", tags=["Bootstrap"])
    async def current_identity(
        request: Request, user: UserContext = Depends(current_user)
    ) -> dict[str, Any]:
        return _envelope(
            request,
            {
                "userId": user.user_id,
                "displayName": user.display_name,
                "roles": sorted(user.roles),
                "plantScope": sorted(user.plant_scope),
                "personas": user.personas,
                "locale": user.locale,
                "permittedActions": user.permitted_actions,
            },
        )

    @app.get("/v1/command-center/summary", tags=["CommandCenter"])
    async def command_center_summary(
        request: Request,
        site: str = "all",
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        selected_site = _requested_site(request, user, site)
        return _envelope(
            request, request.app.state.services.repository.command_summary(selected_site)
        )

    @app.get("/v1/dashboard/kpis", tags=["CommandCenter"])
    async def dashboard_kpis(
        request: Request,
        site: str = "all",
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        selected_site = _requested_site(request, user, site)
        summary = request.app.state.services.repository.command_summary(selected_site)
        return _envelope(
            request,
            {
                "site": selected_site,
                "kpis": summary["kpis"],
                "freshness": summary["freshness"],
                "syntheticBanner": summary["syntheticBanner"],
            },
        )

    @app.get("/v1/realtime/alerts", tags=["Realtime"])
    async def stream_alerts(
        request: Request, user: UserContext = Depends(current_user)
    ) -> StreamingResponse:
        require_reader(user)
        last_event_id = request.headers.get("Last-Event-ID")
        stream = request.app.state.services.events.stream(last_event_id)
        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "X-Correlation-ID": _correlation_id(request),
            },
        )

    @app.get("/v1/realtime/alerts:poll", tags=["Realtime"])
    async def poll_alerts(
        request: Request,
        since: str | None = None,
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        events = request.app.state.services.events.after(since)
        permitted = [
            event.as_poll_item()
            for event in events
            if event.data.get("site") in user.plant_scope
            or event.data.get("site") is None
        ]
        return {
            "events": permitted,
            "asOf": _as_of(),
            "stale": False,
            "correlationId": _correlation_id(request),
        }

    @app.get("/v1/telemetry", tags=["CommandCenter"])
    async def list_telemetry(
        request: Request,
        site: str = "all",
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        rows = _site_rows(
            user, request.app.state.services.repository.telemetry_rows(), site
        )
        return _table_envelope(
            request,
            rows,
            columns={
                "eventId": "text",
                "eventTs": "date",
                "site": "enum",
                "assetId": "text",
                "sensorId": "text",
                "signalCode": "text",
                "value": "number",
                "unit": "enum",
                "quality": "enum",
                "scenarioId": "text",
            },
            default_sort=("eventTs:desc", "eventId:desc"),
            primary_time="eventTs",
        )

    @app.get("/v1/furnaces", tags=["Furnace"])
    async def list_furnaces(
        request: Request,
        site: str = "all",
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(
            user,
            "MaintenanceEngineer.Read",
            "Operator.Read",
            "ProcessEngineer.Contribute",
        )
        rows = _site_rows(user, request.app.state.services.repository.furnaces(), site)
        return _table_envelope(
            request,
            rows,
            columns={
                "assetId": "text",
                "site": "enum",
                "assetType": "enum",
                "componentId": "text",
                "health": "enum",
            },
            default_sort=("assetId:asc",),
            primary_time="assetId",
        )

    @app.get("/v1/furnaces/{asset_id}/telemetry", tags=["Furnace"])
    async def furnace_telemetry(
        asset_id: str,
        request: Request,
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(
            user,
            "MaintenanceEngineer.Read",
            "Operator.Read",
            "ProcessEngineer.Contribute",
        )
        _asset_access(request, user, asset_id)
        rows = [
            row
            for row in request.app.state.services.repository.telemetry_rows()
            if row["assetId"] == asset_id
        ]
        return _table_envelope(
            request,
            rows,
            columns={
                "eventId": "text",
                "eventTs": "date",
                "site": "enum",
                "assetId": "text",
                "sensorId": "text",
                "signalCode": "text",
                "value": "number",
                "unit": "enum",
                "quality": "enum",
            },
            default_sort=("eventTs:desc",),
            primary_time="eventTs",
        )

    @app.get("/v1/furnaces/{asset_id}/lining-forecast", tags=["Furnace"])
    async def lining_forecast(
        asset_id: str,
        request: Request,
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(user, "MaintenanceEngineer.Read", "Operator.Read")
        _asset_access(request, user, asset_id)
        try:
            forecast = request.app.state.services.lining_forecast(
                asset_id=asset_id, correlation_id=_correlation_id(request)
            )
        except ScoringError as exc:
            raise ApiError(404, ErrorCode.NOT_FOUND, "No lining forecast is available.") from exc
        return _envelope(request, forecast)

    @app.get("/v1/energy/intervals", tags=["Energy"])
    async def list_energy_intervals(
        request: Request,
        site: str = "all",
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(user, "EnergyPlanner.Approve")
        rows = _site_rows(user, request.app.state.services.repository.energy_rows(), site)
        return _table_envelope(
            request,
            rows,
            columns={
                "eventId": "text",
                "eventTs": "date",
                "site": "enum",
                "assetId": "text",
                "intervalStart": "date",
                "priceEurMwh": "number",
                "demandMw": "number",
                "baselineDemandMw": "number",
                "consumptionMwh": "number",
                "carbonIntensityKgCo2eMwh": "number",
                "meterId": "text",
                "scenario": "text",
            },
            default_sort=("intervalStart:desc",),
            primary_time="intervalStart",
        )

    @app.post("/v1/energy/schedules:simulate", tags=["Energy"])
    async def simulate_energy(
        request: Request,
        body: dict[str, Any] = Body(...),
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(user, "EnergyPlanner.Approve")
        _require_exact_keys(body, {"site", "horizonHours", "scenario", "constraints"})
        site = _required_string(body, "site")
        require_site(user, site)
        constraints = body["constraints"]
        if not isinstance(constraints, Mapping):
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, "constraints must be an object.")
        try:
            result = request.app.state.services.simulate_energy(
                site=site,
                horizon_hours=int(body["horizonHours"]),
                scenario=_required_string(body, "scenario"),
                constraints=constraints,
                correlation_id=_correlation_id(request),
                actor=user.user_id,
            )
        except (OptimizationError, ValueError) as exc:
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, str(exc)) from exc
        return _envelope(request, result)

    @app.get("/v1/energy/recommendations", tags=["Energy"])
    async def list_energy_recommendations(
        request: Request,
        site: str = "all",
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(user, "EnergyPlanner.Approve")
        selected_site = _requested_site(request, user, site)
        rows = request.app.state.services.list_recommendations(selected_site)
        return _table_envelope(
            request,
            rows,
            columns={
                "recommendationId": "text",
                "site": "enum",
                "scenario": "text",
                "status": "enum",
                "version": "number",
                "modelVersion": "text",
            },
            default_sort=("recommendationId:asc",),
            primary_time="recommendationId",
        )

    @app.post("/v1/energy/recommendations/{recommendation_id}:approve", tags=["Energy"])
    async def approve_energy_recommendation(
        recommendation_id: str,
        request: Request,
        body: dict[str, Any] = Body(...),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        user: UserContext = Depends(current_user),
    ) -> JSONResponse:
        require_any_role(user, "EnergyPlanner.Approve")
        _require_exact_keys(body, {"reason", "approvalContext", "expectedVersion"})
        _required_string(body, "reason")
        if not isinstance(body["approvalContext"], Mapping):
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, "approvalContext must be an object.")
        key = IdempotencyStore.require_key(idempotency_key)
        route = "/v1/energy/recommendations/{id}:approve"
        replay = request.app.state.services.idempotency.replay_or_none(
            route=route, key=key, body=body
        )
        if replay:
            return _replay_response(replay)
        recommendation = request.app.state.services.energy_recommendation(recommendation_id)
        if recommendation is None:
            raise ApiError(404, ErrorCode.NOT_FOUND, "Recommendation was not found.")
        require_site(user, str(recommendation["site"]))
        _check_expected_version(recommendation, body["expectedVersion"])
        if recommendation["status"] != "PENDING_APPROVAL":
            raise ApiError(
                409, ErrorCode.DUPLICATE_APPROVAL, "Recommendation already has a terminal decision."
            )
        recommendation["status"] = "SIMULATED_APPROVED"
        recommendation["version"] += 1
        record = request.app.state.services.audit.append(
            domain="energy",
            entity_id=recommendation_id,
            correlation_id=_correlation_id(request),
            action="energy.approve",
            actor=user.user_id,
            input_snapshot_ref=f"recommendation:{recommendation_id}",
            model_version=recommendation.get("modelVersion"),
            output={"status": recommendation["status"]},
            human_action={"decision": "SIMULATED_APPROVED", "reason": body["reason"]},
        )
        recommendation["approvalAuditRef"] = record.audit_id
        request.app.state.services.recommendations[recommendation_id] = recommendation
        response = _envelope(request, recommendation)
        request.app.state.services.idempotency.store(
            route=route, key=key, body=body, status_code=200, response=response
        )
        return JSONResponse(response)

    @app.post("/v1/energy/recommendations/{recommendation_id}:reject", tags=["Energy"])
    async def reject_energy_recommendation(
        recommendation_id: str,
        request: Request,
        body: dict[str, Any] = Body(...),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        user: UserContext = Depends(current_user),
    ) -> JSONResponse:
        require_any_role(user, "EnergyPlanner.Approve")
        allowed = {"reasonCode", "reasonNote", "expectedVersion"}
        _require_keys(body, {"reasonCode", "expectedVersion"}, allowed)
        if body["reasonCode"] not in {
            "PRODUCTION_CONFLICT",
            "RISK_TOO_HIGH",
            "DATA_QUALITY_CONCERN",
            "OTHER",
        }:
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, "reasonCode is invalid.")
        if body["reasonCode"] == "OTHER":
            _required_string(body, "reasonNote")
        key = IdempotencyStore.require_key(idempotency_key)
        route = "/v1/energy/recommendations/{id}:reject"
        replay = request.app.state.services.idempotency.replay_or_none(
            route=route, key=key, body=body
        )
        if replay:
            return _replay_response(replay)
        recommendation = request.app.state.services.energy_recommendation(recommendation_id)
        if recommendation is None:
            raise ApiError(404, ErrorCode.NOT_FOUND, "Recommendation was not found.")
        require_site(user, str(recommendation["site"]))
        _check_expected_version(recommendation, body["expectedVersion"])
        if recommendation["status"] != "PENDING_APPROVAL":
            raise ApiError(
                409, ErrorCode.DUPLICATE_APPROVAL, "Recommendation already has a terminal decision."
            )
        recommendation["status"] = "REJECTED"
        recommendation["version"] += 1
        record = request.app.state.services.audit.append(
            domain="energy",
            entity_id=recommendation_id,
            correlation_id=_correlation_id(request),
            action="energy.reject",
            actor=user.user_id,
            input_snapshot_ref=f"recommendation:{recommendation_id}",
            model_version=recommendation.get("modelVersion"),
            output={"status": "REJECTED"},
            human_action={"decision": "REJECTED", "reasonCode": body["reasonCode"]},
        )
        recommendation["approvalAuditRef"] = record.audit_id
        request.app.state.services.recommendations[recommendation_id] = recommendation
        response = _envelope(request, recommendation)
        request.app.state.services.idempotency.store(
            route=route, key=key, body=body, status_code=200, response=response
        )
        return JSONResponse(response)

    @app.get("/v1/quality/batches", tags=["Quality"])
    async def list_quality_batches(
        request: Request,
        site: str = "all",
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(user, "ProcessEngineer.Contribute")
        rows = _site_rows(user, request.app.state.services.repository.quality_rows(), site)
        return _table_envelope(
            request,
            rows,
            columns={
                "batchId": "text",
                "site": "enum",
                "assetId": "text",
                "heatId": "text",
                "grade": "enum",
                "sampleId": "text",
                "characteristic": "enum",
                "value": "number",
                "resultStatus": "enum",
                "carbonEquivalent": "number",
                "coilingTempBiasC": "number",
                "riskScore": "number",
                "eventTs": "date",
            },
            default_sort=("eventTs:desc", "batchId:asc"),
            primary_time="eventTs",
        )

    @app.get("/v1/quality/batches/{batch_id}/genealogy", tags=["Quality"])
    async def quality_genealogy(
        batch_id: str,
        request: Request,
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(user, "ProcessEngineer.Contribute")
        result = request.app.state.services.repository.genealogy(batch_id)
        if result is None:
            raise ApiError(404, ErrorCode.NOT_FOUND, "Batch was not found.")
        require_site(user, str(result["site"]))
        return _envelope(request, result)

    @app.post("/v1/quality/what-if", tags=["Quality"])
    async def quality_what_if(
        request: Request,
        body: dict[str, Any] = Body(...),
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(user, "ProcessEngineer.Contribute")
        _require_exact_keys(body, {"batchId", "adjustments"})
        batch = request.app.state.services.repository.quality_batch(
            _required_string(body, "batchId")
        )
        if batch is None:
            raise ApiError(404, ErrorCode.NOT_FOUND, "Batch was not found.")
        require_site(user, str(batch["site"]))
        adjustments = body["adjustments"]
        if not isinstance(adjustments, Mapping):
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, "adjustments must be an object.")
        try:
            result = request.app.state.services.scorer.quality_what_if(
                batch=batch,
                adjustments={name: float(value) for name, value in adjustments.items()},
            )
        except (ScoringError, ValueError) as exc:
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, str(exc)) from exc
        # Emit quality yield metric (side-effect free, no-op offline)
        record_quality_metrics(result)
        record = request.app.state.services.audit.append(
            domain="quality",
            entity_id=batch["batchId"],
            correlation_id=_correlation_id(request),
            action="quality.what_if",
            actor=user.user_id,
            input_snapshot_ref=batch["sourceRef"],
            model_version=result["modelVersion"],
            output={"value": result["value"], "unit": result["unit"]},
        )
        result["auditRef"] = record.audit_id
        return _envelope(request, result)

    @app.get("/v1/sustainability/summary", tags=["CommandCenter"])
    async def sustainability_summary(
        request: Request,
        site: str = "all",
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        selected_site = _requested_site(request, user, site)
        return _envelope(
            request,
            request.app.state.services.repository.sustainability_summary(selected_site),
        )

    @app.get("/v1/sustainability/emissions", tags=["CommandCenter"])
    async def sustainability_emissions(
        request: Request,
        site: str = "all",
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        rows = _site_rows(
            user, request.app.state.services.repository.emissions_rows(), site
        )
        return _table_envelope(
            request,
            rows,
            columns={
                "site": "enum",
                "eventTs": "date",
                "scope2KgCo2e": "number",
                "consumptionMwh": "number",
                "carbonIntensityKgCo2eMwh": "number",
            },
            default_sort=("eventTs:desc",),
            primary_time="eventTs",
        )

    @app.post("/v1/knowledge/interviews", tags=["Knowledge"], status_code=201)
    async def create_knowledge_interview(
        request: Request,
        body: dict[str, Any] = Body(...),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        user: UserContext = Depends(current_user),
    ) -> JSONResponse:
        require_any_role(user, "Knowledge.Publisher")
        _require_exact_keys(body, {"operatorRef", "language", "consent"})
        consent = body["consent"]
        if not isinstance(consent, Mapping):
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, "consent must be an object.")
        if (
            consent.get("granted") is not True
            or consent.get("scope") != "knowledge-capture"
            or not isinstance(consent.get("retentionDays"), int)
            or consent["retentionDays"] < 1
        ):
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, "Recorded knowledge-capture consent is required.")
        key = IdempotencyStore.require_key(idempotency_key)
        route = "/v1/knowledge/interviews"
        replay = request.app.state.services.idempotency.replay_or_none(
            route=route, key=key, body=body
        )
        if replay:
            return _replay_response(replay)
        result = request.app.state.services.knowledge.create_interview(
            operator_ref=_required_string(body, "operatorRef"),
            language=_required_string(body, "language"),
            retention_days=consent["retentionDays"],
            correlation_id=_correlation_id(request),
        )
        record = request.app.state.services.audit.append(
            domain="knowledge",
            entity_id=result["sessionId"],
            correlation_id=_correlation_id(request),
            action="knowledge.interview.create",
            actor=user.user_id,
            input_snapshot_ref="consent:knowledge-capture",
            output={"consentState": result["consentState"]},
        )
        result["auditRef"] = record.audit_id
        response = _envelope(request, result)
        request.app.state.services.idempotency.store(
            route=route, key=key, body=body, status_code=201, response=response
        )
        return JSONResponse(response, status_code=201)

    @app.get("/v1/knowledge/interviews/{session_id}/transcript", tags=["Knowledge"])
    async def knowledge_transcript(
        session_id: str,
        request: Request,
        user: UserContext = Depends(current_user),
    ) -> JSONResponse:
        require_any_role(user, "Knowledge.Publisher")
        result = request.app.state.services.knowledge.transcript(session_id)
        status = 202 if result.get("status") == "PROCESSING" else 200
        return JSONResponse(_envelope(request, result), status_code=status)

    @app.get("/v1/knowledge/procedures", tags=["Knowledge"])
    async def list_knowledge_procedures(
        request: Request,
        status: str | None = None,
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        if status and status not in {"DRAFT", "IN_REVIEW", "APPROVED", "REJECTED"}:
            raise ApiError(400, ErrorCode.VALIDATION_ERROR, "status is invalid.")
        all_rows = request.app.state.services.knowledge.list_procedures(
            status=status, q=None, page=1, size=200
        )["items"]
        return _table_envelope(
            request,
            all_rows,
            columns={
                "procedureId": "text",
                "title": "text",
                "status": "enum",
                "version": "number",
                "sessionId": "text",
                "observation": "text",
            },
            default_sort=("title:asc",),
            primary_time="procedureId",
        )

    @app.post("/v1/knowledge/procedures/{procedure_id}:approve", tags=["Knowledge"])
    async def approve_knowledge_procedure(
        procedure_id: str,
        request: Request,
        body: dict[str, Any] = Body(...),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        user: UserContext = Depends(current_user),
    ) -> JSONResponse:
        require_any_role(user, "Knowledge.Publisher")
        _require_exact_keys(body, {"expectedVersion"})
        key = IdempotencyStore.require_key(idempotency_key)
        route = "/v1/knowledge/procedures/{id}:approve"
        replay = request.app.state.services.idempotency.replay_or_none(
            route=route, key=key, body=body
        )
        if replay:
            return _replay_response(replay)
        result = request.app.state.services.knowledge.approve(
            procedure_id=procedure_id,
            actor=user.user_id,
            roles=set(user.roles),
            expected_version=_required_int(body, "expectedVersion"),
            idempotency_key=key,
            correlation_id=_correlation_id(request),
        )
        record = request.app.state.services.audit.append(
            domain="knowledge",
            entity_id=procedure_id,
            correlation_id=_correlation_id(request),
            action="knowledge.procedure.approve",
            actor=user.user_id,
            input_snapshot_ref=f"procedure:{procedure_id}",
            output={"status": result["status"], "version": result["version"]},
            human_action={"decision": "APPROVED"},
        )
        result["auditRef"] = record.audit_id
        response = _envelope(request, result)
        request.app.state.services.idempotency.store(
            route=route, key=key, body=body, status_code=200, response=response
        )
        return JSONResponse(response)

    @app.get("/v1/knowledge/search", tags=["Knowledge"])
    async def search_knowledge(
        request: Request,
        q: str = Query(default="", min_length=0),
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        result = request.app.state.services.knowledge.search(q)
        return _table_envelope(
            request,
            result["items"],
            columns={
                "procedureId": "text",
                "title": "text",
                "status": "enum",
                "version": "number",
                "observation": "text",
            },
            default_sort=("title:asc",),
            primary_time="procedureId",
        )

    @app.get("/v1/audit/decisions", tags=["Audit"])
    async def list_audit_decisions(
        request: Request,
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        domain = request.query_params.get("domain")
        _assert_audit_access(user, domain)
        rows = request.app.state.services.audit.query(
            domain=domain, entity_id=request.query_params.get("entityId")
        )
        return _table_envelope(
            request,
            rows,
            columns={
                "auditId": "text",
                "domain": "enum",
                "entityId": "text",
                "correlationId": "text",
                "action": "text",
                "actor": "text",
                "modelVersion": "text",
                "recordedAt": "date",
            },
            default_sort=("recordedAt:desc",),
            primary_time="recordedAt",
        )

    @app.get("/v1/platform/capacity", tags=["Platform"])
    async def capacity_status(
        request: Request, user: UserContext = Depends(current_user)
    ) -> dict[str, Any]:
        require_reader(user)
        return _envelope(request, request.app.state.services.capacity.status())

    @app.post("/v1/platform/capacity/start-requests", tags=["Platform"])
    async def start_capacity(
        request: Request,
        body: dict[str, Any] = Body(...),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        user: UserContext = Depends(current_user),
    ) -> JSONResponse:
        return _capacity_mutation(
            request, body, idempotency_key, user, action="start"
        )

    @app.post("/v1/platform/capacity/pause-requests", tags=["Platform"])
    async def pause_capacity(
        request: Request,
        body: dict[str, Any] = Body(...),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        user: UserContext = Depends(current_user),
    ) -> JSONResponse:
        return _capacity_mutation(
            request, body, idempotency_key, user, action="pause"
        )

    @app.post(
        "/v1/platform/capacity/sku-requests",
        tags=["Platform"],
        operation_id="requestCapacitySkuChange",
    )
    async def scale_capacity(
        request: Request,
        body: dict[str, Any] = Body(...),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        user: UserContext = Depends(current_user),
    ) -> JSONResponse:
        return _capacity_mutation(
            request, body, idempotency_key, user, action="scale"
        )

    @app.get("/v1/platform/capacity/operations/{operation_id}", tags=["Platform"])
    async def capacity_operation(
        operation_id: str,
        request: Request,
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        operation = request.app.state.services.capacity.operation(operation_id)
        if operation is None:
            raise ApiError(404, ErrorCode.NOT_FOUND, "Capacity operation was not found.")
        return _envelope(request, operation)

    @app.post("/v1/workorders", tags=["WorkOrders"], status_code=201)
    async def create_workorder(
        request: Request,
        body: dict[str, Any] = Body(...),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        user: UserContext = Depends(current_user),
    ) -> JSONResponse:
        require_any_role(user, "MaintenanceEngineer.Read")
        _require_exact_keys(body, {"assetId", "title", "reason"})
        asset_id = _required_string(body, "assetId")
        _asset_access(request, user, asset_id)
        key = IdempotencyStore.require_key(idempotency_key)
        route = "/v1/workorders"
        replay = request.app.state.services.idempotency.replay_or_none(
            route=route, key=key, body=body
        )
        if replay:
            return _replay_response(replay)
        result = request.app.state.services.repository.create_workorder(
            asset_id=asset_id,
            title=_required_string(body, "title"),
            reason=_required_string(body, "reason"),
            actor=user.user_id,
        )
        record = request.app.state.services.audit.append(
            domain="furnace",
            entity_id=result["workOrderId"],
            correlation_id=_correlation_id(request),
            action="workorder.create",
            actor=user.user_id,
            input_snapshot_ref=f"asset:{asset_id}",
            output={"status": result["status"]},
            human_action={"decision": "CREATE_SYNTHETIC_WORK_ORDER"},
        )
        result["auditRef"] = record.audit_id
        request.app.state.services.events.publish(
            "alert.updated",
            {
                "alertId": next(
                    iter(request.app.state.services.repository.alerts), "unknown-alert"
                ),
                "status": "WORK_ORDER_LINKED",
                "workOrderId": result["workOrderId"],
                "site": result["site"],
                "correlationId": _correlation_id(request),
            },
        )
        response = _envelope(request, result)
        request.app.state.services.idempotency.store(
            route=route, key=key, body=body, status_code=201, response=response
        )
        return JSONResponse(response, status_code=201)

    @app.get("/v1/workorders/{work_order_id}", tags=["WorkOrders"])
    async def get_workorder(
        work_order_id: str,
        request: Request,
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_any_role(user, "MaintenanceEngineer.Read", "Operator.Read")
        result = request.app.state.services.repository.workorder(work_order_id)
        if result is None:
            raise ApiError(404, ErrorCode.NOT_FOUND, "Work order was not found.")
        require_site(user, str(result["site"]))
        return _envelope(request, result)

    @app.get("/v1/search", tags=["Bootstrap"])
    async def global_search(
        request: Request,
        q: str = Query(..., min_length=1),
        types: str | None = None,
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        accepted_types = {
            item.strip()
            for item in (types or "alert,furnace-unit,batch,procedure,workorder").split(",")
            if item.strip()
        }
        needle = q.lower()
        repository = request.app.state.services.repository
        groups: dict[str, list[dict[str, Any]]] = {}
        if "alert" in accepted_types:
            groups["alert"] = [
                item
                for item in repository.alerts_rows()
                if item["site"] in user.plant_scope
                and needle in str(item).lower()
            ]
        if "furnace-unit" in accepted_types:
            groups["furnace-unit"] = [
                item
                for item in repository.furnaces()
                if item["site"] in user.plant_scope and needle in str(item).lower()
            ]
        if "batch" in accepted_types:
            groups["batch"] = [
                item
                for item in repository.quality_rows()
                if item["site"] in user.plant_scope and needle in str(item).lower()
            ]
        if "procedure" in accepted_types:
            groups["procedure"] = request.app.state.services.knowledge.search(q)["items"]
        if "workorder" in accepted_types:
            groups["workorder"] = [
                item
                for item in repository.workorders.values()
                if item["site"] in user.plant_scope and needle in str(item).lower()
            ]
        return _envelope(
            request,
            {
                "groups": [
                    {"type": name, "items": items, "total": len(items)}
                    for name, items in groups.items()
                ]
            },
        )


def _capacity_mutation(
    request: Request,
    body: dict[str, Any],
    idempotency_key: str | None,
    user: UserContext,
    *,
    action: str,
) -> JSONResponse:
    require_any_role(user, "Platform.Capacity.Manage")
    if action == "scale":
        _require_exact_keys(body, {"capacityId", "sku", "reason"})
    else:
        _require_exact_keys(body, {"capacityId", "reason"})
    capacity_id = _required_string(body, "capacityId")
    services = request.app.state.services
    if capacity_id not in services.settings.capacity_allowlist:
        raise ApiError(
            403, ErrorCode.POLICY_DENIED, "The requested capacity is not allow-listed."
        )
    sku = ""
    if action == "scale":
        sku = _required_string(body, "sku")
        permitted_skus = services.settings.capacity_sku_allowlist
        if sku not in permitted_skus:
            permitted = ", ".join(permitted_skus)
            raise ApiError(
                422,
                ErrorCode.VALIDATION_ERROR,
                f"Fabric capacity SKU must be one of {permitted}.",
            )
    key = IdempotencyStore.require_key(idempotency_key)
    route = (
        "/v1/platform/capacity/sku-requests"
        if action == "scale"
        else f"/v1/platform/capacity/{action}-requests"
    )
    replay = services.idempotency.replay_or_none(route=route, key=key, body=body)
    if replay:
        return _replay_response(replay)
    try:
        if action == "start":
            result, transitions = services.capacity.start(
                reason=_required_string(body, "reason"), actor=user.user_id
            )
        elif action == "pause":
            result, transitions = services.capacity.pause(
                reason=_required_string(body, "reason"), actor=user.user_id
            )
        else:
            result, transitions = services.capacity.scale(
                sku=sku,
                reason=_required_string(body, "reason"),
                actor=user.user_id,
            )
    except CapacityError as exc:
        raise ApiError(409, ErrorCode.CAPACITY_STATE_CONFLICT, str(exc)) from exc
    except CapacityUpstreamError as exc:
        raise ApiError(503, ErrorCode.UPSTREAM_UNAVAILABLE, str(exc), retryable=True) from exc
    record = services.audit.append(
        domain="capacity",
        entity_id=capacity_id,
        correlation_id=_correlation_id(request),
        action=f"capacity.{action}",
        actor=user.user_id,
        input_snapshot_ref=f"capacity:{capacity_id}",
        output=result,
        human_action={"reason": body["reason"], "decision": result["status"]},
    )
    result["auditRef"] = record.audit_id
    for transition in transitions:
        services.events.publish(
            "capacity.transition",
            transition | {"correlationId": _correlation_id(request)},
        )
    response = _envelope(request, result)
    services.idempotency.store(
        route=route, key=key, body=body, status_code=200, response=response
    )
    return JSONResponse(response)


def _envelope(request: Request, data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "data": dict(data),
        "asOf": _as_of(),
        "correlationId": _correlation_id(request),
    }


def _replay_response(replay: Any) -> JSONResponse:
    """Keep an idempotent response's stored correlation snapshot header-aligned."""
    correlation_id = str(replay.body.get("correlationId", ""))
    headers = {"X-Correlation-ID": correlation_id} if correlation_id else None
    return JSONResponse(replay.body, status_code=replay.status_code, headers=headers)


def _table_envelope(
    request: Request,
    rows: list[dict[str, Any]],
    *,
    columns: Mapping[str, str],
    default_sort: tuple[str, ...],
    primary_time: str,
) -> dict[str, Any]:
    items, total, page, size = apply_table_query(
        request=request,
        rows=rows,
        columns=columns,
        default_sort=default_sort,
        primary_time=primary_time,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "asOf": _as_of(),
        "correlationId": _correlation_id(request),
    }


def _as_of() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def _correlation_id(request: Request) -> str:
    return str(request.state.correlation_id)


def _requested_site(request: Request, user: UserContext, site: str) -> str:
    if site == "all":
        # The single local fixture is only returned after scope filtering.
        if request.app.state.services.repository.site not in user.plant_scope:
            raise ApiError(
                403, ErrorCode.FORBIDDEN_SCOPE, "You do not have access to the requested plant."
            )
        return request.app.state.services.repository.site
    require_site(user, site)
    return site


def _site_rows(
    user: UserContext, rows: list[dict[str, Any]], site: str
) -> list[dict[str, Any]]:
    if site != "all":
        require_site(user, site)
    return [
        row
        for row in rows
        if row.get("site") in user.plant_scope
        and (site == "all" or row.get("site") == site)
    ]


def _asset_access(request: Request, user: UserContext, asset_id: str) -> None:
    site = request.app.state.services.repository.asset_site(asset_id)
    if site is None:
        raise ApiError(404, ErrorCode.NOT_FOUND, "Asset was not found.")
    require_site(user, site)


def _require_exact_keys(body: Mapping[str, Any], required: set[str]) -> None:
    _require_keys(body, required, required)


def _require_keys(
    body: Mapping[str, Any], required: set[str], allowed: set[str]
) -> None:
    unknown = set(body) - allowed
    missing = required - set(body)
    if unknown:
        raise ApiError(
            400, ErrorCode.VALIDATION_ERROR, f"Unexpected request field '{sorted(unknown)[0]}'."
        )
    if missing:
        raise ApiError(
            400, ErrorCode.VALIDATION_ERROR, f"Missing request field '{sorted(missing)[0]}'."
        )


def _required_string(body: Mapping[str, Any], name: str) -> str:
    value = body.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ApiError(400, ErrorCode.VALIDATION_ERROR, f"{name} must be a non-empty string.")
    return value.strip()


def _required_int(body: Mapping[str, Any], name: str) -> int:
    value = body.get(name)
    if not isinstance(value, int) or value < 1:
        raise ApiError(400, ErrorCode.VALIDATION_ERROR, f"{name} must be a positive integer.")
    return value


def _check_expected_version(item: Mapping[str, Any], expected: Any) -> None:
    if not isinstance(expected, int) or expected != item.get("version"):
        raise ApiError(
            409,
            ErrorCode.STALE_APPROVAL,
            "The recommendation version is stale.",
        )


def _assert_audit_access(user: UserContext, domain: str | None) -> None:
    if "Compliance.Auditor" in user.roles:
        return
    role_by_domain = {
        "energy": "EnergyPlanner.Approve",
        "quality": "ProcessEngineer.Contribute",
        "furnace": "MaintenanceEngineer.Read",
        "knowledge": "Knowledge.Publisher",
        "capacity": "Platform.Capacity.Manage",
    }
    required = role_by_domain.get(domain or "")
    if required is None or required not in user.roles:
        raise ApiError(403, ErrorCode.FORBIDDEN_ROLE, "Audit access is not permitted.")
