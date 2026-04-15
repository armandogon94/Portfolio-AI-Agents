"""Unit tests for the RAG seeding script (slice-16)."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.mark.unit
class TestSeedRagScript:
    SEEDS_DIR = Path(__file__).parent.parent.parent / "src" / "config" / "seeds"

    def test_all_domain_seed_files_exist(self):
        """Seed YAML files exist for all 6 domains."""
        expected = {"healthcare", "finance", "real_estate", "legal", "education", "engineering"}
        found = {f.stem for f in self.SEEDS_DIR.glob("*.yaml")}
        assert expected <= found, f"Missing seed files: {expected - found}"

    def test_seed_files_have_documents_key(self):
        """Each seed YAML has a 'documents' list."""
        import yaml

        for seed_file in self.SEEDS_DIR.glob("*.yaml"):
            data = yaml.safe_load(seed_file.read_text())
            assert "documents" in data, f"{seed_file.name} missing 'documents' key"
            assert isinstance(data["documents"], list)
            assert len(data["documents"]) > 0, f"{seed_file.name} has no documents"

    def test_each_document_has_required_fields(self):
        """Each seed document has 'id' and 'content' fields."""
        import yaml

        for seed_file in self.SEEDS_DIR.glob("*.yaml"):
            data = yaml.safe_load(seed_file.read_text())
            for doc in data["documents"]:
                assert "id" in doc, f"{seed_file.name}: document missing 'id'"
                assert "content" in doc, f"{seed_file.name}: document missing 'content'"
                assert doc["id"], f"{seed_file.name}: document has empty 'id'"
                assert doc["content"], f"{seed_file.name}: document has empty 'content'"

    def test_seed_domain_calls_repo_add_for_each_doc(self):
        """seed_domain() calls repo.add() for each document in the seed file."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from scripts.seed_rag import seed_domain

        mock_repo = MagicMock()
        count = seed_domain("healthcare", mock_repo)

        assert count > 0
        assert mock_repo.add.call_count == count

    def test_seed_domain_passes_correct_fields(self):
        """seed_domain() calls repo.add with doc_id, content, and metadata."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from scripts.seed_rag import seed_domain

        mock_repo = MagicMock()
        seed_domain("healthcare", mock_repo)

        # Verify each call uses keyword args with correct structure
        for call_args in mock_repo.add.call_args_list:
            kwargs = call_args.kwargs
            assert "doc_id" in kwargs
            assert "content" in kwargs
            assert "metadata" in kwargs

    def test_seed_domain_handles_missing_domain_gracefully(self):
        """seed_domain() returns 0 and does not raise for unknown domain."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from scripts.seed_rag import seed_domain

        mock_repo = MagicMock()
        count = seed_domain("nonexistent_domain", mock_repo)
        assert count == 0
        mock_repo.add.assert_not_called()

    def test_load_seed_documents_returns_list(self):
        """load_seed_documents() returns a non-empty list for valid domains."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from scripts.seed_rag import load_seed_documents

        for domain in ["healthcare", "finance", "legal", "education", "engineering", "real_estate"]:
            docs = load_seed_documents(domain)
            assert isinstance(docs, list)
            assert len(docs) > 0, f"No seed documents for domain '{domain}'"
