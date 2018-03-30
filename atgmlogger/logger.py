# -*- coding: utf-8 -*-

import io
from pathlib import Path

from atgmlogger import APPLOG
from .plugins import PluginInterface
from .dispatcher import Command

__all__ = ['DataLogger']


class DataLogger(PluginInterface):
    options = ['logfile']

    def __init__(self):
        super().__init__()
        self.logfile = Path('gravdata.dat')
        self._hdl = None  # type: io.TextIOBase
        self._params = dict(mode='w+', buffering=1, encoding='utf-8',
                            newline='\n')

    @staticmethod
    def consumer_type():
        return {str, Command}

    def _get_fhandle(self):
        self._hdl = self.logfile.open(**self._params)

    def log_rotate(self):
        """
        Call this to notify the logger that logs may have been rotated by the
        system.
        Flush, close then reopen the handle.

        Returns
        -------

        """
        APPLOG.info("LogRotate signal received, re-opening log handle.")
        if self._hdl is None:
            return

        try:
            self._hdl.flush()
            self._hdl.close()
            self._hdl = None
        except IOError:
            APPLOG.exception()
            return

        self._get_fhandle()
        APPLOG.debug("LogRotate completed without exception, handle opened "
                     "on path %s", self._hdl.name)

    def run(self):
        try:
            self._get_fhandle()
        except IOError:
            APPLOG.exception("Error opening file for writing.")
            return

        # TODO: Maybe sample first 5 lines of data, find the mode (freq) of
        # data transmission to set Blink frequency
        while not self.exiting:
            try:
                item = self.get(block=True, timeout=None)
                if item is None:
                    self.queue.task_done()
                    continue
                if isinstance(item, Command):
                    if item.cmd == 'rotate':
                        self.log_rotate()
                else:
                    self._hdl.write(item + '\n')
                    self.context.blink()
                    self.queue.task_done()
            except IOError:
                APPLOG.exception()
                continue
        self._hdl.close()

    def configure(self, **options):
        super().configure(**options)
