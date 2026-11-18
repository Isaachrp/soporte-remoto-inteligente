import secrets
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict
from shared.contracts import Decision
from server.app.services.central_delivery import CentralDelivery
from server.app.services.catalog_delivery import CatalogDelivery
from pydantic import Field
import json


class Confirmation(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    confirmed: bool
    continue_existing: bool = False


class Selection(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    procedure: str = Field(max_length=32)
    parameters: dict
    confirmed: bool


def central_routes(service):
    delivery = CentralDelivery(service)
    catalog_delivery = CatalogDelivery(service)
    router = APIRouter(prefix='/central')

    def technician(authorization: str = Header(default='')):
        if not authorization.startswith('Bearer ') or not secrets.compare_digest(authorization[7:], service.settings.technician_token):
            raise HTTPException(401, 'No autorizado')

    @router.get('/status', dependencies=[Depends(technician)])
    def status():
        return {'mode': service.settings.mode, 'ai_mode': service.settings.ai_mode,
                'v7_lab_enabled': service.settings.v7_lab_enabled}

    @router.post('/catalog/diagnostics', status_code=201, dependencies=[Depends(technician)])
    def catalog_inspect(body: dict):
        return catalog_delivery.inspect(body)

    @router.post('/catalog/{id}/analyze', dependencies=[Depends(technician)])
    def catalog_analyze(id: str):
        return catalog_delivery.analyze(id)

    @router.get('/catalog/{id}/options', dependencies=[Depends(technician)])
    def catalog_options(id: str, lines: int = 2):
        if not 2 <= lines <= 12:
            raise HTTPException(422, 'Selecciona entre 2 y 12 enlaces.')
        return catalog_delivery.options(catalog_delivery.read(id), lines)

    @router.post('/catalog/{id}/prepare', dependencies=[Depends(technician)])
    def catalog_prepare(id: str, body: Selection):
        return catalog_delivery.prepare_selection(id, body.procedure, body.parameters, body.confirmed)

    @router.post('/catalog/{id}/decision', dependencies=[Depends(technician)])
    def catalog_decide(id: str, body: Decision):
        return catalog_delivery.decide(id, body.decision, body.binding_hash)

    @router.get('/catalog/{id}/package', dependencies=[Depends(technician)])
    def catalog_package(id: str):
        value = catalog_delivery.package(id)
        return Response(json.dumps(value, ensure_ascii=False, indent=2), media_type='application/json', headers={'Cache-Control': 'no-store'})

    @router.get('/catalog/{id}/executable', dependencies=[Depends(technician)])
    def catalog_executable(id: str):
        return FileResponse(catalog_delivery.executable(id), media_type='application/octet-stream',
                            filename='Configuracion-cliente.exe', headers={'Cache-Control': 'no-store'})

    @router.get('/deliveries', dependencies=[Depends(technician)])
    def history():
        return delivery.history()

    @router.post('/diagnostics', status_code=201, dependencies=[Depends(technician)])
    def inspect(body: dict):
        return delivery.inspect(body)

    @router.get('/deliveries/{id}', dependencies=[Depends(technician)])
    def read(id: str):
        return delivery.read(id)

    @router.post('/deliveries/{id}/prepare', dependencies=[Depends(technician)])
    def prepare(id: str, body: Confirmation):
        return delivery.prepare(id, body.confirmed, body.continue_existing)

    @router.post('/deliveries/{id}/decision', dependencies=[Depends(technician)])
    def decision(id: str, body: Decision):
        return delivery.decide(id, body.decision, body.binding_hash)

    @router.get('/deliveries/{id}/package', dependencies=[Depends(technician)])
    def package(id: str):
        value = delivery.package(id)
        return Response(json.dumps(value, ensure_ascii=False, indent=2) + '\n', media_type='application/json',
                        headers={'Content-Disposition': f'attachment; filename="ECMP-{value["id"]}.json"', 'Cache-Control': 'no-store'})

    @router.get('/deliveries/{id}/executable', dependencies=[Depends(technician)])
    def executable(id: str):
        return FileResponse(delivery.executable(id), media_type='application/octet-stream',
                            filename='ECMP-cliente.exe', headers={'Cache-Control': 'no-store'})

    return router
