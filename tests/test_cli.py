"""CLI entrypoint: exit codes + directory/container dispatch + --foreign."""
import zipfile

import pytest

from sdplugin.cli import main


def _run(argv):
    with pytest.raises(SystemExit) as e:
        main(argv)
    return e.value.code


def test_cli_clean_exits_zero(plugin_factory, capsys):
    assert _run([str(plugin_factory())]) == 0
    assert "publication-ready" in capsys.readouterr().out


def test_cli_coloured_icon_exits_one(plugin_factory, capsys):
    assert _run([str(plugin_factory(white_icons=False))]) == 1
    assert "non-white-icon" in capsys.readouterr().out


def test_cli_strict_blocks_on_warning(plugin_factory):
    assert _run([str(plugin_factory(retina=False)), "--strict"]) == 1
    assert _run([str(plugin_factory(retina=False))]) == 0


def test_cli_foreign_override(plugin_factory):
    plug = plugin_factory(name="MIDI Thing", description="A midi plugin")
    (plug / "ui" / "connect.html").write_text("<p>midi note here</p>")
    assert _run([str(plug), "--foreign", "midi"]) == 1


def test_cli_container_dispatch(plugin_factory, tmp_path, capsys):
    plug = plugin_factory()
    archive = tmp_path / "demo.streamDeckPlugin"
    with zipfile.ZipFile(archive, "w") as z:
        for f in plug.rglob("*"):
            if f.is_file():
                z.write(f, f"{plug.name}/{f.relative_to(plug).as_posix()}")
    assert _run([str(archive)]) == 0
