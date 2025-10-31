from __future__ import annotations

from pythonping import ping

import socket
import typing as t
from abc import abstractmethod, ABC
from collections import deque
from dataclasses import dataclass, field

from . import settings, logger, timer


class Monitor(ABC):
    """Monitor interface definition."""

    def __init__(self) -> None:
        self._history_timer = deque(maxlen=settings.SRV_TIMER_DEQUE_SIZE)

    def __call__(self) -> float:
        self._history_timer.appendleft(self.run())
        if not self._history_timer:
            return 0.
        return sum(self._history_timer) / len(self._history_timer)

    @abstractmethod
    def run(self) -> float: ...

    @abstractmethod
    def __str__(self) -> str: ...


class PingMonitor(Monitor):
    
    def __init__(self, target: str, name: str = '') -> None:
        super().__init__()
        self.target = target
        self.name = name

    def __str__(self) -> str:
        if self.name:
            return f'Ping {self.name}({self.target})'
        return f'Ping {self.target}'

    def run(self) -> float:
        response = ping(
            self.target, 
            count=settings.PING_PACKET_COUNT, 
            timeout=settings.PING_TIMEOUT
        )
        if response.stats_success_ratio == 0.:
            logger.warning(f'ping {self.target} failed')
            raise RuntimeError(f'ping {self.target} failed')
        return response.rtt_avg_ms


class TCPMonitor(Monitor):

    def __init__(self, target: str, port: int, name: str = '') -> None:
        super().__init__()
        self.target = target
        self.name = name
        self.port = port

    def __str__(self) -> str:
        if self.name:
            return f'TCP {self.name}({self.target}:{self.port})'
        return f'TCP {self.target}:{self.port}'
    
    @timer
    def run(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(settings.TCP_TIMEOUT)
        try:
            result = sock.connect_ex((self.target, self.port))
            if result != 0:
                logger.warning(f'tcp port {self.port} closed for host {self.target}')
                raise RuntimeError('tcp port {self.port} closed for host {self.target}')
        except socket.error as e:
            logger.warning(f'tcp conn failed {self.target}:{self.port}')
            raise e
        finally:
            sock.close()


@dataclass
class MonitorResult:
    name: str
    status: bool
    avg: float
    children: t.List[MonitorResult] = field(default_factory=list)

    def __str__(self) -> str:
        status = '+' if self.status else '-'
        headline = f'{self.name}: {status}, {self.avg:.2f}'
        lines = [headline]
        for child in self.children:
            lines.append('\t' + str(child))
        return '\n'.join(lines)


class MonitorManager:

    def __init__(self, name: str, monitors: t.List[Monitor]) -> None:
        self.monitors = monitors
        self.name = name

    def __call__(self) -> MonitorResult:
        delay, status, results = [], True, []
        for monitor in self.monitors:
            try:
                delay.append(monitor())
                results.append(MonitorResult(str(monitor), avg=delay[-1], status=True))
            except Exception as e:
                logger.warning(f'running {monitor} failed: {e}')
                results.append(MonitorResult(str(monitor), avg=0., status=False))
                status = False
                continue
        if delay:
            avg = sum(delay) / len(delay)
        else:
            avg = 0.
        return MonitorResult(name=self.name, status=status, avg=avg, children=results)
