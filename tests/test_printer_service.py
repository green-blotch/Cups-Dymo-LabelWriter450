import importlib
import os
import sys
import types

import pytest
from PIL import Image


def _fake_cups_module(fake_connection):
    """Return a fake cups module exposing a Connection factory."""
    return types.SimpleNamespace(Connection=lambda: fake_connection)


@pytest.fixture()
def printer_service(monkeypatch):
    class FakeConnection:
        def __init__(self):
            self.print_calls = []
            self.printFile_return = 123
            self.raise_on_print = False
            self.printers = {"dymo": {"status": "ready"}}

        def printFile(self, printer, path, job_title, options):
            if self.raise_on_print:
                raise Exception("connection error")
            self.print_calls.append((printer, path, job_title, options))
            return self.printFile_return

        def getPrinters(self):
            return self.printers

    fake_conn = FakeConnection()
    fake_module = _fake_cups_module(fake_conn)
    monkeypatch.setitem(sys.modules, "cups", fake_module)

    import cups_dymo_label_printer.printer_service as ps

    importlib.reload(ps)
    service = ps.PrinterService()
    return service, fake_conn, ps


def test_print_builds_options_and_cleans_temp(printer_service):
    service, fake_conn, _ = printer_service
    fake_conn.printFile_return = 999
    image = Image.new("RGB", (10, 10), "white")

    job_id = service.print_image(image, label_size="11354", copies=2, job_title="Label")

    assert job_id == 999
    assert len(fake_conn.print_calls) == 1
    printer, path, job_title, options = fake_conn.print_calls[0]
    assert printer == "dymo"
    assert job_title == "Label"
    assert options == {"media": "w162h90", "fit-to-page": "True", "copies": "2"}
    assert not os.path.exists(path)


def test_reject_invalid_label_size(printer_service):
    service, fake_conn, _ = printer_service

    with pytest.raises(ValueError):
        service.print_image(Image.new("RGB", (10, 10), "white"), label_size="BAD")

    assert fake_conn.print_calls == []


def test_surface_cups_failure_as_runtime_error(printer_service):
    service, fake_conn, _ = printer_service
    fake_conn.raise_on_print = True

    with pytest.raises(RuntimeError) as exc:
        service.print_image(Image.new("RGB", (10, 10), "white"), label_size="11354")

    assert "Failed to print" in str(exc.value)


def test_report_printer_status_found(printer_service):
    service, fake_conn, _ = printer_service
    fake_conn.printers = {"dymo": {"state": "idle"}}

    status = service.get_printer_status()

    assert status == {"state": "idle"}


def test_report_printer_status_missing(printer_service):
    service, fake_conn, _ = printer_service
    fake_conn.printers = {}

    status = service.get_printer_status()

    assert status == {"error": "Printer not found"}
