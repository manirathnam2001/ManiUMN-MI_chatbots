"""Test suite for email_queue.EmailQueue."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from email_queue import EmailQueue


class TestEmailQueueRemove(unittest.TestCase):
    """Tests for EmailQueue.remove() — the path the recent fix targeted."""

    def setUp(self):
        self.queue_dir = tempfile.mkdtemp()
        self.queue = EmailQueue(queue_dir=self.queue_dir)

    def tearDown(self):
        shutil.rmtree(self.queue_dir, ignore_errors=True)

    def _add_entry(self, name: str = "alice") -> str:
        return self.queue.add(
            pdf_data=b"%PDF-1.4 test",
            filename=f"{name}.pdf",
            recipient="box@example.com",
            student_name=name,
            session_type="OHI",
        )

    def test_remove_existing_entry_returns_true_and_drops_it(self):
        entry_id = self._add_entry()
        self.assertEqual(self.queue.get_queue_size(), 1)

        self.assertTrue(self.queue.remove(entry_id))
        self.assertEqual(self.queue.get_queue_size(), 0)

    def test_remove_unknown_entry_returns_false_and_keeps_queue(self):
        entry_id = self._add_entry()

        self.assertFalse(self.queue.remove("nonexistent-id"))
        self.assertEqual(self.queue.get_queue_size(), 1)
        self.assertEqual(self.queue.get_pending()[0]["id"], entry_id)

    def test_remove_deletes_associated_pdf_file(self):
        entry_id = self._add_entry()
        pdf_path = Path(self.queue.get_pending()[0]["pdf_path"])
        self.assertTrue(pdf_path.exists())

        self.queue.remove(entry_id)
        self.assertFalse(pdf_path.exists())

    def test_remove_loads_queue_file_only_once(self):
        """Regression: previous version called _load() twice per remove()."""
        entry_id = self._add_entry()

        original_load = EmailQueue._load
        with patch.object(EmailQueue, "_load", autospec=True, side_effect=original_load) as spy:
            self.queue.remove(entry_id)

        self.assertEqual(spy.call_count, 1)

    def test_remove_only_drops_target_entry(self):
        keep_id = self._add_entry("alice")
        drop_id = self._add_entry("bob")

        self.queue.remove(drop_id)

        remaining = self.queue.get_pending()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["id"], keep_id)

    def test_remove_tolerates_entry_without_pdf_path(self):
        entry_id = self._add_entry()
        # Simulate a legacy/corrupt entry by stripping pdf_path on disk.
        queue_file = Path(self.queue_dir) / EmailQueue.QUEUE_FILE
        with open(queue_file, "r") as f:
            data = json.load(f)
        for entry in data:
            entry.pop("pdf_path", None)
        with open(queue_file, "w") as f:
            json.dump(data, f)

        self.assertTrue(self.queue.remove(entry_id))
        self.assertEqual(self.queue.get_queue_size(), 0)


if __name__ == "__main__":
    unittest.main()
