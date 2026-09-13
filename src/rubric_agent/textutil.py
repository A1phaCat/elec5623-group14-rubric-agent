from __future__ import annotations

import re

TOKEN = re.compile(r"[a-z0-9@]+")
STOP = {
    "a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "with", "by",
    "is", "are", "be", "as", "at", "from", "that", "this", "it", "its", "was",
    "were", "not", "no", "but", "if", "then", "than", "into", "without", "within",
}
CITATION = re.compile(r"\[(E-\d{3})\]")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?;])\s+")

# Sentences that *deny* support are not positive claims (proposal FR10).
NEGATIVE_OPENERS = (
    "insufficient", "no relevant", "no evidence", "not enough", "the evidence does not",
    "cannot", "could not", "unable", "does not address", "no score",
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def content_tokens(text: str) -> list[str]:
    return [t for t in tokens(text) if t not in STOP and len(t) > 1]


_SUFFIXES = ("ations", "ation", "ised", "ized", "ising", "izing", "ness", "ments", "ment",
             "ings", "ing", "edly", "ies", "ed", "es", "ly", "s")


def stem(token: str) -> str:
    """Tiny suffix stripper so 'scoped'/'scope' and 'metrics'/'metric' compare equal.

    Deliberately crude and deterministic; it only has to be consistent between
    query and document, not linguistically correct.
    """
    if len(token) <= 4 or "@" in token or token.isdigit():
        return token
    for suf in _SUFFIXES:
        if token.endswith(suf) and len(token) - len(suf) >= 3:
            base = token[: -len(suf)]
            if suf == "ies":
                base += "y"
            return base
    return token


def stemmed_tokens(text: str) -> list[str]:
    return [stem(t) for t in content_tokens(text)]


def citation_ids(text: str) -> list[str]:
    return CITATION.findall(text or "")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT.split(normalize(text)) if s.strip()]


def positive_claims(text: str) -> list[str]:
    """Sentences that assert something about the submission.

    This is the unit counted by M6 (unsupported-judgement rate): every positive
    claim must carry at least one `[E-00N]` citation.
    """
    out = []
    for s in sentences(text):
        low = s.lower()
        if low.startswith(NEGATIVE_OPENERS):
            continue
        out.append(s)
    return out


def unsupported_claims(text: str) -> list[str]:
    return [s for s in positive_claims(text) if not citation_ids(s)]
