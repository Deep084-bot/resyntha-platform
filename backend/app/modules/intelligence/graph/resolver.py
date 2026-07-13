"""EntityResolver — lightweight name canonicalisation.

Maps variant spellings and aliases to canonical forms so that,
for example, ``"mit"``, ``"MIT"`` and ``"Massachusetts Institute
of Technology"`` are treated as the same institution.

Fuzzy matching (levenshtein, embedding similarity) is intentionally
**not** implemented yet.  The design supports adding it later by
replacing the simple dict lookup with a more sophisticated strategy.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EntityResolver:
    """Canonicalise entity names via configurable alias mappings.

    Parameters
    ----------
    aliases:
        ``{(entity_type, raw_name_lower): canonical_name}``.
        Built-in defaults cover common academic abbreviations.
    """

    aliases: dict[tuple[str, str], str] = field(default_factory=lambda: _DEFAULT_ALIASES.copy())

    def resolve(self, name: str, entity_type: str = "") -> str:
        """Return the canonical form of *name*.

        Applies whitespace trimming, case normalisation, and then
        the alias dictionary.
        """
        cleaned = name.strip()
        if not cleaned:
            return ""
        key = (entity_type, cleaned.lower())
        return self.aliases.get(key, cleaned)

    def add_alias(self, raw: str, canonical: str, entity_type: str = "") -> None:
        """Register a single alias mapping."""
        key = (entity_type, raw.strip().lower())
        self.aliases[key] = canonical


_DEFAULT_ALIASES: dict[tuple[str, str], str] = {
    # ── Institutions ──────────────────────────────────────────
    ("institution", "mit"): "Massachusetts Institute of Technology",
    (
        "institution",
        "massachusetts institute of technology",
    ): "Massachusetts Institute of Technology",  # noqa: E501
    ("institution", "stanford"): "Stanford University",
    ("institution", "stanford university"): "Stanford University",
    ("institution", "uc berkeley"): "UC Berkeley",
    ("institution", "berkeley"): "UC Berkeley",
    ("institution", "university of california berkeley"): "UC Berkeley",
    ("institution", "cmu"): "Carnegie Mellon University",
    ("institution", "carnegie mellon"): "Carnegie Mellon University",
    ("institution", "oxford"): "University of Oxford",
    ("institution", "university of oxford"): "University of Oxford",
    ("institution", "cambridge"): "University of Cambridge",
    ("institution", "university of cambridge"): "University of Cambridge",
    ("institution", "google"): "Google",
    ("institution", "google research"): "Google",
    ("institution", "google brain"): "Google",
    ("institution", "google deepmind"): "Google DeepMind",
    ("institution", "deepmind"): "Google DeepMind",
    ("institution", "microsoft"): "Microsoft",
    ("institution", "microsoft research"): "Microsoft",
    ("institution", "meta"): "Meta",
    ("institution", "meta ai"): "Meta",
    ("institution", "facebook"): "Meta",
    ("institution", "facebook ai research"): "Meta",
    ("institution", "fair"): "Meta",
    ("institution", "openai"): "OpenAI",
    ("institution", "nvidia"): "NVIDIA",
    ("institution", "ibm"): "IBM",
    ("institution", "ibm research"): "IBM",
    ("institution", "amazon"): "Amazon",
    ("institution", "aws"): "Amazon",
    # ── Methodologies ─────────────────────────────────────────
    ("methodology", "transformer"): "Transformer",
    ("methodology", "transformers"): "Transformer",
    ("methodology", "cnn"): "CNN",
    ("methodology", "convolutional neural network"): "CNN",
    ("methodology", "convolutional neural networks"): "CNN",
    ("methodology", "rnn"): "RNN",
    ("methodology", "recurrent neural network"): "RNN",
    ("methodology", "recurrent neural networks"): "RNN",
    ("methodology", "lstm"): "LSTM",
    ("methodology", "long short-term memory"): "LSTM",
    ("methodology", "gpt"): "GPT",
    ("methodology", "bert"): "BERT",
    ("methodology", "diffusion"): "Diffusion",
    ("methodology", "diffusion model"): "Diffusion",
    ("methodology", "diffusion models"): "Diffusion",
    ("methodology", "reinforcement learning"): "Reinforcement Learning",
    ("methodology", "rl"): "Reinforcement Learning",
    ("methodology", "transfer learning"): "Transfer Learning",
    ("methodology", "fine-tuning"): "Fine-tuning",
    ("methodology", "fine tuning"): "Fine-tuning",
    ("methodology", "prompting"): "Prompting",
    ("methodology", "prompt engineering"): "Prompting",
    ("methodology", "few-shot"): "Few-shot Learning",
    ("methodology", "few shot"): "Few-shot Learning",
    ("methodology", "zero-shot"): "Zero-shot Learning",
    ("methodology", "zero shot"): "Zero-shot Learning",
    # ── Datasets ──────────────────────────────────────────────
    ("dataset", "imagenet"): "ImageNet",
    ("dataset", "coco"): "COCO",
    ("dataset", "ms coco"): "COCO",
    ("dataset", "squad"): "SQuAD",
    ("dataset", "squad2"): "SQuAD",
    ("dataset", "glue"): "GLUE",
    ("dataset", "superglue"): "SuperGLUE",
    ("dataset", "mnist"): "MNIST",
    ("dataset", "cifar10"): "CIFAR-10",
    ("dataset", "cifar-10"): "CIFAR-10",
    ("dataset", "cifar100"): "CIFAR-100",
    ("dataset", "cifar-100"): "CIFAR-100",
    ("dataset", "wmt"): "WMT",
    ("dataset", "wikitext"): "WikiText",
    ("dataset", "wikitext103"): "WikiText-103",
    ("dataset", "wikitext-103"): "WikiText-103",
    # ── Technologies ───────────────────────────────────────────
    ("technology", "pytorch"): "PyTorch",
    ("technology", "torch"): "PyTorch",
    ("technology", "tensorflow"): "TensorFlow",
    ("technology", "tf"): "TensorFlow",
    ("technology", "jax"): "JAX",
    ("technology", "huggingface"): "Hugging Face Transformers",
    ("technology", "hugging face"): "Hugging Face Transformers",
    ("technology", "transformers"): "Hugging Face Transformers",
    ("technology", "langchain"): "LangChain",
    ("technology", "cuda"): "CUDA",
    # ── Metrics ────────────────────────────────────────────────
    ("metric", "accuracy"): "Accuracy",
    ("metric", "precision"): "Precision",
    ("metric", "recall"): "Recall",
    ("metric", "f1"): "F1",
    ("metric", "f1 score"): "F1",
    ("metric", "f1-score"): "F1",
    ("metric", "bleu"): "BLEU",
    ("metric", "rouge"): "ROUGE",
    ("metric", "rouge-l"): "ROUGE",
    ("metric", "perplexity"): "Perplexity",
    ("metric", "ppl"): "Perplexity",
    ("metric", "mae"): "MAE",
    ("metric", "mean absolute error"): "MAE",
    ("metric", "rmse"): "RMSE",
    ("metric", "mse"): "MSE",
    ("metric", "mean squared error"): "MSE",
    ("metric", "auc"): "AUC",
    ("metric", "auc-roc"): "AUC",
    ("metric", "map"): "mAP",
    ("metric", "mean average precision"): "mAP",
    ("metric", "ndcg"): "NDCG",
    ("metric", "latency"): "Latency",
    ("metric", "throughput"): "Throughput",
    ("metric", "inference time"): "Latency",
}
