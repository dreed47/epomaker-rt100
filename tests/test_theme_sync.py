"""Theme sync logic, no keyboard needed. Run: python tests/test_theme_sync.py"""
import os
import tempfile
from pathlib import Path

# Isolate before importing core: settings, desktop files and runtime state.
TMP = Path(tempfile.mkdtemp(prefix="rt100-test-"))
os.environ.update(
    EPOMAKER_RT100_CONFIG_DIR=str(TMP / "app"),
    XDG_CONFIG_HOME=str(TMP / "config"),
    XDG_STATE_HOME=str(TMP / "state"),
    XDG_RUNTIME_DIR=str(TMP / "run"),
)
(TMP / "run").mkdir()

from epomaker_rt100 import core  # noqa: E402

assert str(core.SETTINGS_PATH).startswith(str(TMP)), core.SETTINGS_PATH


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# vivid: hue kept, stretched to full saturation; greys become white.
assert core.vivid((0x8B, 0xE9, 0xFD)) == (0, 0xD2, 0xFF)
assert core.vivid((0xD9, 0xA8, 0x62)) == (0xFF, 0x96, 0)
assert core.vivid((0x80, 0x80, 0x80)) == (255, 255, 255)

# desktop_colours: nothing on disk -> None.
assert core.desktop_colours() is None

theme = TMP / "state/omarchy/current/theme/colors.toml"
write(theme, 'accent = "#0A84FF"\nforeground = "#F5F5F7"\n')
assert core.desktop_colours() == ((0x0A, 0x84, 0xFF), (0xF5, 0xF5, 0xF7))

# Bar override wins over the accent; other sections' background is ignored.
shell = TMP / "config/omarchy/shell.toml"
write(shell, '[font]\nbackground = "#000001"\n[bar]\nbackground = "#7f3f0a"\n')
assert core.desktop_colours()[0] == (0x7F, 0x3F, 0x0A)
write(shell, "not = [valid toml")
assert core.desktop_colours()[0] == (0x0A, 0x84, 0xFF)


# theme_key_colours: accent group vs rest, BACKSLASH via calibrated name.
class Key:
    def __init__(self, name, value):
        self.name, self.value = name, value


keys = [Key("LEFT_SHIFT", 4), Key("Q", 8), Key("HASH", 75)]
out = core.theme_key_colours(keys, ["LEFT_SHIFT", "BACKSLASH"], "A", "T", "HASH")
assert out == {4: "A", 8: "T", 75: "A"}, out

# Real keymap: every default key name exists, so none silently drop out.
if not core.IMPORT_ERROR:
    names = {k.name for k in core.keymap_keys()}
    missing = set(core.THEME_SYNC_DEFAULT_KEYS) - names
    assert not missing, missing

# sync_theme does nothing (and never opens the device) while switched off.
assert core.sync_theme() == (0, "Follow desktop colours is off.")

print("ok")
