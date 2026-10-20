"""Regression tests using real local directories and ZIPs; no network access."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import warnings
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "core" / "yaya" / "scripts" / "packs.py"
SPEC = importlib.util.spec_from_file_location("yaya_packs", SCRIPT)
PACKS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PACKS
SPEC.loader.exec_module(PACKS)


class PackChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.data = self.base / "user"
        self.project = self.base / "project"
        self.core = self.base / "core"
        self.core.mkdir()
        self.core_patch = mock.patch.object(PACKS, "CORE", self.core)
        self.core_patch.start()
        self.addCleanup(self.core_patch.stop)
        self.archive_counter = 0

    def files(self, identifier="ja", version="0.1.0", **changes):
        metadata = {
            "format_version": 1,
            "id": identifier,
            "version": version,
            "core_major": 0,
            "name": "Test language pack",
            "license": "MIT",
            "quality": "experimental",
            "direction": "ltr",
        }
        metadata.update(changes)
        return {
            "pack.json": json.dumps(metadata).encode("utf-8"),
            "GUIDE.md": ("# Guide\nVersion " + version + "\n").encode(),
            "examples.md": "# Examples\n原文 → 改写\n".encode("utf-8"),
            "LICENSE": b"MIT test fixture license\n",
        }

    def directory(self, root, identifier="ja", **changes):
        path = root / identifier
        path.mkdir(parents=True)
        for name, content in self.files(identifier, **changes).items():
            (path / name).write_bytes(content)
        return path

    def archive(self, files=None, extra=()):
        self.archive_counter += 1
        path = self.base / f"pack-{self.archive_counter}.zip"
        files = self.files() if files is None else files
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                for name, content in files.items():
                    archive.writestr(name, content)
                for name, content, mode in extra:
                    info = zipfile.ZipInfo(name)
                    info.create_system = 3
                    info.external_attr = mode << 16
                    archive.writestr(info, content)
        return path, hashlib.sha256(path.read_bytes()).hexdigest()

    def install(self, files=None, **kwargs):
        archive, digest = self.archive(files)
        return PACKS.install(archive, digest, data_dir=str(self.data), **kwargs)

    def installed(self, identifier="ja"):
        return self.data / "language-packs" / identifier

    def version(self, directory):
        return json.loads((directory / "pack.json").read_text(encoding="utf-8"))["version"]

    def assert_no_stage(self):
        self.assertFalse(list(self.data.glob(".stage-*")))

    def link_directory(self, link, target):
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(target, link, target_is_directory=True)
            return
        except OSError:
            if os.name != "nt":
                self.skipTest("Directory symlinks unavailable")
        # Windows junctions do not need developer mode or administrative rights.
        run = subprocess.run(["cmd", "/d", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
        if run.returncode:
            self.skipTest("Directory symlinks and junctions unavailable")

    def test_tag_profile_and_canonical_casing(self):
        cases = {
            "FR-ca": "fr-CA", "sr-latn-rs": "sr-Latn-RS", "es-419": "es-419",
            "sl-ROZAJ-biske": "sl-rozaj-biske", "de-1901": "de-1901", "abc": "abc",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(PACKS.canonical_tag(source), expected)
        for value in ("", "x-private", "i-klingon", "en_US", "en-u-ca-gregory", "zh-cmn", "en-abc", "en-US-US", "sl-rozaj-ROZAJ", "../ja", "中文"):
            with self.subTest(value=value), self.assertRaises(PACKS.PackError):
                PACKS.canonical_tag(value)
        with self.assertRaises(PACKS.PackError):
            PACKS.pack_id("FR-ca")

    def test_fallback_sequence_and_chinese_region_inference(self):
        self.assertEqual(PACKS.candidates("fr-CA"), ["fr-CA", "fr"])
        self.assertEqual(PACKS.candidates("sr-Latn-RS"), ["sr-Latn-RS", "sr-Latn", "sr"])
        self.assertEqual(PACKS.candidates("zh-TW"), ["zh-TW", "zh-Hant-TW", "zh-Hant", "zh"])
        self.assertEqual(PACKS.candidates("zh-CN"), ["zh-CN", "zh-Hans-CN", "zh-Hans", "zh"])
        self.assertEqual(PACKS.candidates("zh-Hans-TW"), ["zh-Hans-TW", "zh-Hans", "zh"])

    def test_location_precedence_before_specificity(self):
        self.directory(self.project / ".yaya" / "language-packs", "fr")
        self.directory(self.data / "language-packs", "fr-CA")
        self.directory(self.core / "languages", "fr-CA")
        result = PACKS.resolve("fr-CA", str(self.data), str(self.project))
        self.assertEqual((result["status"], result["source"], result["resolved"]), ("ready", "project", "fr"))

    def test_exact_pack_before_fallback_in_same_location(self):
        self.directory(self.data / "language-packs", "fr")
        self.directory(self.data / "language-packs", "fr-CA")
        self.assertEqual(PACKS.resolve("FR-ca", str(self.data))["resolved"], "fr-CA")

    def test_bundled_fallback_does_not_cross_scripts(self):
        self.directory(self.core / "languages", "zh-Hans")
        self.directory(self.core / "languages", "en")
        self.assertEqual(PACKS.resolve("zh-CN", str(self.data))["resolved"], "zh-Hans")
        self.assertEqual(PACKS.resolve("zh-TW", str(self.data))["status"], "missing")

    def test_missing_lookup_is_read_only(self):
        self.assertEqual(PACKS.resolve("ja", str(self.data), str(self.project))["status"], "missing")
        self.assertEqual(PACKS.inventory(str(self.data), str(self.project))["packs"], [])
        self.assertFalse(self.data.exists())
        self.assertFalse(self.project.exists())

    def test_invalid_higher_priority_pack_blocks_fallback(self):
        path = self.directory(self.project / ".yaya" / "language-packs", "fr-CA")
        (path / "GUIDE.md").write_bytes(b"")
        self.directory(self.data / "language-packs", "fr-CA")
        result = PACKS.resolve("fr-CA", str(self.data), str(self.project))
        self.assertEqual((result["status"], result["source"], result["available"]), ("invalid", "project", False))

    def test_incompatible_pack_is_explicit_and_blocks_fallback(self):
        self.directory(self.project / ".yaya" / "language-packs", "ja", core_major=99)
        self.directory(self.data / "language-packs", "ja")
        result = PACKS.resolve("ja", str(self.data), str(self.project))
        self.assertEqual((result["status"], result["available"]), ("incompatible", False))
        items = PACKS.inventory(str(self.data), str(self.project))["packs"]
        self.assertEqual(items[0]["status"], "incompatible")

    def test_directory_id_mismatch_is_invalid(self):
        path = self.directory(self.data / "language-packs", "ja")
        (path / "pack.json").write_bytes(self.files("ko")["pack.json"])
        self.assertEqual(PACKS.resolve("ja", str(self.data))["status"], "invalid")
        self.assertEqual(PACKS.inventory(str(self.data))["packs"][0]["status"], "invalid")

    def test_metadata_protocol_is_strict(self):
        path = self.base / "fixture"
        path.mkdir()
        mutations = [
            {"format_version": True}, {"core_major": -1}, {"version": "1.02.0"},
            {"version": "1.0.0-01"}, {"name": " "}, {"license": "MIT OR Apache-2.0"},
            {"name": " " * 100 + "x"},
            {"quality": "excellent"}, {"direction": "auto"}, {"id": "JA"}, {"surprise": "field"},
        ]
        for mutation in mutations:
            for name, content in self.files(**mutation).items():
                (path / name).write_bytes(content)
            with self.subTest(mutation=mutation), self.assertRaises(PACKS.PackError):
                PACKS.validate(path)
        for name, content in self.files().items():
            (path / name).write_bytes(content)
        metadata = self.files()["pack.json"].decode().replace('"id": "ja"', '"id": "ja", "id": "ko"')
        (path / "pack.json").write_text(metadata, encoding="utf-8")
        with self.assertRaises(PACKS.PackError):
            PACKS.validate(path)

    def test_reviewed_quality_requires_evidence(self):
        path = self.directory(self.base / "fixtures", quality="reviewed")
        with self.assertRaises(PACKS.PackError):
            PACKS.validate(path)
        (path / "REVIEW.md").write_text("Reviewed against listed examples.\n", encoding="utf-8")
        self.assertEqual(PACKS.validate(path)["quality"], "reviewed")

    def test_current_format_resolves_optional_patterns(self):
        for identifier, has_patterns in (
            ("en", False), ("fr", False), ("ja", True),
        ):
            with self.subTest(identifier=identifier):
                path = self.directory(self.data / "language-packs", identifier)
                if has_patterns:
                    (path / "PATTERNS.md").write_text("# Patterns\nKeep useful wording.\n", encoding="utf-8")
                self.assertEqual(PACKS.validate(path)["format_version"], 1)
                result = PACKS.resolve(identifier, str(self.data))
                self.assertEqual((result["status"], result["format_version"]), ("ready", 1))
                self.assertEqual(result["patterns"], str((path / "PATTERNS.md").resolve()) if has_patterns else None)
        self.assertTrue(all(item["status"] == "ready" for item in PACKS.inventory(str(self.data))["packs"]))
        self.assertIsNone(PACKS.resolve("ko", str(self.data))["patterns"])

    def test_content_update_rollback_and_remove_preserve_complete_versions(self):
        original = self.files()
        upgraded = self.files(version="0.2.0")
        upgraded["PATTERNS.md"] = "# Patterns\n作者の表現を保つ。\n".encode("utf-8")
        self.install(original)
        self.assertIsNone(PACKS.resolve("ja", str(self.data))["patterns"])
        update = self.install(upgraded, replace=True)
        self.assertFalse((Path(update["backup"]) / "PATTERNS.md").exists())
        self.assertEqual(PACKS.resolve("ja", str(self.data))["format_version"], 1)
        self.assertEqual((self.installed() / "PATTERNS.md").read_bytes(), upgraded["PATTERNS.md"])
        self.assertEqual(self.install(upgraded)["status"], "unchanged")
        PACKS.rollback("ja", str(self.data))
        self.assertEqual(PACKS.validate(self.installed())["format_version"], 1)
        self.assertFalse((self.installed() / "PATTERNS.md").exists())
        PACKS.rollback("ja", str(self.data))
        self.assertEqual((self.installed() / "PATTERNS.md").read_bytes(), upgraded["PATTERNS.md"])
        removed = PACKS.remove("ja", str(self.data))
        self.assertEqual((Path(removed["backup"]) / "PATTERNS.md").read_bytes(), upgraded["PATTERNS.md"])
        PACKS.rollback("ja", str(self.data))
        self.assertEqual(PACKS.resolve("ja", str(self.data))["format_version"], 1)
        self.assert_no_stage()

    def test_pack_without_patterns_installs_and_rolls_back(self):
        original = self.files()
        self.install(original)
        self.install(self.files(version="0.2.0"), replace=True)
        PACKS.rollback("ja", str(self.data))
        result = PACKS.resolve("ja", str(self.data))
        self.assertEqual((result["status"], result["version"], result["patterns"]), ("ready", "0.1.0", None))
        self.assert_no_stage()

    def test_pattern_content_updates_and_restores_with_the_pack(self):
        original = self.files()
        original["PATTERNS.md"] = b"Keep the original regional examples.\n"
        self.install(original)
        changed = self.files(version="0.2.0")
        changed["PATTERNS.md"] = b"Updated regional examples and exceptions.\n"
        update = self.install(changed, replace=True)
        self.assertEqual((Path(update["backup"]) / "PATTERNS.md").read_bytes(), original["PATTERNS.md"])
        self.assertEqual((self.installed() / "PATTERNS.md").read_bytes(), changed["PATTERNS.md"])
        PACKS.rollback("ja", str(self.data))
        self.assertEqual(PACKS.validate(self.installed())["format_version"], 1)
        self.assertEqual((self.installed() / "PATTERNS.md").read_bytes(), original["PATTERNS.md"])
        self.assert_no_stage()

    def test_future_format_blocks_fallback_and_install(self):
        self.directory(self.project / ".yaya" / "language-packs", format_version=2)
        self.directory(self.core / "languages")
        result = PACKS.resolve("ja", str(self.data), str(self.project))
        self.assertEqual((result["status"], result["patterns"]), ("incompatible", None))
        self.assertEqual(PACKS.inventory(str(self.data), str(self.project))["packs"][0]["status"], "incompatible")
        with self.assertRaisesRegex(PACKS.PackError, "Incompatible"):
            self.install(self.files(format_version=2))
        self.assertFalse(self.installed().exists())
        self.assert_no_stage()

    def test_pattern_contents_receive_same_text_and_size_checks(self):
        path = self.directory(self.base / "fixtures")
        for invalid in (b"", b" \n", b"hello\0world", b"\xff", b"a" * (PACKS.MAX_FILE + 1)):
            with self.subTest(size=len(invalid)):
                (path / "PATTERNS.md").write_bytes(invalid)
                with self.assertRaises(ValueError):
                    PACKS.validate(path)
                files = self.files()
                files["PATTERNS.md"] = invalid
                with self.assertRaises(ValueError):
                    self.install(files)
                self.assert_no_stage()
                self.assertFalse(self.installed().exists())

    def test_archive_extra_colliding_and_linked_patterns_fail_safely(self):
        self.install()
        valid = self.files()
        valid["PATTERNS.md"] = b"Regular Markdown.\n"
        for name, mode in (
            ("patterns.md", stat.S_IFREG | 0o644),
            ("PATTERNS.md", stat.S_IFREG | 0o644),
            ("detector.json", stat.S_IFREG | 0o644),
            ("../PATTERNS.md", stat.S_IFREG | 0o644),
        ):
            with self.subTest(name=name):
                archive, digest = self.archive(valid, [(name, b"unexpected", mode)])
                with self.assertRaises(PACKS.PackError):
                    PACKS.install(archive, digest, str(self.data), replace=True)
                self.assertEqual(PACKS.validate(self.installed())["format_version"], 1)
                self.assert_no_stage()
        for mode in (stat.S_IFLNK | 0o777, stat.S_IFIFO | 0o644, stat.S_IFDIR | 0o755):
            with self.subTest(mode=mode):
                archive, digest = self.archive(self.files(), [("PATTERNS.md", b"../outside", mode)])
                with self.assertRaises(PACKS.PackError):
                    PACKS.install(archive, digest, str(self.data), replace=True)
                self.assert_no_stage()
                self.assertEqual(PACKS.validate(self.installed())["format_version"], 1)
        self.assertFalse((self.data / "backups").exists())

    def test_semver_prerelease_build_and_ascii_boundaries(self):
        path = self.base / "semver fixture"
        path.mkdir()
        valid = ("0.0.0", "9.8.7-rc.1+publisher.005", "1.2.3-0.3.7", "1.2.3-0A.000a+001.09")
        invalid = ("v1.2.3", "1.2", "01.2.3", "1.2.3-01", "1.2.3-rc..1", "1.2.3+", "1.2.٣", "1.2.3-１２")
        for version in (*valid, *invalid):
            for name, content in self.files(version=version).items():
                (path / name).write_bytes(content)
            with self.subTest(version=version):
                if version in valid:
                    self.assertEqual(PACKS.validate(path)["version"], version)
                else:
                    with self.assertRaises(PACKS.PackError):
                        PACKS.validate(path)

    def test_external_reviewed_pack_lifecycle_with_unicode_and_spaced_paths(self):
        self.data = self.base / "用户 data with spaces"
        identifier = "es-419"
        original = "9.8.7-rc.1+publisher.005"
        newer = "9.8.7+publisher.006"

        def reviewed_files(version):
            files = self.files(identifier, version, quality="reviewed")
            files["REVIEW.md"] = b"Local fixture review evidence.\n"
            return files

        self.assertEqual(self.install(reviewed_files(original))["status"], "installed")
        resolved = PACKS.resolve("ES-419", str(self.data))
        self.assertEqual((resolved["resolved"], resolved["version"], resolved["quality"]), (identifier, original, "reviewed"))
        self.assertEqual(self.install(reviewed_files(original))["status"], "unchanged")
        self.install(reviewed_files(newer), replace=True)
        PACKS.rollback(identifier, str(self.data))
        self.assertEqual(self.version(self.installed(identifier)), original)
        removed = PACKS.remove(identifier, str(self.data))
        self.assertTrue((Path(removed["backup"]) / "REVIEW.md").is_file())
        self.assertEqual(PACKS.resolve(identifier, str(self.data))["status"], "missing")
        PACKS.rollback(identifier, str(self.data))
        self.assertEqual(self.version(self.installed(identifier)), original)
        self.assertEqual(PACKS.inventory(str(self.data))["packs"][0]["id"], identifier)
        self.assertEqual(list(self.core.iterdir()), [])
        self.assert_no_stage()

    def test_empty_binary_invalid_utf8_and_unexpected_files_fail(self):
        path = self.directory(self.base / "fixtures")
        for invalid in (b"", b" \n", b"hello\0world", b"\xff"):
            (path / "GUIDE.md").write_bytes(invalid)
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                PACKS.validate(path)
        (path / "GUIDE.md").write_bytes(b"Guide")
        (path / "script.py").write_bytes(b"print('not allowed')")
        with self.assertRaises(PACKS.PackError):
            PACKS.validate(path)

    def test_install_idempotence_and_explicit_replace(self):
        first = self.install()
        self.assertEqual(first["status"], "installed")
        self.assertIsNone(first["backup"])
        self.assertEqual(self.install()["status"], "unchanged")
        with self.assertRaises(PACKS.PackError):
            self.install(self.files(version="0.2.0"))
        self.assertEqual(self.version(self.installed()), "0.1.0")
        update = self.install(self.files(version="0.2.0"), replace=True)
        self.assertEqual(self.version(Path(update["backup"])), "0.1.0")
        self.assertEqual(self.version(self.installed()), "0.2.0")
        self.assert_no_stage()

    def test_rollback_swaps_current_and_previous_versions(self):
        self.install()
        self.install(self.files(version="0.2.0"), replace=True)
        result = PACKS.rollback("ja", str(self.data))
        self.assertEqual(self.version(self.installed()), "0.1.0")
        self.assertEqual(self.version(Path(result["backup"])), "0.2.0")
        PACKS.rollback("ja", str(self.data))
        self.assertEqual(self.version(self.installed()), "0.2.0")

    def test_remove_is_reversible_and_missing_is_explicit(self):
        self.install()
        removed = PACKS.remove("ja", str(self.data))
        self.assertFalse(self.installed().exists())
        self.assertTrue(Path(removed["backup"]).is_dir())
        self.assertEqual(PACKS.remove("ja", str(self.data))["status"], "missing")
        self.assertEqual(PACKS.rollback("ja", str(self.data))["status"], "restored")
        self.assertEqual(self.version(self.installed()), "0.1.0")
        with self.assertRaises(PACKS.PackError):
            PACKS.rollback("ko", str(self.data))

    def test_wrong_existing_id_blocks_install_remove_and_rollback(self):
        self.install()
        self.install(self.files(version="0.2.0"), replace=True)
        (self.installed() / "pack.json").write_bytes(self.files("ko")["pack.json"])
        operations = [
            lambda: self.install(self.files(version="0.3.0"), replace=True),
            lambda: PACKS.remove("ja", str(self.data)),
            lambda: PACKS.rollback("ja", str(self.data)),
        ]
        for operation in operations:
            with self.subTest(operation=operation), self.assertRaises(PACKS.PackError):
                operation()
            self.assertEqual(json.loads((self.installed() / "pack.json").read_bytes())["id"], "ko")
        self.assert_no_stage()

    def test_project_install_is_separate_from_user_and_core(self):
        archive, digest = self.archive()
        result = PACKS.install(archive, digest, project=str(self.project))
        expected = self.project / ".yaya" / "language-packs" / "ja"
        self.assertEqual(Path(result["path"]), expected)
        self.assertFalse(self.data.exists())
        self.assertFalse((self.core / "languages" / "ja").exists())
        for forbidden in (self.core, self.core / "custom"):
            with self.subTest(forbidden=forbidden), self.assertRaises(PACKS.PackError):
                PACKS.install(archive, digest, data_dir=str(forbidden))

    def test_archive_sha256_and_archive_limit_before_mutation(self):
        archive, digest = self.archive()
        for wrong in ("bad", "0" * 64):
            with self.subTest(wrong=wrong), self.assertRaises(PACKS.PackError):
                PACKS.install(archive, wrong, str(self.data))
        self.assertFalse(self.data.exists())
        huge = self.base / "huge.zip"
        huge.write_bytes(b"x" * (PACKS.MAX_ARCHIVE + 1))
        with self.assertRaises(PACKS.PackError):
            PACKS.install(huge, hashlib.sha256(huge.read_bytes()).hexdigest(), str(self.data))
        self.assertFalse(self.data.exists())
        self.assertEqual(PACKS.install(archive, digest.upper(), str(self.data))["status"], "installed")

    def test_traversal_nested_absolute_and_extra_archive_members_rejected(self):
        unsafe = ["../escape.md", "/escape.md", "C:/escape.md", "..\\escape.md", "nested/GUIDE.md", "README.md"]
        for name in unsafe:
            archive, digest = self.archive(extra=[(name, b"malicious", stat.S_IFREG | 0o644)])
            with self.subTest(name=name), self.assertRaises(PACKS.PackError):
                PACKS.install(archive, digest, str(self.data))
            self.assert_no_stage()
            self.assertFalse(self.installed().exists())
        self.assertFalse((self.base / "escape.md").exists())

    def test_duplicate_and_case_colliding_archive_members_rejected(self):
        for name in ("GUIDE.md", "guide.md"):
            archive, digest = self.archive(extra=[(name, b"duplicate", stat.S_IFREG | 0o644)])
            with self.subTest(name=name), self.assertRaises(PACKS.PackError):
                PACKS.install(archive, digest, str(self.data))
            self.assert_no_stage()

    def test_symlink_and_special_file_archive_members_rejected(self):
        files = self.files()
        files.pop("GUIDE.md")
        for mode in (stat.S_IFLNK | 0o777, stat.S_IFIFO | 0o644, stat.S_IFDIR | 0o755):
            archive, digest = self.archive(files, [("GUIDE.md", b"../../outside", mode)])
            with self.subTest(mode=mode), self.assertRaises(PACKS.PackError):
                PACKS.install(archive, digest, str(self.data))
            self.assert_no_stage()

    def test_uncompressed_member_and_total_size_limits(self):
        files = self.files()
        files["GUIDE.md"] = b"a" * (PACKS.MAX_FILE + 1)
        archive, digest = self.archive(files)
        with self.assertRaises(PACKS.PackError):
            PACKS.install(archive, digest, str(self.data))
        files = self.files()
        for name in ("GUIDE.md", "examples.md", "LICENSE", "REVIEW.md"):
            files[name] = b"a" * PACKS.MAX_FILE
        archive, digest = self.archive(files)
        with self.assertRaises(PACKS.PackError):
            PACKS.install(archive, digest, str(self.data))
        self.assert_no_stage()

    def test_bad_zip_and_invalid_metadata_leave_no_stage_or_install(self):
        bad = self.base / "bad.zip"
        bad.write_bytes(b"Not a ZIP")
        with self.assertRaises(zipfile.BadZipFile):
            PACKS.install(bad, hashlib.sha256(bad.read_bytes()).hexdigest(), str(self.data))
        with self.assertRaises(PACKS.PackError):
            self.install(self.files(format_version=99))
        self.assert_no_stage()
        self.assertFalse(self.installed().exists())

    def test_remote_url_is_not_implicitly_downloaded(self):
        with self.assertRaises(OSError):
            PACKS.install(Path("https://example.invalid/pack.zip"), "0" * 64, str(self.data))
        self.assertFalse(self.data.exists())

    def test_linked_data_root_and_destination_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.link_directory(self.data, outside)
        archive, digest = self.archive()
        with self.assertRaises(PACKS.PackError):
            PACKS.install(archive, digest, str(self.data))
        self.assertEqual(list(outside.iterdir()), [])

    def test_linked_pack_directory_and_backups_rejected(self):
        outside = self.directory(self.base / "outside")
        self.link_directory(self.installed(), outside)
        self.assertEqual(PACKS.resolve("ja", str(self.data))["status"], "invalid")
        with self.assertRaises(PACKS.PackError):
            PACKS.remove("ja", str(self.data))
        self.assertEqual(self.version(outside), "0.1.0")

    def test_linked_empty_resolution_root_is_invalid_not_missing(self):
        outside = self.base / "empty"
        outside.mkdir()
        self.link_directory(self.data / "language-packs", outside)
        self.directory(self.core / "languages", "ja")
        result = PACKS.resolve("ja", str(self.data))
        self.assertEqual((result["status"], result["available"]), ("invalid", False))

    def test_reported_link_guard_blocks_empty_roots_even_without_os_link_support(self):
        # Complement the platform integration test when this host cannot create links.
        flagged_root = self.data / "language-packs"
        self.directory(self.core / "languages", "ja")
        original_is_symlink = Path.is_symlink

        def reports_link(path):
            return path == flagged_root or original_is_symlink(path)

        with mock.patch.object(Path, "is_symlink", reports_link):
            self.assertEqual(PACKS.resolve("ja", str(self.data))["status"], "invalid")
            with self.assertRaises(PACKS.PackError):
                PACKS.inventory(str(self.data))

    def test_file_at_pack_root_is_invalid_not_missing(self):
        self.data.mkdir()
        (self.data / "language-packs").write_bytes(b"not a directory")
        self.directory(self.core / "languages", "ja")
        self.assertEqual(PACKS.resolve("ja", str(self.data))["status"], "invalid")

    def test_linked_backup_directory_prevents_move(self):
        self.install()
        outside = self.base / "backup-target"
        outside.mkdir()
        self.link_directory(self.data / "backups", outside)
        with self.assertRaises(PACKS.PackError):
            PACKS.remove("ja", str(self.data))
        self.assertTrue(self.installed().is_dir())
        self.assertEqual(list(outside.iterdir()), [])

    def test_failed_install_move_restores_previous_pack(self):
        self.install()
        original_rename = Path.rename

        def fail_stage(path, target):
            if path.name.startswith(".stage-"):
                raise OSError("simulated final move failure")
            return original_rename(path, target)

        with mock.patch.object(Path, "rename", fail_stage), self.assertRaises(OSError):
            self.install(self.files(version="0.2.0"), replace=True)
        self.assertEqual(self.version(self.installed()), "0.1.0")
        self.assert_no_stage()

    def test_failed_install_recovery_reports_preserved_backup(self):
        self.install()
        original_rename = Path.rename

        def fail_stage_and_restore(path, target):
            if path.name.startswith(".stage-") or path.parent == self.data / "backups" / "ja":
                raise OSError("simulated move failure")
            return original_rename(path, target)

        with mock.patch.object(Path, "rename", fail_stage_and_restore):
            with self.assertRaises(PACKS.PackError) as raised:
                self.install(self.files(version="0.2.0"), replace=True)
        backups = list((self.data / "backups" / "ja").iterdir())
        self.assertEqual(len(backups), 1)
        self.assertIn(str(backups[0]), str(raised.exception))
        self.assertEqual(self.version(backups[0]), "0.1.0")
        self.assertFalse(self.installed().exists())
        self.assert_no_stage()

    def test_cleanup_failure_preserves_recovery_error_and_paths(self):
        self.install()
        original_rename = Path.rename

        def fail_stage_and_restore(path, target):
            if path.name.startswith(".stage-") or path.parent == self.data / "backups" / "ja":
                raise OSError("simulated move failure")
            return original_rename(path, target)

        with mock.patch.object(Path, "rename", fail_stage_and_restore), mock.patch.object(PACKS.shutil, "rmtree", side_effect=OSError("simulated cleanup failure")):
            with self.assertRaises(PACKS.PackError) as raised:
                self.install(self.files(version="0.2.0"), replace=True)
        backup = next((self.data / "backups" / "ja").iterdir())
        stage = next(self.data.glob(".stage-*"))
        self.assertIn(str(backup), str(raised.exception))
        self.assertIn(str(stage), str(raised.exception))
        self.assertEqual(self.version(backup), "0.1.0")
        self.assertEqual(self.version(stage), "0.2.0")

    def test_stale_stat_cannot_bypass_file_or_archive_read_limit(self):
        archive = self.base / "grown.zip"
        archive.write_bytes(b"x" * (PACKS.MAX_ARCHIVE + 1))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        directory = self.directory(self.base / "fixtures")
        large_file = directory / "GUIDE.md"
        large_file.write_bytes(b"x" * (PACKS.MAX_FILE + 1))
        original_stat = Path.stat

        def stale_size(path, *args, **kwargs):
            result = original_stat(path, *args, **kwargs)
            if path in {archive, large_file}:
                values = {name: getattr(result, name) for name in dir(result) if name.startswith("st_")}
                values["st_size"] = 0
                return SimpleNamespace(**values)
            return result

        with mock.patch.object(Path, "stat", stale_size):
            with self.assertRaisesRegex(PACKS.PackError, "Archive exceeds"):
                PACKS.install(archive, digest, str(self.data))
            with self.assertRaisesRegex(PACKS.PackError, "Invalid file or size"):
                PACKS.validate(directory)
        self.assertFalse(self.data.exists())

    def test_failed_rollback_move_restores_current_pack(self):
        self.install()
        update = self.install(self.files(version="0.2.0"), replace=True)
        restore_source = Path(update["backup"])
        original_rename = Path.rename

        def fail_selected_backup(path, target):
            if path == restore_source:
                raise OSError("simulated rollback move failure")
            return original_rename(path, target)

        with mock.patch.object(Path, "rename", fail_selected_backup), self.assertRaises(OSError):
            PACKS.rollback("ja", str(self.data))
        self.assertEqual(self.version(self.installed()), "0.2.0")
        self.assertEqual(self.version(restore_source), "0.1.0")

    def test_failed_rollback_recovery_reports_preserved_current_pack(self):
        self.install()
        self.install(self.files(version="0.2.0"), replace=True)
        original_rename = Path.rename

        def fail_all_backup_moves(path, target):
            if path.parent == self.data / "backups" / "ja":
                raise OSError("simulated rollback and restore failure")
            return original_rename(path, target)

        with mock.patch.object(Path, "rename", fail_all_backup_moves):
            with self.assertRaises(PACKS.PackError) as raised:
                PACKS.rollback("ja", str(self.data))
        backups = list((self.data / "backups" / "ja").iterdir())
        current_backups = [path for path in backups if self.version(path) == "0.2.0"]
        self.assertEqual(len(current_backups), 1)
        self.assertIn(str(current_backups[0]), str(raised.exception))
        self.assertEqual(len(backups), 2)

    def test_corrupt_latest_backup_is_not_silently_skipped(self):
        self.install()
        update = self.install(self.files(version="0.2.0"), replace=True)
        (Path(update["backup"]) / "GUIDE.md").write_bytes(b"")
        with self.assertRaises(PACKS.PackError):
            PACKS.rollback("ja", str(self.data))
        self.assertEqual(self.version(self.installed()), "0.2.0")

    def test_cli_errors_are_json_and_mutually_exclusive_locations_fail(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "install", str(self.base / "absent.zip"), "--sha256", "0" * 64, "--data-dir", str(self.data)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(json.loads(run.stdout)["status"], "error")
        run = subprocess.run([sys.executable, str(SCRIPT), "remove", "ja", "--data-dir", str(self.data), "--project", str(self.project)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertFalse(self.data.exists())
        self.assertFalse(self.project.exists())


if __name__ == "__main__":
    unittest.main()
