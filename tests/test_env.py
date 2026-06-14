"""Tests for forge.env — minimal .env loader (no extra dependency)."""
import os

from forge import env


class TestLoadDotenv:
    def test_loads_keys_without_overriding_existing(self, tmp_path, monkeypatch):
        envfile = tmp_path / ".env"
        envfile.write_text("# comment\nCMC_API_KEY=abc123\nEMPTY=\nFOO = bar \n")
        monkeypatch.delenv("CMC_API_KEY", raising=False)
        monkeypatch.setenv("FOO", "already-set")

        env.load_dotenv(envfile)

        assert os.environ["CMC_API_KEY"] == "abc123"
        assert os.environ["FOO"] == "already-set"   # existing env wins (setdefault)

    def test_missing_file_is_noop(self, tmp_path):
        env.load_dotenv(tmp_path / "nope.env")  # must not raise

    def test_strips_surrounding_quotes(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text('CMC_API_KEY="quoted-key"\n')
        monkeypatch.delenv("CMC_API_KEY", raising=False)
        env.load_dotenv(tmp_path / ".env")
        assert os.environ["CMC_API_KEY"] == "quoted-key"

    def test_strips_utf8_bom(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_bytes("﻿CMC_API_KEY=bomkey\n".encode("utf-8"))
        monkeypatch.delenv("CMC_API_KEY", raising=False)
        env.load_dotenv(tmp_path / ".env")
        assert os.environ["CMC_API_KEY"] == "bomkey"

    def test_strips_inline_comment(self, tmp_path, monkeypatch):
        (tmp_path / ".env").write_text("CMC_API_KEY=k123 # my key\n")
        monkeypatch.delenv("CMC_API_KEY", raising=False)
        env.load_dotenv(tmp_path / ".env")
        assert os.environ["CMC_API_KEY"] == "k123"
