import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lifetrace_archive", ROOT / "scripts" / "archive.py")
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / "examples" / "fictional-profile.json").read_text(encoding="utf-8"))

    def test_fixture_and_candidate_rejection(self):
        archive.validate(self.fixture)
        invalid = copy.deepcopy(self.fixture)
        invalid["entries"][0]["status"] = "candidate"
        with self.assertRaises(ValueError):
            archive.validate(invalid)

    def test_confirmation_required_and_add(self):
        class Args:
            confirmed = False
            kind = "reflection"
            title = "新的节奏"
            content = "我开始享受每天的步行。"
            when_date = None
            when_text = None
            source_type = "subject"
            source_ref = "虚构访谈"
            visibility = "private"

        with self.assertRaises(ValueError):
            archive.add(copy.deepcopy(self.fixture), Args())
        Args.confirmed = True
        updated = archive.add(copy.deepcopy(self.fixture), Args())
        self.assertEqual(len(updated["entries"]), 2)
        self.assertEqual(updated["revision"], 2)
        archive.validate(updated)

    def test_merge_keeps_deletion_against_old_export(self):
        old = copy.deepcopy(self.fixture)
        deleted = archive.delete(copy.deepcopy(old), old["entries"][0]["id"], "人物要求删除")
        merged = archive.merge(old, deleted)
        self.assertEqual(merged["entries"], [])
        self.assertEqual(len(merged["tombstones"]), 1)

    def test_merge_rejects_conflicts_and_other_person(self):
        other = copy.deepcopy(self.fixture)
        other["entries"][0]["content"] = "不同叙述"
        with self.assertRaisesRegex(ValueError, "entry conflict"):
            archive.merge(self.fixture, other)
        other["archive_id"] = "9ea54549-1cab-4a7c-88fb-779e316e6c66"
        with self.assertRaisesRegex(ValueError, "archive IDs differ"):
            archive.merge(self.fixture, other)

    def test_file_roundtrip_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "archive.json"
            archive.write(target, self.fixture)
            self.assertEqual(archive.read(target), self.fixture)
            with self.assertRaisesRegex(ValueError, "output exists"):
                archive.write(target, self.fixture)


if __name__ == "__main__":
    unittest.main()
