"""Normalization utilities for extracted entities.

Handles normalisation of:
- Institution names (abbreviations → full forms)
- Author names (various formats → canonical)
- Dataset names (case/spelling variants)
- Technology names (case/spelling variants)
"""

import re
import unicodedata

_INSTITUTION_ALIASES: dict[str, str] = {
    "mit": "Massachusetts Institute of Technology",
    "caltech": "California Institute of Technology",
    "ucla": "University of California, Los Angeles",
    "uc berkeley": "University of California, Berkeley",
    "ucb": "University of California, Berkeley",
    "uc san diego": "University of California, San Diego",
    "ucsd": "University of California, San Diego",
    "ucsf": "University of California, San Francisco",
    "nyu": "New York University",
    "cmu": "Carnegie Mellon University",
    "uiuc": "University of Illinois Urbana-Champaign",
    "ut austin": "University of Texas at Austin",
    "uta": "University of Texas at Austin",
    "ucl": "University College London",
    "imperial": "Imperial College London",
    "eth zurich": "ETH Zurich",
    "ethz": "ETH Zurich",
    "epfl": "École Polytechnique Fédérale de Lausanne",
    "kaist": "KAIST",
    "nus": "National University of Singapore",
    "hku": "University of Hong Kong",
    "tum": "Technical University of Munich",
    "mpi": "Max Planck Institute",
    "cambridge": "University of Cambridge",
    "oxford": "University of Oxford",
    "stanford": "Stanford University",
    "harvard": "Harvard University",
}

_DATASET_ALIASES: dict[str, str] = {
    "imagenet": "ImageNet",
    "cifar-10": "CIFAR-10",
    "cifar10": "CIFAR-10",
    "cifar-100": "CIFAR-100",
    "cifar100": "CIFAR-100",
    "mnist": "MNIST",
    "fashion-mnist": "Fashion-MNIST",
    "fashion mnist": "Fashion-MNIST",
    "svhn": "SVHN",
    "squad": "SQuAD",
    "squad1": "SQuAD",
    "squad2": "SQuAD 2.0",
    "glue": "GLUE",
    "superglue": "SuperGLUE",
    "coco": "COCO",
    "ms coco": "COCO",
    "mscoco": "COCO",
    "cityscapes": "Cityscapes",
    "pascal voc": "PASCAL VOC",
    "pascal voc 2012": "PASCAL VOC 2012",
    "wn18": "WN18",
    "wn18rr": "WN18RR",
    "fb15k": "FB15k",
    "fb15k-237": "FB15k-237",
    "freebase": "Freebase",
    "wikidata": "Wikidata",
    "amazon review": "Amazon Review",
}

_TECHNOLOGY_ALIASES: dict[str, str] = {
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "jax": "JAX",
    "keras": "Keras",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "scipy": "SciPy",
    "numpy": "NumPy",
    "pandas": "pandas",
    "matplotlib": "Matplotlib",
    "huggingface": "Hugging Face",
    "hugging face": "Hugging Face",
    "transformers": "Transformers (Hugging Face)",
    "opencv": "OpenCV",
    "nltk": "NLTK",
    "spacy": "spaCy",
    "gensim": "Gensim",
    "django": "Django",
    "flask": "Flask",
    "react": "React",
    "angular": "Angular",
    "cuda": "CUDA",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "git": "Git",
    "bert": "BERT",
    "gpt": "GPT",
    "gpt-3": "GPT-3",
    "gpt-4": "GPT-4",
    "roberta": "RoBERTa",
    "xlnet": "XLNet",
    "t5": "T5",
    "bart": "BART",
    "deberta": "DeBERTa",
    "llama": "LLaMA",
    "llama2": "LLaMA 2",
    "llama3": "LLaMA 3",
    "mistral": "Mistral",
    "mixtral": "Mixtral",
    "falcon": "Falcon",
    "gemma": "Gemma",
}

_RE_AUTHOR_SPLIT = re.compile(r"\s*,\s*")


class ExtractionNormalizer:
    """Normalize extracted entity names to canonical forms."""

    @staticmethod
    def normalize_institution(name: str) -> str:
        """Normalize an institution name to its canonical form."""
        cleaned = _clean_text(name)
        lower = cleaned.lower()
        if lower in _INSTITUTION_ALIASES:
            return _INSTITUTION_ALIASES[lower]
        return cleaned

    @staticmethod
    def normalize_author(name: str) -> str:
        """Normalize an author name to 'First Last' format.

        Handles 'Last, First', 'Last, First M.', and 'First Last'
        formats. Strips trailing non-name tokens.
        """
        cleaned = name.strip()
        if not cleaned:
            return ""

        if "," in cleaned:
            parts = _RE_AUTHOR_SPLIT.split(cleaned, maxsplit=1)
            if len(parts) == 2:
                last, first = parts
                return f"{first.strip()} {last.strip()}"

        return cleaned

    @staticmethod
    def normalize_dataset(name: str) -> str:
        """Normalize a dataset name to its canonical form."""
        cleaned = _clean_text(name)
        lower = cleaned.lower()
        if lower in _DATASET_ALIASES:
            return _DATASET_ALIASES[lower]
        return cleaned

    @staticmethod
    def normalize_technology(name: str) -> str:
        """Normalize a technology name to its canonical form."""
        cleaned = _clean_text(name)
        lower = cleaned.lower()
        if lower in _TECHNOLOGY_ALIASES:
            return _TECHNOLOGY_ALIASES[lower]
        return cleaned


_RE_WHITESPACE = re.compile(r"\s+")


def _clean_text(text: str) -> str:
    """Strip whitespace and normalize unicode."""
    text = unicodedata.normalize("NFKC", text)
    text = _RE_WHITESPACE.sub(" ", text)
    return text.strip()
