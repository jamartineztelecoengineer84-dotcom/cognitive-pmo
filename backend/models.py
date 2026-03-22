from pydantic import BaseModel
from typing import Optional
from datetime import date


class ProyectoCreate(BaseModel):
    nombre: str
    prioridad: str
    prioridad_num: int
    estado: str
    horas_estimadas: int
    skill_requerida: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class IncidenciaCreate(BaseModel):
    descripcion: str
    prioridad: str
    categoria: str
    sla_limite: Optional[str] = None
    tecnico_asignado: Optional[str] = None
    flag_build_vs_run: Optional[bool] = False
    impacto_negocio: Optional[str] = None


class AsignarTecnico(BaseModel):
    id_tecnico: str
    estado: Optional[str] = "OCUPADO"
    carga_actual: Optional[int] = 0


class BufferUpdate(BaseModel):
    id_proyecto: str


class KanbanTareaCreate(BaseModel):
    tipo: str
    prioridad: str
    titulo: str
    columna: Optional[str] = "Backlog"
    usuario_asignado: Optional[str] = None
    id_tecnico: Optional[str] = None
    tiempo_horas: Optional[int] = 0
    bloqueador: Optional[str] = None
