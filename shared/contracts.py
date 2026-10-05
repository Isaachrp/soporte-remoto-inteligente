"""Closed ECMP contracts; no commands or credentials in request parameters."""
import hashlib
import json
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSION = "0.1.0"
GENERATOR = "ECMP-PHP-001/1.0.0"
ADAPTER = "ecmp-native/1"
SPEEDS = {"256k", "512k"} | {f"{n}M" for n in [*range(1, 11), 15, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, *range(250, 1001, 50)]}

def digest(value):
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def normalize(text):
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines()).strip() + "\n"

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Parameters(Strict):
    tipo: Literal["ECMP"]
    lineas: int = Field(ge=2, le=12, strict=True)
    lan: str
    dhcp: bool = Field(strict=True)
    # Retain original velN/gwN/ipN names on the wire.
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_form(self):
        extra = self.__pydantic_extra__
        expected = {f"{key}{i}" for i in range(1, self.lineas+1) for key in ("vel", "gw", "ip")}
        if set(extra) != expected:
            raise ValueError("Se requieren exactamente velN, gwN e ipN para cada linea")
        if not re.fullmatch(r"172\.16\.(0|[1-9][0-9]{0,2})\.1", self.lan) or int(self.lan.split('.')[2]) > 254:
            raise ValueError("LAN fuera del formulario original")
        networks = set()
        for i in range(1, self.lineas+1):
            if not isinstance(extra[f"vel{i}"], str) or extra[f"vel{i}"] not in SPEEDS:
                raise ValueError("Velocidad fuera del formulario original")
            gw, ip = extra[f"gw{i}"], extra[f"ip{i}"]
            if not isinstance(gw, str) or not re.fullmatch(r"192\.168\.(0|[1-9][0-9]{0,2})\.(1|254)", gw) or int(gw.split('.')[2]) > 254:
                raise ValueError("Gateway fuera del formulario original")
            if type(ip) is not int or not 2 <= ip <= 253:
                raise ValueError("IP WAN debe ser octeto entero 2..253")
            subnet = gw.rsplit('.', 1)[0]
            if subnet in networks:
                raise ValueError("Subredes WAN superpuestas")
            networks.add(subnet)
        return self

class Target(Strict):
    router_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    identity: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    management_interface: str = Field(pattern=r"^ether[1-9][0-9]*$")

class Request(Strict):
    text: str = Field(min_length=1, max_length=1000)
    session_id: str
    target: Target
    parameters: Parameters | None = None

class Registration(Strict):
    agent_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    version: Literal[VERSION]
    mode: Literal["simulated", "real"]
    router_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")

class Decision(Strict):
    decision: Literal["approve", "reject"]
    binding_hash: str

class Reconciliation(Strict):
    session_id: str

class Result(Strict):
    status: Literal["ok", "failed", "uncertain"]
    snapshot: dict | None = None
    completed: int = Field(default=0, ge=0)
    error: Literal["tls", "timeout", "connection", "validation", "router_error"] | None = None

# Exact versions are deliberately empty: mocks do not certify RouterOS.
CERTIFIED = frozenset()

def variant(version, mode):
    if mode == "simulated" and version == "6.49.18":
        return "legacy-v6-simulation-only"
    raise ValueError("Version/variante no certificada; escrituras reales bloqueadas")

ACTIONS = {
    "get_ecmp_precheck": {"risk": "read", "timeout": 60, "authorization": "session"},
    "apply_approved_ecmp": {"risk": "write", "timeout": 120, "authorization": "single_use_claim"},
    "verify_ecmp": {"risk": "read", "timeout": 60, "authorization": "session"},
}
