from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from statistics import mean
from typing import Protocol, List
from datetime import datetime   
from enum import Enum           



class TipoNotificacion(Enum):  
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"
    SMS = "SMS"

class NivelAlerta(Enum):      
    NORMAL = "NORMAL"
    ADVERTENCIA = "ADVERTENCIA"
    CRITICO = "CRITICO"


class Notificador(Protocol):
    def enviar(self, mensaje: str) -> None: ...


class NotificadorEmail:
    def __init__(self, destinatario: str) -> None:
        self._destinatario = destinatario
    def enviar(self, mensaje: str) -> None:
        print(f"[EMAIL a {self._destinatario}] {mensaje}")


class NotificadorWebhook:
    def __init__(self, url: str) -> None:
        self._url = url
    def enviar(self, mensaje: str) -> None:
        print(f"[WEBHOOK {self._url}] {mensaje}")


class NotificadorSMS:   
    def __init__(self, telefono: str) -> None:
        self._telefono = telefono
    def enviar(self, mensaje: str) -> None:
        print(f"[SMS a {self._telefono}] {mensaje}")



@dataclass
class Sensor(ABC):
    id: str
    ventana: int = 5
    _calibracion: float = field(default=0.0, repr=False)
    _buffer: list[float] = field(default_factory=list, repr=False)

    def leer(self, valor: float) -> None:
        v = valor + self._calibracion
        self._buffer.append(v)
        if len(self._buffer) > self.ventana:
            self._buffer.pop(0)

    @property
    def promedio(self) -> float:
        return mean(self._buffer) if self._buffer else 0.0

    @abstractmethod
    def en_alerta(self) -> bool: ...


@dataclass
class SensorTemperatura(Sensor):
    umbral: float = 80.0
    def en_alerta(self) -> bool:
        return self.promedio >= self.umbral


@dataclass
class SensorVibracion(Sensor):
    rms_umbral: float = 2.5
    def en_alerta(self) -> bool:
        return abs(self.promedio) >= self.rms_umbral
    def calcular_rms(self) -> float: 
        return (sum(x**2 for x in self._buffer) / len(self._buffer))**0.5 if self._buffer else 0.0


@dataclass
class SensorPresion(Sensor):   
    presion_max: float = 100.0
    presion_min: float = 1.0
    def en_alerta(self) -> bool:
        return not (self.presion_min <= self.promedio <= self.presion_max)



class Alerta:   
    sensor_id: str
    mensaje: str
    hora: datetime
    nivel: NivelAlerta = NivelAlerta.NORMAL
    def es_critica(self) -> bool:
        return self.nivel == NivelAlerta.CRITICO



class GestorAlertas:
    def __init__(self, sensores: List[Sensor], notificadores: List[Notificador]) -> None:
        self._sensores = sensores
        self._notificadores = notificadores
        self._historial: List[Alerta] = []   

    def evaluar_y_notificar(self) -> None:
        for s in self._sensores:
            if s.en_alerta():
                msg = f"ALERTA: Sensor {s.id} en umbral (avg={s.promedio:.2f})"
                alerta = Alerta(sensor_id=s.id, mensaje=msg, hora=datetime.now(), nivel=NivelAlerta.CRITICO) 
                self._historial.append(alerta)  
                for n in self._notificadores:
                    n.enviar(msg)
