"""Tests for knowledge extraction: output schema, normalisation, and validation.

All tests are pure-unit — no DB, no LLM calls.
"""

import uuid

from pydantic import ValidationError
import pytest

from app.modules.extraction.domain.knowledge import (
    Author,
    Dataset,
    ExtractionOutput,
    Institution,
    Metric,
    PaperKnowledge,
    Technology,
)
from app.modules.extraction.utils.normalization import ExtractionNormalizer
from app.modules.extraction.utils.validation import ExtractionValidator


# ── ExtractionOutput schema ──────────────────────────────────────

class TestExtractionOutput:
    """Validates the output Pydantic schema."""

    def test_minimal_output(self) -> None:
        """All fields should have sensible defaults."""
        output = ExtractionOutput()
        assert output.research_questions == []
        assert output.key_findings == []
        assert output.methodology is None
        assert output.limitations == []
        assert output.key_contributions == []
        assert output.relevant_techniques == []
        assert output.cited_works == []
        assert output.future_work == []
        assert output.summary == ""
        assert output.authors == []
        assert output.institutions == []
        assert output.datasets_used == []
        assert output.technologies == []
        assert output.evaluation_metrics == []
        assert output.research_domains == []
        assert output.keywords == []
        assert output.paper_type is None
        assert output.funding is None

    def test_full_output(self) -> None:
        """All fields populate correctly."""
        output = ExtractionOutput(
            research_questions=["RQ1"],
            key_findings=["Finding 1"],
            methodology="Survey",
            limitations=["Small sample"],
            key_contributions=["Novel method"],
            relevant_techniques=["CNNs"],
            cited_works=["Smith 2020"],
            future_work=["Scale up"],
            summary="A paper about X.",
            authors=[Author(name="John A. Smith", order=1, is_corresponding=True)],
            institutions=[Institution(name="MIT", department="CS", country="USA")],
            datasets_used=[Dataset(name="ImageNet", is_public=True, is_benchmark=True)],
            technologies=[Technology(name="PyTorch", type="framework")],
            evaluation_metrics=[Metric(name="accuracy", value="92.5%", dataset="ImageNet")],
            research_domains=["Computer Vision"],
            keywords=["deep learning", "classification"],
            paper_type="benchmark",
            funding="NSF grant 1234",
        )
        assert len(output.authors) == 1
        assert output.authors[0].name == "John A. Smith"
        assert output.authors[0].order == 1
        assert output.authors[0].is_corresponding is True
        assert output.institutions[0].name == "MIT"
        assert output.datasets_used[0].name == "ImageNet"
        assert output.technologies[0].name == "PyTorch"
        assert output.evaluation_metrics[0].name == "accuracy"
        assert output.paper_type == "benchmark"
        assert output.funding == "NSF grant 1234"

    def test_author_validation(self) -> None:
        """Author model validates correctly."""
        with pytest.raises(ValidationError):
            Author()  # name is required
        author = Author(name="Alice B. Wonderland")
        assert author.order is None
        assert author.is_corresponding is None


# ── Author extraction ───────────────────────────────────────────

class TestAuthorExtraction:
    """Tests for author name extraction and normalisation."""

    def test_normalize_full_name(self) -> None:
        assert ExtractionNormalizer.normalize_author("John A. Smith") == "John A. Smith"

    def test_normalize_last_first(self) -> None:
        assert ExtractionNormalizer.normalize_author("Smith, John A.") == "John A. Smith"

    def test_normalize_last_first_no_middle(self) -> None:
        assert ExtractionNormalizer.normalize_author("Smith, John") == "John Smith"

    def test_normalize_empty_string(self) -> None:
        assert ExtractionNormalizer.normalize_author("") == ""

    def test_normalize_whitespace(self) -> None:
        assert ExtractionNormalizer.normalize_author("  Smith, John  ") == "John Smith"


# ── Institution extraction ──────────────────────────────────────

class TestInstitutionExtraction:
    """Tests for institution name extraction and normalisation."""

    def test_normalize_full_name(self) -> None:
        result = ExtractionNormalizer.normalize_institution("Stanford University")
        assert result == "Stanford University"

    def test_normalize_alias_mit(self) -> None:
        result = ExtractionNormalizer.normalize_institution("MIT")
        assert result == "Massachusetts Institute of Technology"

    def test_normalize_alias_eth(self) -> None:
        result = ExtractionNormalizer.normalize_institution("ETH Zurich")
        assert result == "ETH Zurich"

    def test_normalize_alias_ethz(self) -> None:
        result = ExtractionNormalizer.normalize_institution("ETHZ")
        assert result == "ETH Zurich"

    def test_normalize_case_insensitive(self) -> None:
        result = ExtractionNormalizer.normalize_institution("mit")
        assert result == "Massachusetts Institute of Technology"


# ── Dataset extraction ──────────────────────────────────────────

class TestDatasetExtraction:
    """Tests for dataset name extraction and normalisation."""

    def test_normalize_imagenet(self) -> None:
        result = ExtractionNormalizer.normalize_dataset("imagenet")
        assert result == "ImageNet"

    def test_normalize_cifar10(self) -> None:
        result = ExtractionNormalizer.normalize_dataset("CIFAR-10")
        assert result == "CIFAR-10"

    def test_normalize_coco(self) -> None:
        result = ExtractionNormalizer.normalize_dataset("MS COCO")
        assert result == "COCO"

    def test_normalize_unknown(self) -> None:
        result = ExtractionNormalizer.normalize_dataset("MyCustomDataset2024")
        assert result == "MyCustomDataset2024"


# ── Technology extraction ───────────────────────────────────────

class TestTechnologyExtraction:
    """Tests for technology name extraction and normalisation."""

    def test_normalize_pytorch(self) -> None:
        result = ExtractionNormalizer.normalize_technology("pytorch")
        assert result == "PyTorch"

    def test_normalize_tensorflow(self) -> None:
        result = ExtractionNormalizer.normalize_technology("tensorflow")
        assert result == "TensorFlow"

    def test_normalize_transformers(self) -> None:
        result = ExtractionNormalizer.normalize_technology("transformers")
        assert result == "Transformers (Hugging Face)"

    def test_normalize_unknown(self) -> None:
        result = ExtractionNormalizer.normalize_technology("SomeNewFramework")
        assert result == "SomeNewFramework"


# ── Normalization ───────────────────────────────────────────────

class TestNormalization:
    """General normalisation tests."""

    def test_duplicate_removal_via_canonical(self) -> None:
        """Same entity spelled differently should resolve to same canonical form."""
        assert ExtractionNormalizer.normalize_dataset("imagenet") == ExtractionNormalizer.normalize_dataset("ImageNet")

    def test_institution_alias_equivalence(self) -> None:
        assert ExtractionNormalizer.normalize_institution("MIT") == ExtractionNormalizer.normalize_institution("mit")


# ── Validation ──────────────────────────────────────────────────

class TestValidation:
    """Validation logic tests."""

    def test_reject_empty_string(self) -> None:
        assert ExtractionValidator.is_valid_entity_name("") is False

    def test_reject_whitespace_only(self) -> None:
        assert ExtractionValidator.is_valid_entity_name("   ") is False

    def test_reject_single_char(self) -> None:
        assert ExtractionValidator.is_valid_entity_name(".") is False

    def test_reject_placeholder(self) -> None:
        assert ExtractionValidator.is_valid_entity_name("unknown") is False
        assert ExtractionValidator.is_valid_entity_name("n/a") is False
        assert ExtractionValidator.is_valid_entity_name("TBD") is False

    def test_reject_numeric_only(self) -> None:
        assert ExtractionValidator.is_valid_entity_name("12345") is False

    def test_reject_special_only(self) -> None:
        assert ExtractionValidator.is_valid_entity_name("!@#$%") is False

    def test_accept_valid_name(self) -> None:
        assert ExtractionValidator.is_valid_entity_name("ImageNet") is True
        assert ExtractionValidator.is_valid_entity_name("BERT") is True

    def test_confidence_score_author(self) -> None:
        score = ExtractionValidator.confidence_score("author", "John A. Smith")
        assert 0.5 < score <= 1.0

    def test_confidence_score_institution(self) -> None:
        score = ExtractionValidator.confidence_score("institution", "Stanford University")
        assert 0.5 < score <= 1.0

    def test_confidence_score_low_for_short(self) -> None:
        score = ExtractionValidator.confidence_score("dataset", "AB")
        assert score < 0.7

    def test_confidence_score_zero_for_invalid(self) -> None:
        score = ExtractionValidator.confidence_score("author", "")
        assert score == 0.0

    def test_filter_valid_entities_strings(self) -> None:
        entities = ["PyTorch", "unknown", "TensorFlow", "", "A"]
        result = ExtractionValidator.filter_valid_entities(entities, "technology")
        assert len(result) == 2  # PyTorch and TensorFlow
        assert all(e["name"] in ("PyTorch", "TensorFlow") for e in result)

    def test_filter_valid_entities_dicts(self) -> None:
        entities = [
            {"name": "Stanford University", "country": "USA"},
            {"name": ""},
            {"name": "n/a"},
        ]
        result = ExtractionValidator.filter_valid_entities(entities, "institution")
        assert len(result) == 1
        assert result[0]["name"] == "Stanford University"

    def test_max_name_length(self) -> None:
        long_name = "A" * 201
        assert ExtractionValidator.is_valid_entity_name(long_name) is False


# ── PaperKnowledge ──────────────────────────────────────────────

class TestPaperKnowledge:
    """PaperKnowledge wrapper tests."""

    def test_minimal(self) -> None:
        pk = PaperKnowledge(
            paper_id=uuid.uuid4(),
            paper_title="Test Paper",
            extraction=ExtractionOutput(),
            model_used="gpt-4",
        )
        assert pk.paper_title == "Test Paper"
        assert pk.confidence_score is None
