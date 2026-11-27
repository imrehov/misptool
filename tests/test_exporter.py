import base64
import json
from unittest.mock import Mock

import pytest

from scripts.exporter import dump_inline_attachments, fetch_all_events, fetch_recent_events, save_events_json
from src.misptool.application.cli_commands import CliCommands


def event(event_id="42", attributes=None):
    return {"id": event_id, "info": "test event", "Attribute": attributes or [], "Object": []}


def attachment(filename="report.txt", content=b"harmless test", attr_type="attachment"):
    return {"type": attr_type, "value": filename, "data": base64.b64encode(content).decode()}


def test_full_export_searches_full_events_and_pages_until_empty():
    client = Mock()
    first = event("1", [attachment()])
    second = event("2")
    client.search.side_effect = [[{"Event": first}], {"response": [second]}, []]

    assert fetch_all_events(client, with_attachments=True) == [first, second]
    client.events.assert_not_called()
    assert [call.kwargs["page"] for call in client.search.call_args_list] == [1, 2, 3]
    for call in client.search.call_args_list:
        assert call.kwargs == {
            "controller": "events", "return_format": "json", "pythonify": False,
            "metadata": False, "with_attachments": True, "limit": 100, "page": call.kwargs["page"],
        }


def test_recent_export_passes_lookback_and_excludes_attachments_by_default():
    client = Mock()
    client.search.side_effect = [[{"Event": event()}], []]
    assert fetch_recent_events(client, 15) == [event()]
    for call in client.search.call_args_list:
        assert call.kwargs["timestamp"] == "15m"
        assert call.kwargs["with_attachments"] is False


def test_export_uses_installed_pymisp_request_format_through_client_wrapper():
    from pymisp import PyMISP
    from src.misptool.infrastructure.misp_client import MispClient

    client = object.__new__(PyMISP)
    client.root_url = "https://misp.example/"
    client.global_pythonify = False
    client._prepare_request = Mock()
    client._check_json_response = Mock(side_effect=[[{"Event": event()}], []])
    wrapper = object.__new__(MispClient)
    wrapper.misp_client = client

    assert fetch_recent_events(wrapper, 10, with_attachments=True) == [event()]
    for call in client._prepare_request.call_args_list:
        assert call.args == ("POST", "https://misp.example/events/restSearch")
        payload = call.kwargs["data"]
        assert payload["returnFormat"] == "json"
        assert payload["withAttachments"] == 1
        assert payload["metadata"] == 0
        assert payload["timestamp"] == "10m"


@pytest.mark.parametrize("response", [
    {"errors": ["Access denied"]}, {"error": "failed"},
    {"response": {"errors": ["failed"]}}, {"message": "failed"},
    None, "invalid JSON", ["not an event"], [{"Event": {}}], [{"id": None}],
])
def test_api_errors_and_invalid_responses_raise_clear_errors(response):
    client = Mock()
    client.search.return_value = response
    with pytest.raises(RuntimeError, match="MISP"):
        fetch_all_events(client)


def test_failed_later_page_does_not_overwrite_existing_export(tmp_path, monkeypatch):
    client = Mock()
    client.search.side_effect = [[{"Event": event()}], {"errors": ["failed"]}]
    output = tmp_path / "events.json"
    output.write_text("existing export")
    commands = CliCommands("unused.yaml")
    monkeypatch.setattr(commands, "build_misp", lambda: client)
    with pytest.raises(RuntimeError, match="page 2"):
        commands.export_events(str(output))
    assert output.read_text() == "existing export"


def test_repeated_pages_abort_instead_of_looping_forever():
    client = Mock()
    client.search.return_value = [{"Event": event()}]
    with pytest.raises(RuntimeError, match="pagination"):
        fetch_all_events(client)
    assert client.search.call_count == 2


def test_overlapping_pages_do_not_duplicate_events():
    client = Mock()
    client.search.side_effect = [[event("1")], [event("1"), event("2")], []]
    assert [item["id"] for item in fetch_all_events(client)] == ["1", "2"]


@pytest.mark.parametrize("lookback", [0, -1])
def test_recent_export_rejects_invalid_lookback(lookback):
    with pytest.raises(ValueError, match="positive"):
        fetch_recent_events(Mock(), lookback)


def test_json_save_is_atomic_and_keeps_unicode(tmp_path):
    output = tmp_path / "nested" / "events.json"
    save_events_json([{"info": "ü test"}], str(output))
    assert json.loads(output.read_text()) == [{"info": "ü test"}]
    with pytest.raises(TypeError):
        save_events_json([{"invalid": object()}], str(output))
    assert json.loads(output.read_text()) == [{"info": "ü test"}]
    assert list(output.parent.iterdir()) == [output]


def test_dump_includes_object_attachments_and_keeps_duplicate_filenames(tmp_path):
    exported = event(attributes=[attachment(content=b"first")])
    exported["Object"] = [{"Attribute": [attachment(content=b"second"), attachment(
        "sample.exe|md5", b"zipped sample test", "malware-sample",
    )]}]
    assert dump_inline_attachments([exported], str(tmp_path)) == 3
    files = list((tmp_path / "42").iterdir())
    assert {path.read_bytes() for path in files} == {b"first", b"second", b"zipped sample test"}


@pytest.mark.parametrize("filename", ["../../escape.txt", "/tmp/escape.txt", "..\\..\\escape.txt", "..", ""])
def test_attachment_paths_stay_in_event_directory(tmp_path, filename):
    exported = event("../../outside", [attachment(filename)])
    assert dump_inline_attachments([exported], str(tmp_path / "attachments")) == 1
    files = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert len(files) == 1
    assert files[0].parent == tmp_path / "attachments" / "outside"


def test_existing_event_directory_symlink_cannot_escape_export(tmp_path):
    base = tmp_path / "attachments"
    base.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (base / "42").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="outside"):
        dump_inline_attachments([event(attributes=[attachment()])], str(base))
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("symlink", [False, True])
def test_existing_attachment_files_are_not_overwritten(tmp_path, symlink):
    exported = event(attributes=[attachment()])
    target = tmp_path / "42" / "1_report.txt"
    target.parent.mkdir()
    if symlink:
        original = tmp_path / "original.txt"
        original.write_bytes(b"keep")
        target.symlink_to(original)
    else:
        target.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        dump_inline_attachments([exported], str(tmp_path))
    assert target.read_bytes() == b"keep"


@pytest.mark.parametrize("data", ["not base64!", None])
def test_invalid_attachment_data_is_reported(tmp_path, data):
    exported = event(attributes=[{**attachment(), "data": data}])
    with pytest.raises(ValueError, match="base64"):
        dump_inline_attachments([exported], str(tmp_path))
    assert not list(tmp_path.rglob("*.txt"))


@pytest.mark.parametrize("recent", [False, True])
def test_cli_exports_full_json_and_attachments_next_to_output(tmp_path, monkeypatch, recent):
    client = Mock()
    exported = event(attributes=[attachment()])
    exported["Object"] = [{"Attribute": [attachment("object.txt", b"object test")]}]
    client.search.side_effect = [[{"Event": exported}], []]
    commands = CliCommands("unused.yaml")
    commands._config = {"polling": {"lookback_minutes": 20}}
    monkeypatch.setattr(commands, "build_misp", lambda: client)
    output = tmp_path / "export" / "events.json"

    commands.export_events(str(output), recent=recent, with_attachments=True)

    assert json.loads(output.read_text()) == [exported]
    assert (output.parent / "attachments" / "42" / "1_report.txt").read_bytes() == b"harmless test"
    assert (output.parent / "attachments" / "42" / "2_object.txt").read_bytes() == b"object test"
    for call in client.search.call_args_list:
        assert call.kwargs["with_attachments"] is True
        assert call.kwargs.get("timestamp") == ("20m" if recent else None)
