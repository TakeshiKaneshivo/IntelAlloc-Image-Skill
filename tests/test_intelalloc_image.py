import argparse
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT_PATH = pathlib.Path(__file__).parents[1] / "skills" / "intelalloc-image" / "scripts" / "intelalloc_image.py"
SPEC = importlib.util.spec_from_file_location("intelalloc_image", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def request_args(host=None, model=None):
    return argparse.Namespace(runtime_host=host, runtime_model=model)


class RuntimeCredentialTests(unittest.TestCase):
    def test_workbuddy_matches_current_model_id(self):
        with tempfile.TemporaryDirectory() as directory:
            models_path = pathlib.Path(directory) / "models.json"
            models_path.write_text(
                json.dumps(
                    [
                        {"id": "glm-5.2", "name": "glm-5.2", "apiKey": "glm-key"},
                        {"id": "gpt-5.6-luna", "name": "gpt-5.6-luna", "apiKey": "luna-key"},
                    ]
                ),
                encoding="utf-8",
            )
            with mock.patch.object(MODULE, "workbuddy_models_path", return_value=models_path), mock.patch.dict(
                MODULE.os.environ, {}, clear=True
            ):
                result = MODULE.resolve_automatic_api_key(request_args("workbuddy", "gpt-5.6-luna"))

        self.assertEqual(result["api_key"], "luna-key")
        self.assertEqual(result["source"], "workbuddy-model")
        self.assertEqual(result["match"], "model-matched")
        self.assertEqual(result["reason"], "key-available")

    def test_workbuddy_lookup_reports_missing_or_invalid_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            models_path = pathlib.Path(directory) / "models.json"
            with mock.patch.object(MODULE, "workbuddy_models_path", return_value=models_path):
                key, reason = MODULE.load_workbuddy_model_api_key("gpt-5.6-luna")
                self.assertEqual((key, reason), ("", "model-not-found"))

                models_path.write_text("{not json", encoding="utf-8")
                key, reason = MODULE.load_workbuddy_model_api_key("gpt-5.6-luna")
                self.assertEqual((key, reason), ("", "model-not-found"))

                models_path.write_text(json.dumps({"models": []}), encoding="utf-8")
                key, reason = MODULE.load_workbuddy_model_api_key("gpt-5.6-luna")
                self.assertEqual((key, reason), ("", "models-invalid"))

                models_path.write_text(json.dumps([{"id": "gpt-5.6-luna"}]), encoding="utf-8")
                key, reason = MODULE.load_workbuddy_model_api_key("gpt-5.6-luna")
                self.assertEqual((key, reason), ("", "model-key-missing"))

    def test_unknown_runtime_does_not_read_models(self):
        with mock.patch.object(MODULE, "load_workbuddy_model_api_key") as load_key, mock.patch.dict(
            MODULE.os.environ, {}, clear=True
        ):
            result = MODULE.resolve_automatic_api_key(request_args())

        load_key.assert_not_called()
        self.assertEqual(result["host"], "unknown")
        self.assertEqual(result["reason"], "runtime-host-unknown")
        self.assertEqual(result["match"], "not-checked")

    def test_codebuddy_runtime_variables_are_supported(self):
        with mock.patch.object(MODULE, "load_workbuddy_model_api_key", return_value=("luna-key", "model-matched")), mock.patch.dict(
            MODULE.os.environ,
            {"CODEBUDDY_SESSION_ID": "session", "CODEBUDDY_MODEL": "custom-local:gpt-5.6-luna"},
            clear=True,
        ):
            result = MODULE.resolve_automatic_api_key(request_args())

        self.assertEqual(result["host"], "workbuddy")
        self.assertEqual(result["model"], "custom-local:gpt-5.6-luna")
        self.assertEqual(result["model_source"], "workbuddy-environment")
        self.assertEqual(result["api_key"], "luna-key")

    def test_non_gpt_workbuddy_model_does_not_read_models(self):
        with mock.patch.object(MODULE, "load_workbuddy_model_api_key") as load_key, mock.patch.dict(
            MODULE.os.environ, {}, clear=True
        ):
            result = MODULE.resolve_automatic_api_key(request_args("workbuddy", "glm-5.2"))

        load_key.assert_not_called()
        self.assertEqual(result["reason"], "runtime-model-not-gpt")
        self.assertEqual(result["match"], "not-checked")

    def test_codex_uses_auth_for_gpt_runtime(self):
        with mock.patch.object(MODULE, "load_codex_auth_api_key", return_value="codex-key"), mock.patch.dict(
            MODULE.os.environ, {}, clear=True
        ):
            result = MODULE.resolve_automatic_api_key(request_args("codex", "gpt-5.6-terra"))

        self.assertEqual(result["api_key"], "codex-key")
        self.assertEqual(result["source"], "codex-auth")
        self.assertEqual(result["match"], "auth-file")


class KeySelectionTests(unittest.TestCase):
    def test_saved_automatic_config_takes_precedence_over_current_model(self):
        cfg = {
            "api_key": "old-key",
            "api_key_origin": "workbuddy-model",
            "api_key_runtime_host": "workbuddy",
            "api_key_runtime_model": "gpt-old",
        }
        automatic = {
            "api_key": "new-key",
            "source": "workbuddy-model",
            "reason": "key-available",
            "match": "model-matched",
            "host": "workbuddy",
            "model": "gpt-5.6-luna",
            "host_source": "cli",
            "model_source": "cli",
            "model_is_gpt": "true",
        }
        with mock.patch.object(MODULE, "load_config", return_value=cfg), mock.patch.object(
            MODULE, "resolve_automatic_api_key", return_value=automatic
        ) as resolve_auto, mock.patch.object(MODULE, "save_automatic_api_key") as save_key:
            settings = MODULE.resolve_settings(request_args("workbuddy", "gpt-5.6-luna"), require_key=True)

        self.assertEqual(settings["api_key"], "old-key")
        self.assertEqual(settings["api_key_source"], "config")
        self.assertEqual(settings["stored_automatic_key_matches_runtime"], "false")
        resolve_auto.assert_not_called()
        save_key.assert_not_called()

    def test_saved_automatic_config_is_preferred_when_model_matches(self):
        cfg = {
            "api_key": "saved-key",
            "api_key_origin": "workbuddy-model",
            "api_key_runtime_host": "workbuddy",
            "api_key_runtime_model": "gpt-5.6-luna",
        }
        automatic = {
            "api_key": "current-key",
            "source": "workbuddy-model",
            "reason": "key-available",
            "match": "model-matched",
            "host": "workbuddy",
            "model": "gpt-5.6-luna",
            "host_source": "cli",
            "model_source": "cli",
            "model_is_gpt": "true",
        }
        with mock.patch.object(MODULE, "load_config", return_value=cfg), mock.patch.object(
            MODULE, "resolve_automatic_api_key", return_value=automatic
        ) as resolve_auto, mock.patch.object(MODULE, "save_automatic_api_key") as save_key:
            settings = MODULE.resolve_settings(request_args("workbuddy", "gpt-5.6-luna"), require_key=True)

        self.assertEqual(settings["api_key"], "saved-key")
        self.assertEqual(settings["stored_automatic_key_matches_runtime"], "true")
        resolve_auto.assert_not_called()
        save_key.assert_not_called()

    def test_saved_automatic_config_is_reused_when_current_lookup_fails(self):
        cfg = {
            "api_key": "saved-key",
            "api_key_origin": "workbuddy-model",
            "api_key_runtime_host": "workbuddy",
            "api_key_runtime_model": "gpt-5.6-luna",
        }
        automatic = {
            "api_key": "",
            "source": "workbuddy-model",
            "reason": "model-not-found",
            "match": "model-not-found",
            "host": "workbuddy",
            "model": "gpt-5.6-luna",
            "host_source": "cli",
            "model_source": "cli",
            "model_is_gpt": "true",
        }
        with mock.patch.object(MODULE, "load_config", return_value=cfg), mock.patch.object(
            MODULE, "resolve_automatic_api_key", return_value=automatic
        ) as resolve_auto, mock.patch.object(MODULE, "save_automatic_api_key") as save_key:
            settings = MODULE.resolve_settings(request_args("workbuddy", "gpt-5.6-luna"), require_key=True)

        self.assertEqual(settings["api_key"], "saved-key")
        self.assertEqual(settings["api_key_source"], "config")
        self.assertEqual(settings["stored_automatic_key_matches_runtime"], "true")
        resolve_auto.assert_not_called()
        save_key.assert_not_called()

    def test_manual_configured_key_keeps_precedence(self):
        cfg = {"api_key": "manual-key", "api_key_origin": "manual"}
        automatic = {
            "api_key": "automatic-key",
            "source": "workbuddy-model",
            "reason": "key-available",
            "match": "model-matched",
            "host": "workbuddy",
            "model": "gpt-5.6-luna",
            "host_source": "cli",
            "model_source": "cli",
            "model_is_gpt": "true",
        }
        with mock.patch.object(MODULE, "load_config", return_value=cfg), mock.patch.object(
            MODULE, "resolve_automatic_api_key", return_value=automatic
        ) as resolve_auto, mock.patch.object(MODULE, "save_automatic_api_key") as save_key:
            settings = MODULE.resolve_settings(request_args(), require_key=True)

        self.assertEqual(settings["api_key"], "manual-key")
        self.assertEqual(settings["api_key_source"], "config")
        resolve_auto.assert_not_called()
        save_key.assert_not_called()


class RuntimeArgumentTests(unittest.TestCase):
    def test_help_reports_host_specific_default_outputs(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(MODULE.command_help(argparse.Namespace()), 0)

        help_text = output.getvalue()
        self.assertIn("Codex: saves under ~/Pictures/IntelAlloc/Codex", help_text)
        self.assertIn("WorkBuddy: saves under ~/Pictures/IntelAlloc/WorkBuddy", help_text)
        self.assertIn("Unknown host: keeps ~/Pictures/IntelAlloc", help_text)

    def test_all_stateful_commands_accept_workbuddy_runtime_arguments(self):
        parser = MODULE.build_parser()
        commands = (
            ("configure", ["--api-key", "manual-key"]),
            ("show-config", []),
            ("generate", ["--prompt", "test"]),
            ("edit", ["--prompt", "test", "--input", "image.png"]),
            ("batch-edit", ["--prompt", "test", "--input-dir", "images"]),
            ("last", []),
            ("history", []),
        )
        for command, required_args in commands:
            with self.subTest(command=command):
                args = parser.parse_args(
                    [
                        command,
                        "--runtime-host",
                        "workbuddy",
                        "--runtime-model",
                        "gpt-5.6-luna",
                        *required_args,
                    ]
                )
                self.assertEqual(args.runtime_host, "workbuddy")
                self.assertEqual(args.runtime_model, "gpt-5.6-luna")


class HostStateIsolationTests(unittest.TestCase):
    def test_workbuddy_paths_are_macos_home_relative(self):
        mac_home = pathlib.PurePosixPath("/Users/tester")
        with mock.patch.object(MODULE.pathlib.Path, "home", return_value=mac_home), mock.patch.object(
            MODULE.platform, "system", return_value="Darwin"
        ):
            self.assertEqual(
                MODULE.config_path("workbuddy"),
                pathlib.PurePosixPath("/Users/tester/.workbuddy-ai/intelalloc-image/config.json"),
            )
            self.assertEqual(
                MODULE.history_path("workbuddy"),
                pathlib.PurePosixPath("/Users/tester/.workbuddy-ai/intelalloc-image/history.json"),
            )
            self.assertEqual(
                MODULE.workbuddy_models_path(), pathlib.PurePosixPath("/Users/tester/.workbuddy-ai/models.json")
            )
            self.assertEqual(
                MODULE.default_output_dir("workbuddy"),
                pathlib.PurePosixPath("/Users/tester/Pictures/IntelAlloc/WorkBuddy"),
            )

    def test_paths_and_default_outputs_are_host_specific(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            MODULE.pathlib.Path, "home", return_value=pathlib.Path(directory)
        ):
            self.assertEqual(
                MODULE.config_path("codex"),
                pathlib.Path(directory) / ".codex" / "intelalloc-image" / "config.json",
            )
            self.assertEqual(
                MODULE.history_path("workbuddy"),
                pathlib.Path(directory) / ".workbuddy-ai" / "intelalloc-image" / "history.json",
            )
            self.assertEqual(
                MODULE.default_output_dir("codex"),
                pathlib.Path(directory) / "Pictures" / "IntelAlloc" / "Codex",
            )
            self.assertEqual(
                MODULE.default_output_dir("workbuddy"),
                pathlib.Path(directory) / "Pictures" / "IntelAlloc" / "WorkBuddy",
            )
            self.assertEqual(MODULE.config_path("unknown"), MODULE.config_path("codex"))
            self.assertEqual(
                MODULE.default_output_dir("unknown"), pathlib.Path(directory) / "Pictures" / "IntelAlloc"
            )

    def test_configure_keeps_codex_and_workbuddy_configs_separate(self):
        parser = MODULE.build_parser()
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            MODULE.pathlib.Path, "home", return_value=pathlib.Path(directory)
        ):
            codex_args = parser.parse_args(
                ["configure", "--runtime-host", "codex", "--api-key", "codex-key"]
            )
            workbuddy_args = parser.parse_args(
                ["configure", "--runtime-host", "workbuddy", "--api-key", "workbuddy-key"]
            )
            self.assertEqual(MODULE.command_configure(codex_args), 0)
            self.assertEqual(MODULE.command_configure(workbuddy_args), 0)
            self.assertEqual(MODULE.load_config("codex")["api_key"], "codex-key")
            self.assertEqual(MODULE.load_config("workbuddy")["api_key"], "workbuddy-key")

    def test_history_and_from_last_do_not_cross_hosts(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            MODULE.pathlib.Path, "home", return_value=pathlib.Path(directory)
        ):
            codex_image = pathlib.Path(directory) / "codex.png"
            workbuddy_image = pathlib.Path(directory) / "workbuddy.png"
            codex_image.touch()
            workbuddy_image.touch()
            MODULE.add_history({"type": "generate"}, [codex_image], "codex")
            MODULE.add_history({"type": "generate"}, [workbuddy_image], "workbuddy")

            self.assertEqual(MODULE.get_last_output_path("codex"), codex_image.resolve())
            self.assertEqual(MODULE.get_last_output_path("workbuddy"), workbuddy_image.resolve())
            args = argparse.Namespace(inputs=[], input_dir=None, recursive=False, limit=None, from_last=True)
            self.assertEqual(MODULE.resolve_inputs(args, "workbuddy"), [workbuddy_image.resolve()])

    def test_explicit_output_paths_are_not_rewritten(self):
        explicit_file = MODULE.resolve_output_path(
            argparse.Namespace(output="D:/out/result.png", output_dir=None), "generate", "workbuddy"
        )
        explicit_directory = MODULE.resolve_output_path(
            argparse.Namespace(output=None, output_dir="D:/out"), "generate", "codex"
        )
        self.assertEqual(explicit_file, pathlib.Path("D:/out/result.png"))
        self.assertEqual(explicit_directory.parent, pathlib.Path("D:/out"))


if __name__ == "__main__":
    unittest.main()
