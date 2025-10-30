from __future__ import annotations

import win32serviceutil
import win32service
import win32event
import servicemanager
import schedule
import requests

import sys
import time
import typing as t

from src import logger, settings, monitor
from config import MonitorMan, Target


class WinServiceProxy(win32serviceutil.ServiceFramework):

    _svc_name_ = settings.SRV_NAME
    _svc_display_name_ = settings.SRV_DISPLAY_NAME

    def handle(self) -> None:
        result: monitor.MonitorResult = MonitorMan()
        try:
            requests.get(Target, params={
                'status': 'up' if result.status else 'down',
                'ping': int(result.avg),
                'msg': str(result)
            })
        except Exception as e:
            logger.error(f'cannot update {Target}: {str(result)} - {e}')
        else:
            logger.debug(f'updated {Target}: {str(result)}')

    def __init__(self, args: t.Iterable[str]) -> None:
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self._stopped = False

    def SvcStop(self) -> None:
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        logger.info("service stopping...")
        self._stopped = True

    def SvcDoRun(self) -> None:
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        logger.info("service starting...")
        self.main()

    def main(self) -> None:
        job = schedule.every(settings.SRV_HANDLE_FREQ_SEC).seconds.do(self.handle)
        while not self._stopped:
            logger.info(f'service next running at: {job.next_run}')
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(WinServiceProxy)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(WinServiceProxy)
