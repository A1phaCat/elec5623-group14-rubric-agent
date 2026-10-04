from __future__ import annotations

import re

TOKEN = re.compile(r"[a-z0-9@]+")
STOP = {
    "a", "an", "the", "and", "or", "of", "to", "for", "in", "on", "with", "by",
    "is", "are", "be", "as", "at", "from", "that", "this", "it", "its", "was",
    "were", "not", "no", "but", "if", "then", "than", "into", "without", "within",
}
# Canonical form is [E-001]; models also produce [E-001, E-002] or [E-001: "quote"].
# Any E-00N inside square brackets counts as a citation *attempt*; whether the ID is
# allowed is checked separately by the validator.
BRACKET = re.compile(r"\[([^\]]*?E-\d{3}[^\]]*)\]")
ID_IN_BRACKET = re.compile(r"E-\d{3}")
# Split only at a full stop / ! / ? followed by whitespace and a capital, quote or bracket,
# so that semicolons and quoted rubric text do not create citation-less fragments.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])")

# Sentences that *deny* support are not positive claims (proposal FR10).
NEGATIVE_OPENERS = (
    "insufficient", "no relevant", "no evidence", "not enough", "the evidence does not",
    "cannot", "could not", "unable", "does not address", "no score",
)
# A sentence that says something is *absent* is not a positive claim: absence cannot be
# cited to a span. Matched anywhere in the sentence.
NEGATIVE_MARKERS = re.compile(
    r"\b(?:does not|do not|did not|is not|are not|was not|were not|not (?:explicitly |clearly |fully )?"
    r"(?:state|stated|mention|mentioned|provide|provided|describe|described|address|addressed|present|shown|given|include|included)|"
    r"no (?:evidence|mention|detail|details|metric|metrics|baseline|plan|discussion|explanation|information)|"
    r"lacks?|lacking|missing|absent|omits?|fails? to|without (?:any|a|an|specifying|stating|explaining|providing))\b",
    re.I,
)
# A sentence about the rubric level rather than the submission's content: a judgement,
# not a claim that can be traced to a span ("This aligns with the descriptor for 4.0").
JUDGEMENT_MARKERS = re.compile(
    r"\b(?:descriptor|rubric|level|band|criterion(?:'s)? (?:descriptor|level|wording)|"
    r"aligns? with|matches? the|corresponds? to|meets? the|warrants?|justif(?:y|ies) a score|score of|"
    r"best matches|therefore|overall|in summary|thus|hence)\b",
    re.I,
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
    out: list[str] = []
    for group in BRACKET.findall(text or ""):
        out.extend(ID_IN_BRACKET.findall(group))
    return out


# [E-001: "span"] or [E-001: 'span'] inside one citation bracket.
CITED_QUOTE = re.compile(r"""(E-\d{3})\s*:\s*(["'])(.*?)\2""", re.DOTALL)


def cited_quotes(text: str) -> list[tuple[str, str]]:
    """Quoted spans written next to an evidence id, as in [E-001: "span"]."""
    found: list[tuple[str, str]] = []
    for group in BRACKET.findall(text or ""):
        for eid, _mark, quote in CITED_QUOTE.findall(group):
            found.append((eid, quote))
    return found


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT.split(normalize(text)) if s.strip()]


def positive_claims(text: str) -> list[str]:
    """Sentences that assert something *is in* the submission.

    This is the unit counted by M6 (unsupported-judgement rate): every positive
    claim must carry at least one `[E-00N]` citation. Excluded, because they
    cannot point at a span: sentences that state an absence ("does not
    mention…", "no baseline is given") and sentences that only relate the
    finding to the rubric ("this aligns with the descriptor for 4.0"). A
    sentence that carries a citation is always kept, whatever it says.
    """
    out = []
    for s in sentences(text):
        low = s.lower()
        if citation_ids(s):
            out.append(s)
            continue
        if low.startswith(NEGATIVE_OPENERS) or NEGATIVE_MARKERS.search(s) or JUDGEMENT_MARKERS.search(s):
            continue
        out.append(s)
    return out


def unsupported_claims(text: str) -> list[str]:
    return [s for s in positive_claims(text) if not citation_ids(s)]
