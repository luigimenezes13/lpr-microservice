from fastapi import APIRouter

from vehicle.application.process_capture_cycle import ProcessCaptureCycle


def build_router(process_capture_cycle: ProcessCaptureCycle) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def healthcheck():
        return {"status": "ok", "service": "vehicle"}

    @router.post("/vehicle/capture-cycle")
    def run_single_capture_cycle():
        process_capture_cycle.execute()
        return {"status": "ok", "action": "capture_cycle_executed"}

    return router
