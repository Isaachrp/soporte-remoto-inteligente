import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import ValidationError
from server.app.core.config import Settings
from server.app.services.operations import Operations
from server.app.api.routes import routes

def create_app(settings=None, **dependencies):
    service = Operations(settings or Settings.from_env(), **dependencies)
    @asynccontextmanager
    async def lifespan(app):
        service.sweep()
        async def reap():
            while True:
                await asyncio.sleep(5)
                await asyncio.to_thread(service.sweep)
        task = asyncio.create_task(reap())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
    app = FastAPI(title='ECMP supervisado',version='0.1.0',lifespan=lifespan)
    app.state.service = service
    app.include_router(routes(service))
    @app.get('/',include_in_schema=False)
    def technician_interface():
        return FileResponse(Path(__file__).with_name('ui.html'))
    @app.get('/ui-assets/{name}', include_in_schema=False)
    def technician_asset(name: str):
        if name not in {'logo_b.png', 'modem.gif', 'mikrotik.jpg', 'clientes.jpg'}:
            return JSONResponse(status_code=404, content={'detail': 'Imagen no encontrada'})
        return FileResponse(Path(__file__).resolve().parents[2] / 'php' / 'sistema-generador' / name)
    async def invalid(request, exc):
        return JSONResponse(status_code=422,content={'detail':'Datos invalidos; revise el esquema. No incluya secretos.'})
    app.add_exception_handler(RequestValidationError,invalid)
    app.add_exception_handler(ValidationError,invalid)
    @app.middleware('http')
    async def transport(request, call_next):
        # Bind to loopback for development. Remote deployment requires ASGI TLS.
        if request.url.scheme != 'https' and request.client and request.client.host not in ('127.0.0.1','::1','testclient'):
            return JSONResponse(status_code=403,content={'detail':'HTTPS requerido'})
        if int(request.headers.get('content-length','0')) > 1000000:
            return JSONResponse(status_code=413,content={'detail':'Solicitud excesiva'})
        return await call_next(request)
    return app
