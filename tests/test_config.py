from pathlib import Path

import yaml

from kai.config import DEFAULTS, load_config


def test_missing_file_returns_defaults(tmp_path):
    cfg = load_config(tmp_path / "nope.yaml")
    assert cfg == DEFAULTS
    assert cfg is not DEFAULTS  # must be a copy


def test_deep_merge_preserves_unset_keys(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump({"tts": {"rate": 220}}), encoding="utf-8")
    cfg = load_config(path)
    assert cfg["tts"]["rate"] == 220
    assert cfg["tts"]["enabled"] is True  # default kept
    assert cfg["persona"] == "kai"
    assert cfg["wake_word"]["keyword"] is None  # None = persona's name


def test_custom_commands_load(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        yaml.safe_dump({"commands": [{"phrase": "deploy status", "run": "kubectl get pods"}]}),
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg["commands"][0]["phrase"] == "deploy status"


def test_non_mapping_root_rejected(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("- just\n- a list\n", encoding="utf-8")
    try:
        load_config(path)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
