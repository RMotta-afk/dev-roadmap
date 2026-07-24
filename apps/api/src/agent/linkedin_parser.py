"""Deterministic parser for LinkedIn 'Save to PDF' exports.

Turns the plain text produced by :mod:`agent.pdf_parser` into a structured
:class:`~app.schemas.profile.LinkedInProfile`. LinkedIn renders a two-column
layout, so pypdf emits the sidebar (Contact / Top Skills / Languages /
Certifications) first, then the main column (name, headline, location, Summary,
Experience, Education). This parser keys off the fixed section headers and,
when available, the known user name to split the intro block deterministically.
"""

from __future__ import annotations

import re

from app.schemas.profile import (
    ContactInfo,
    Education,
    Experience,
    LanguageProficiency,
    LinkedInProfile,
)

SIDEBAR_HEADERS = {"contact", "top skills", "languages", "certifications"}
MAIN_HEADERS = {
    "summary", "experience", "education", "honors & awards", "publications",
    "projects", "volunteering", "courses", "skills", "interests",
    "recommendations", "patents",
}
ALL_HEADERS = SIDEBAR_HEADERS | MAIN_HEADERS

BULLET_CHARS = "-\u2022*\u00b7\u2023\u25e6\uf0b7\u25aa\u2013"
_PAGE_RE = re.compile(r"^Page \d+ of \d+$", re.IGNORECASE)
_MONTHS = (
    "january|february|march|april|may|june|july|august|september|october|"
    "november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
)
_MONTH_START_RE = re.compile(rf"^({_MONTHS})\b", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_DURATION_RE = re.compile(r"^\d+\s+years?(\s+\d+\s+months?)?$|^\d+\s+months?$", re.IGNORECASE)
_PARENS_RE = re.compile(r"\(([^)]*)\)")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_URL_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/\S+", re.IGNORECASE)


def _clean_lines(text: str) -> list[str]:
    """Normalize raw extracted text into meaningful, non-empty lines."""
    out: list[str] = []
    for raw in text.splitlines():
        line = raw.replace("\xa0", " ").strip()
        # Drop decorative private-use glyphs except recognised bullet markers.
        line = "".join(
            ch for ch in line
            if not ("\ue000" <= ch <= "\uf8ff") or ch in BULLET_CHARS
        ).strip()
        if not line or _PAGE_RE.match(line):
            continue
        out.append(line)
    return out


def _is_bullet(line: str) -> bool:
    return bool(line) and line[0] in BULLET_CHARS and not _MONTH_START_RE.match(line)


def _strip_bullet(line: str) -> str:
    return line.lstrip(BULLET_CHARS + " ").strip()


def _is_date_range(line: str) -> bool:
    return bool(
        _MONTH_START_RE.match(line)
        and _YEAR_RE.search(line)
        and ("-" in line or "\u2013" in line or "present" in line.lower())
    )


def _is_duration_only(line: str) -> bool:
    return bool(_DURATION_RE.match(line.strip()))


def _header_of(line: str) -> str | None:
    key = line.strip().lower()
    return key if key in ALL_HEADERS else None


def _join_wrapped(lines: list[str]) -> list[str]:
    """Merge visually-wrapped continuation lines into single list items."""
    items: list[str] = []
    for line in lines:
        cont = line[:1].islower() or (items and items[-1].endswith("-"))
        if items and cont:
            joiner = "" if items[-1].endswith("-") else " "
            items[-1] = items[-1].rstrip("-") + joiner + line
        else:
            items.append(line)
    return items


def _find_name_index(lines: list[str], known_name: str | None) -> int | None:
    """Locate the line that begins the main-column intro block."""
    if known_name:
        target = known_name.strip().lower()
        for i, line in enumerate(lines):
            if line.strip().lower() == target or line.strip().lower().startswith(target):
                return i
    # Heuristic fallback: a short Title-Case line with no digits/@/| symbols.
    for i, line in enumerate(lines):
        words = line.split()
        if (
            1 < len(words) <= 4
            and not any(c.isdigit() or c in "@|" for c in line)
            and all(w[:1].isupper() for w in words if w)
        ):
            return i
    return None


def _parse_contact(lines: list[str]) -> ContactInfo:
    joined = " ".join(_join_wrapped(lines))
    email = _EMAIL_RE.search(joined)
    url = _URL_RE.search(joined)
    url_val = url.group(0) if url else None
    if url_val:
        url_val = url_val.split(" ")[0].rstrip(").,")
    return ContactInfo(
        email=email.group(0) if email else None,
        linkedin_url=url_val,
    )


def _parse_languages(lines: list[str]) -> list[LanguageProficiency]:
    langs: list[LanguageProficiency] = []
    for item in _join_wrapped(lines):
        m = _PARENS_RE.search(item)
        if m:
            langs.append(LanguageProficiency(language=item[: m.start()].strip(), proficiency=m.group(1).strip()))
        else:
            langs.append(LanguageProficiency(language=item.strip()))
    return langs


def _looks_like_header(line: str) -> bool:
    """A short, capitalized, non-bullet line — i.e. a company or job title."""
    return (
        not _is_bullet(line)
        and not _is_date_range(line)
        and len(line) <= 60
        and line[:1].isupper()
    )


def _append_continuation(highlight: str, line: str) -> str:
    joiner = "" if highlight.endswith("-") else " "
    return highlight.rstrip("-") + joiner + line


def _parse_experiences(lines: list[str]) -> list[Experience]:
    """Parse the Experience section into positions.

    LinkedIn wraps long bullets onto marker-less continuation lines and reuses a
    single company header for consecutive roles. Continuations are re-attached to
    their bullet, and only short capitalized lines are treated as company/title.
    """
    experiences: list[Experience] = []
    header_buf: list[str] = []  # company/title/duration lines before a date anchor
    last_company: str | None = None
    current: Experience | None = None
    expect_location = False

    for line in lines:
        if _is_bullet(line):
            expect_location = False
            header_buf = []
            if current is not None:
                current.highlights.append(_strip_bullet(line))
            continue

        if _is_date_range(line):
            non_dur = [h for h in header_buf if not _is_duration_only(h)]
            has_dur = any(_is_duration_only(h) for h in header_buf)
            if len(non_dur) >= 2:
                company, title = non_dur[0], non_dur[-1]
            elif len(non_dur) == 1 and has_dur:
                company, title = non_dur[0], None
            elif len(non_dur) == 1:
                company, title = last_company, non_dur[0]
            else:
                company, title = last_company, None
            if company:
                last_company = company
            dur = _PARENS_RE.search(line)
            current = Experience(
                company=company or "Unknown",
                title=title,
                date_range=_PARENS_RE.sub("", line).strip(" -\u2013"),
                duration=dur.group(1).strip() if dur else None,
            )
            experiences.append(current)
            header_buf = []
            expect_location = True
            continue

        if expect_location and current is not None and current.location is None and _looks_like_header(line):
            current.location = line
            expect_location = False
            continue
        expect_location = False

        if _looks_like_header(line) or _is_duration_only(line):
            header_buf.append(line)
        elif current is not None and current.highlights:
            current.highlights[-1] = _append_continuation(current.highlights[-1], line)
        else:
            header_buf.append(line)

    return experiences


def _parse_education(lines: list[str]) -> list[Education]:
    """Parse the Education section; a degree line attaches to the institution
    line above it."""
    kw = ("bachelor", "master", "bsc", "msc", "mba", "phd", "degree", "diploma",
          "associate", "b.e", "be,", "engineering -", "doctor")
    entries: list[Education] = []
    for line in lines:
        low = line.lower()
        date_m = _PARENS_RE.search(line)
        is_degree = bool(date_m and _YEAR_RE.search(date_m.group(1))) or any(k in low for k in kw)
        if is_degree and entries:
            body = _PARENS_RE.sub("", line).strip()
            degree, field = (body.split(",", 1) + [""])[:2] if "," in body else (body, "")
            entries[-1].degree = degree.strip() or None
            entries[-1].field_of_study = field.strip() or None
            if date_m:
                entries[-1].date_range = date_m.group(1).strip()
        else:
            entries.append(Education(institution=line.strip()))
    return entries


def _slice_sections(lines: list[str]) -> dict[str, list[str]]:
    """Group lines by their (canonical) section header."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        header = _header_of(line)
        if header is not None:
            current = header
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return sections


def parse_linkedin_profile(text: str, known_name: str | None = None) -> LinkedInProfile:
    """Parse extracted LinkedIn PDF text into a structured ``LinkedInProfile``."""
    lines = _clean_lines(text)
    if not lines:
        return LinkedInProfile()

    main_start = next(
        (i for i, ln in enumerate(lines) if (_header_of(ln) or "") in MAIN_HEADERS),
        len(lines),
    )
    name_idx = _find_name_index(lines[:main_start], known_name)

    intro = lines[name_idx:main_start] if name_idx is not None else []
    sidebar_end = name_idx if name_idx is not None else main_start
    sidebar = _slice_sections(lines[:sidebar_end])
    main = _slice_sections(lines[main_start:])

    profile = LinkedInProfile()
    if intro:
        profile.name = known_name or intro[0]
        profile.location = intro[-1] if len(intro) > 1 else None
        headline = intro[1:-1] if len(intro) > 2 else (intro[1:] if len(intro) == 2 else [])
        profile.headline = " ".join(headline) or None

    if "contact" in sidebar:
        profile.contact = _parse_contact(sidebar["contact"])
    if "top skills" in sidebar:
        profile.top_skills = [s.strip() for s in _join_wrapped(sidebar["top skills"])]
    if "languages" in sidebar:
        profile.languages = _parse_languages(sidebar["languages"])
    if "certifications" in sidebar:
        profile.certifications = [c.strip() for c in _join_wrapped(sidebar["certifications"])]

    if main.get("summary"):
        profile.summary = " ".join(main["summary"]).strip() or None
    if main.get("experience"):
        profile.experiences = _parse_experiences(main["experience"])
    if main.get("education"):
        profile.education = _parse_education(main["education"])

    return profile
