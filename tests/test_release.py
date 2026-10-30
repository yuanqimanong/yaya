"""Build real release archives and check the portable delivery contract."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACK_FILES = {"pack.json", "GUIDE.md", "examples.md", "LICENSE"}


class ReleaseBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep generated artifacts outside tests/ and every copied source tree.
        cls.temporary = tempfile.TemporaryDirectory(prefix=".release test ", dir=ROOT)
        cls.scratch = Path(cls.temporary.name).resolve()
        if cls.scratch.parent != ROOT:
            raise RuntimeError("Test temporary directory escaped the repository")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.source = cls.scratch / "source with spaces"
        for name in ("scripts", "core", "language-packs", "templates"):
            shutil.copytree(ROOT / name, cls.source / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        cls.builder = cls.source / "scripts" / "build_release.py"
        cls.core_source = cls.source / "core" / "yaya"
        # Deliberate local development files must never become runtime assets.
        for name in ("evals/should-not-ship.txt", ".pytest_cache/should-not-ship.txt", "__pycache__/stale.pyc"):
            sentinel = cls.core_source / name
            sentinel.parent.mkdir(parents=True, exist_ok=True)
            sentinel.write_bytes(b"release-test-sentinel\n")
        cls.first = cls.scratch / "artifacts first"
        cls.second = cls.scratch / "artifacts second"
        for destination in (cls.first, cls.second):
            result = cls.run_script(cls.builder, "--output", destination)
            if result.returncode:
                raise RuntimeError(f"Release build failed: {result.stderr}\n{result.stdout}")
        cls.catalog = json.loads((cls.first / "catalog.json").read_text(encoding="utf-8"))
        cls.core_asset = cls.catalog["core"]
        cls.assets = [cls.core_asset, *cls.catalog["language_packs"]]

    @classmethod
    def run_script(cls, script, *arguments):
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            [sys.executable, str(script), *(str(arg) for arg in arguments)],
            cwd=cls.scratch,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )

    def read_core_names(self):
        with zipfile.ZipFile(self.first / self.core_asset["file"]) as archive:
            return archive.namelist()

    def unpack_core(self, directory):
        with zipfile.ZipFile(self.first / self.core_asset["file"]) as archive:
            for name in archive.namelist():
                path = PurePosixPath(name)
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
            archive.extractall(directory)
        return directory / "yaya"

    def test_core_has_only_bundled_languages_and_runtime_files(self):
        names = self.read_core_names()
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(name.startswith("yaya/") for name in names))
        required = {
            "yaya/SKILL.md", "yaya/LICENSE", "yaya/version.json",
            "yaya/scripts/packs.py", "yaya/scripts/check_comments.py",
            "yaya/scripts/detect_tells.py", "yaya/scripts/check_rewrite.py",
            "yaya/scripts/prose_scan.py", "yaya/scripts/tell_rules.json",
            "yaya/scripts/check_docstrings.py", "yaya/scripts/edit_evidence.py",
            "yaya/agents/openai.yaml", "yaya/references/text.md",
            "yaya/references/comments.md", "yaya/references/prompts.md",
            "yaya/references/style-learning.md", "yaya/references/language-packs.md",
            "yaya/references/humanize.md",
            "yaya/references/engineering.md", "yaya/references/validation.md", "yaya/references/authorship.md",
            "yaya/languages/en/PATTERNS.md", "yaya/languages/zh-Hans/PATTERNS.md",
            "yaya/catalog.json", "yaya/scripts/yaya.py", "yaya/references/commands.md",
            "yaya/references/domains.md", "yaya/references/verify.md",
            "yaya/references/check.md", "yaya/references/scan.md",
            *{f"yaya/references/domains/{name}.md" for name in ("tech", "finance", "data", "academic", "business")},
        }
        self.assertTrue(required <= set(names))
        languages = {PurePosixPath(name).parts[2] for name in names if name.startswith("yaya/languages/")}
        self.assertEqual(languages, {"zh-Hans", "en"})
        forbidden = {"evals", "tests", "templates", "language-packs", "__pycache__", ".pytest_cache", ".git"}
        for name in names:
            with self.subTest(member=name):
                self.assertFalse(forbidden.intersection(PurePosixPath(name).parts))
                self.assertFalse(name.endswith(".pyc"))
                self.assertNotIn("should-not-ship", name)
        self.assertEqual(set(self.core_asset["bundled_languages"]), languages)

    def test_optional_archives_are_flat_valid_and_compatible(self):
        records = self.catalog["language_packs"]
        expected_ids = {path.name for path in (self.source / "language-packs").iterdir() if path.is_dir()}
        self.assertEqual({item["id"] for item in records}, expected_ids)
        validator = self.core_source / "scripts" / "packs.py"
        core_version = json.loads((self.core_source / "version.json").read_text(encoding="utf-8"))
        for item in records:
            with self.subTest(language=item["id"]):
                destination = self.scratch / "validate optional" / item["id"]
                with zipfile.ZipFile(self.first / item["file"]) as archive:
                    names = set(archive.namelist())
                    self.assertTrue(PACK_FILES <= names <= PACK_FILES | {"REVIEW.md", "PATTERNS.md"})
                    self.assertEqual(len(archive.namelist()), len(names))
                    if item["quality"] == "reviewed":
                        self.assertIn("REVIEW.md", names)
                    self.assertTrue(all("/" not in n and "\\" not in n for n in archive.namelist()))
                    self.assertTrue(all(not member.is_dir() for member in archive.infolist()))
                    self.assertIn(b"MIT License", archive.read("LICENSE"))
                    archive.extractall(destination)
                checked = self.run_script(validator, "validate", destination)
                self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
                metadata = json.loads(checked.stdout)["pack"]
                self.assertEqual(metadata["id"], item["id"])
                self.assertEqual(metadata["core_major"], core_version["core_major"])
                self.assertEqual(metadata["format_version"], core_version["pack_format"])
                for key, value in metadata.items():
                    self.assertEqual(item[key], value)

    def test_catalog_and_checksums_match_actual_bytes(self):
        self.assertEqual(self.catalog["catalog_version"], 1)
        expected_files = {"catalog.json", "SHA256SUMS", *(item["file"] for item in self.assets)}
        self.assertEqual({path.name for path in self.first.iterdir()}, expected_files)
        expected_checksums = {}
        for item in self.assets:
            with self.subTest(asset=item["file"]):
                content = (self.first / item["file"]).read_bytes()
                digest = hashlib.sha256(content).hexdigest()
                self.assertEqual(item["sha256"], digest)
                self.assertEqual(item["bytes"], len(content))
                expected_checksums[item["file"]] = digest
        checksum_lines = (self.first / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        actual_checksums = {}
        for line in checksum_lines:
            digest, name = line.split("  ", 1)
            self.assertNotIn(name, actual_checksums)
            actual_checksums[name] = digest
        self.assertEqual(actual_checksums, expected_checksums)

    def test_repeated_builds_have_identical_bytes(self):
        first_files = {path.name for path in self.first.iterdir()}
        self.assertEqual(first_files, {path.name for path in self.second.iterdir()})
        for name in first_files:
            with self.subTest(asset=name):
                self.assertEqual((self.first / name).read_bytes(), (self.second / name).read_bytes())

    def test_moved_core_resolves_bundled_languages_from_paths_with_spaces(self):
        core = self.unpack_core(self.scratch / "unpacked before move")
        moved = self.scratch / "relocated runtime with spaces" / "yaya"
        moved.parent.mkdir(parents=True)
        core.rename(moved)
        resolver = moved / "scripts" / "packs.py"
        for language in ("zh-Hans", "en"):
            with self.subTest(language=language):
                run = self.run_script(
                    resolver, "resolve", "--language", language,
                    "--data-dir", self.scratch / "empty user data",
                    "--project", self.scratch / "empty project",
                )
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                result = json.loads(run.stdout)
                self.assertEqual(result["status"], "ready")
                self.assertEqual(result["source"], "bundled")
                self.assertEqual(result["resolved"], language)
                self.assertEqual(Path(result["path"]), (moved / "languages" / language).resolve())
                self.assertTrue(Path(result["guide"]).is_file())
                self.assertTrue(Path(result["examples"]).is_file())
                self.assertTrue(Path(result["patterns"]).is_file())
                self.assertEqual(Path(result["patterns"]).parent, (moved / "languages" / language).resolve())
                self.assertEqual(result["format_version"], 1)

    def test_portable_new_tool_entrypoints_load_from_relocated_release(self):
        core = self.unpack_core(self.scratch / "tool relocation")
        before = self.scratch / "portable before.md"
        after = self.scratch / "portable after.md"
        before.write_text("Keep `retry_limit` at 2.\n", encoding="utf-8")
        after.write_text("Leave `retry_limit` at 2.\n", encoding="utf-8")
        detected = self.run_script(core / "scripts" / "detect_tells.py", before, "--language", "en")
        self.assertEqual(detected.returncode, 0, detected.stdout + detected.stderr)
        self.assertEqual(json.loads(detected.stdout)["status"], "ok")
        plan_run = self.run_script(core / "scripts/yaya.py", "scan", "--file", before, "--lang", "en")
        self.assertEqual(plan_run.returncode, 0, plan_run.stderr)
        plan = json.loads(plan_run.stdout)
        self.assertEqual(Path(plan["scanner"]["script"]), (core / "scripts/detect_tells.py").resolve())
        scanned = self.run_script(Path(plan["scanner"]["script"]), *plan["scanner"]["args"])
        self.assertEqual(json.loads(scanned.stdout)["status"], "ok")
        checked = self.run_script(core / "scripts" / "check_rewrite.py", before, after)
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertEqual(json.loads(checked.stdout)["status"], "passed")
        after.write_text("Leave `retry_limit` at 3.\n", encoding="utf-8")
        changed_number = self.run_script(core / "scripts" / "check_rewrite.py", before, after)
        self.assertEqual(changed_number.returncode, 1, changed_number.stdout + changed_number.stderr)
        self.assertEqual(json.loads(changed_number.stdout)["status"], "failed")

    def test_contribution_template_is_not_published(self):
        self.assertTrue((self.source / "templates" / "language-pack" / "pack.json").is_file())
        if not (self.source / "language-packs" / "fr").exists():
            self.assertNotIn("fr", {item["id"] for item in self.catalog["language_packs"]})
            self.assertFalse(any("yaya-lang-fr-" in path.name for path in self.first.iterdir()))
        self.assertFalse(any("/templates/" in name or "/languages/fr/" in name for name in self.read_core_names()))

    def test_command_help_and_domain_routing_work_in_relocated_release(self):
        core = self.unpack_core(self.scratch / "command relocation")
        script = core / "scripts/yaya.py"
        help_result = self.run_script(script, "--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("polish", help_result.stdout)
        version = self.run_script(script, "--version", "--json")
        self.assertEqual(version.returncode, 0, version.stderr)
        self.assertEqual(json.loads(version.stdout)["version"], self.core_asset["version"])
        comparison = self.run_script(script, "check", "--before", "old.md", "--after", "new.md")
        self.assertEqual(comparison.returncode, 0, comparison.stderr)
        self.assertEqual(json.loads(comparison.stdout)["scope"], "mechanical-prose")
        plan = self.run_script(script, "polish", "--domain", "finance")
        self.assertEqual(plan.returncode, 0, plan.stderr)
        resolved = json.loads(plan.stdout)
        self.assertEqual(resolved["domain"]["id"], "finance")
        self.assertTrue(all(Path(ref).is_relative_to(core) for ref in resolved["references"]))
        self.assertTrue(all(Path(ref).is_file() for ref in resolved["references"]))

    def test_output_cannot_escape_into_sources_through_dotdot(self):
        # An existing parent makes this a real filesystem alias on every platform.
        alias_parent = self.source / "unused output"
        alias_parent.mkdir()
        output = alias_parent / ".." / "core" / "yaya"
        source_catalog = (self.core_source / "catalog.json").read_bytes()
        run = self.run_script(self.builder, "--output", output)
        self.assertNotEqual(run.returncode, 0, "Builder accepted an output alias into the core source")
        self.assertFalse(any(self.core_source.glob("*.zip")))
        self.assertEqual((self.core_source / "catalog.json").read_bytes(), source_catalog)

    def test_output_cannot_target_core_source_parent(self):
        output = self.source / "core"
        run = self.run_script(self.builder, "--output", output)
        self.assertNotEqual(run.returncode, 0, "Builder accepted the core source parent as output")
        self.assertFalse(any(output.glob("*.zip")))
        self.assertFalse((output / "catalog.json").exists())

    def test_invalid_core_version_metadata_fails_before_creating_output(self):
        source = self.scratch / "invalid version source"
        shutil.copytree(self.source, source)
        version_path = source / "core" / "yaya" / "version.json"
        baseline = json.loads(version_path.read_text(encoding="utf-8"))
        cases = [
            {**baseline, "pack_format": True},
            {**baseline, "core_major": False},
            {**baseline, "pack_format": 1.0},
            {**baseline, "pack_format": 2},
            {**baseline, "core_major": 0.0},
            {**baseline, "version": None},
            {**baseline, "version": "0.1.0-01"},
            {**baseline, "core_major": 1},
            {key: value for key, value in baseline.items() if key != "version"},
            [baseline],
        ]
        texts = [json.dumps(case) for case in cases]
        texts.append('{"version":"0.1.0","version":"0.2.0","pack_format":1,"core_major":0}')
        for index, text in enumerate(texts):
            with self.subTest(metadata=text):
                version_path.write_text(text, encoding="utf-8")
                output = self.scratch / f"invalid version output {index}"
                run = self.run_script(source / "scripts" / "build_release.py", "--output", output)
                self.assertNotEqual(run.returncode, 0)
                self.assertNotIn("Traceback", run.stderr)
                self.assertFalse(output.exists())

    def test_new_reviewed_language_pack_builds_and_installs_without_core_changes(self):
        source = self.scratch / "extended source"
        shutil.copytree(self.source, source)
        identifier = "sr-Latn-RS"
        package = source / "language-packs" / identifier
        package.mkdir()
        for name in PACK_FILES:
            shutil.copyfile(source / "templates" / "language-pack" / name, package / name)
        meta_path = package / "pack.json"
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        metadata.update(id=identifier, version="9.8.7-rc.1+publisher.005", quality="reviewed")
        meta_path.write_text(json.dumps(metadata), encoding="utf-8")
        (package / "REVIEW.md").write_text("Local test fixture review evidence.\n", encoding="utf-8")
        output = self.scratch / "extended output"
        run = self.run_script(source / "scripts" / "build_release.py", "--output", output)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        catalog = json.loads(run.stdout)
        asset = next(item for item in catalog["language_packs"] if item["id"] == identifier)
        self.assertEqual(asset["version"], metadata["version"])
        with zipfile.ZipFile(output / asset["file"]) as archive:
            self.assertEqual(set(archive.namelist()), PACK_FILES | {"REVIEW.md"})
        data = self.scratch / "external data with spaces"
        helper = self.core_source / "scripts" / "packs.py"
        installed = self.run_script(
            helper, "install", output / asset["file"], "--sha256", asset["sha256"], "--data-dir", data,
        )
        self.assertEqual(installed.returncode, 0, installed.stdout + installed.stderr)
        resolved = self.run_script(helper, "resolve", "--language", identifier + "-1994", "--data-dir", data)
        self.assertEqual(resolved.returncode, 0, resolved.stdout + resolved.stderr)
        result = json.loads(resolved.stdout)
        self.assertEqual((result["resolved"], result["source"], result["quality"]), (identifier, "user", "reviewed"))
        self.assertIsNone(result["patterns"])
        self.assertFalse((self.core_source / "languages" / identifier).exists())

    def test_build_rejects_unrecognized_pack_format_before_creating_output(self):
        source = self.scratch / "unsupported format source"
        shutil.copytree(self.source, source)
        package = source / "language-packs" / "fr"
        package.mkdir()
        for name in PACK_FILES:
            shutil.copyfile(source / "templates" / "language-pack" / name, package / name)
        metadata_path = package / "pack.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata.update(format_version=2, id="fr", version="0.2.0")
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        output = self.scratch / "unsupported format release"
        run = self.run_script(source / "scripts" / "build_release.py", "--output", output)
        self.assertNotEqual(run.returncode, 0)
        self.assertNotIn("Traceback", run.stderr)
        self.assertFalse(output.exists())

    def test_missing_required_runtime_file_fails_before_creating_output(self):
        source = self.scratch / "incomplete runtime source"
        shutil.copytree(self.source, source)
        missing = source / "core" / "yaya" / "scripts" / "tell_rules.json"
        missing.unlink()
        output = self.scratch / "incomplete runtime output"
        run = self.run_script(source / "scripts" / "build_release.py", "--output", output)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("Required runtime file missing", run.stderr)
        self.assertFalse(output.exists())

    def test_invalid_command_default_prevents_release(self):
        source = self.scratch / "bad command catalog"
        shutil.copytree(self.source, source)
        path = source / "core/yaya/catalog.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        catalog["options"]["focus"]["default"] = "unsupported"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        output = self.scratch / "bad catalog output"
        run = self.run_script(source / "scripts/build_release.py", "--output", output)
        self.assertEqual(run.returncode, 1)
        self.assertIn("options.focus.default", run.stderr)
        self.assertNotIn("Traceback", run.stderr)
        self.assertFalse(output.exists())

    def test_skill_and_archive_versions_must_agree(self):
        source = self.scratch / "skill version source"
        shutil.copytree(self.source, source)
        path = source / "core/yaya/SKILL.md"
        original = path.read_text(encoding="utf-8")
        current = self.core_asset["version"]
        declaration = f'  version: "{current}"'
        self.assertIn(declaration, original)
        for index, replacement in enumerate(('  version: "99.0.0"',
                                               '  release: "' + current + '"',
                                               declaration + "\n" + declaration)):
            with self.subTest(replacement=replacement):
                path.write_text(original.replace(declaration, replacement), encoding="utf-8")
                output = self.scratch / f"mismatched skill output {index}"
                run = self.run_script(source / "scripts/build_release.py", "--output", output)
                self.assertEqual(run.returncode, 1)
                self.assertIn("SKILL.md", run.stderr)
                self.assertNotIn("Traceback", run.stderr)
                self.assertFalse(output.exists())

    def test_invalid_tell_rule_prevents_release(self):
        source = self.scratch / "bad tell rules"
        shutil.copytree(self.source, source)
        path = source / "core/yaya/scripts/tell_rules.json"
        rules = json.loads(path.read_text(encoding="utf-8"))
        rules["rules"][0]["severity"] = "P3"
        path.write_text(json.dumps(rules), encoding="utf-8")
        output = self.scratch / "bad tell output"
        run = self.run_script(source / "scripts/build_release.py", "--output", output)
        self.assertEqual(run.returncode, 1)
        self.assertIn("severity", run.stderr)
        self.assertNotIn("Traceback", run.stderr)
        self.assertFalse(output.exists())

    def test_existing_output_links_do_not_overwrite_their_targets(self):
        for index, filename in enumerate((self.core_asset["file"], "catalog.json", "SHA256SUMS")):
            with self.subTest(filename=filename):
                destination = self.scratch / f"linked output {index}"
                destination.mkdir()
                target = self.scratch / f"unrelated file {index}.txt"
                original = b"This unrelated file must remain unchanged.\n"
                target.write_bytes(original)
                try:
                    (destination / filename).symlink_to(target)
                except (OSError, NotImplementedError) as error:
                    self.skipTest(f"This host cannot create symbolic links: {error}")
                run = self.run_script(self.builder, "--output", destination)
                self.assertNotEqual(run.returncode, 0, "Builder followed an existing output link")
                self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
