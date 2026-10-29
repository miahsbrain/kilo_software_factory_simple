#!/usr/bin/env python3
"""check-finding.py — validate a QA finding before it becomes a board row.

Reads a finding markdown body and checks that it carries the sections a
reviewer needs to act on it: summary, repro steps, expected and actual
behavior, evidence, acceptance criteria, and risk.

Usage:
  check-finding.py --body-file <path.md>
                   [--kind bug|ux|tests|docs|tech-debt]
                   [--priority high|medium|low]
                   [--category functional|visual|network|console|a11y|data|testability]
                   [--route <path>]

Exit codes:
  0  body accepted
  2  bad argument
  66 body is weak (missing sections, placeholders, too few acceptance criteria)
"""

import argparse
import re
import sys

KINDS = ("bug", "ux", "tests", "docs", "tech-debt")
PRIORITIES = ("high", "medium", "low")
CATEGORIES = ("functional", "visual", "network", "console", "a11y", "data", "testability")

RISK_LEVELS = ("\U0001f7e2 low", "\U0001f7e1 medium", "\U0001f534 high")

REQUIRED_SECTIONS = (
    "Summary",
    "Repro steps",
    "Expected behavior",
    "Actual behavior",
    "Evidence",
    "Acceptance criteria",
    "Risk",
)

EVIDENCE_WORDS = ("screenshot", "console", "network", "spec")
EVIDENCE_ARTIFACTS = ("screenshot", "console", "network", "spec/test")

FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]*`")
PLACEHOLDER_ANGLE_RE = re.compile(r"<[^>\n]*[\s:][^>\n]*>")
PLACEHOLDER_DOTS_RE = re.compile(r"<\.\.\.>")
CHECKBOX_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s+\S", re.MULTILINE)
NUMBERED_RE = re.compile(r"^\s*\d+[.)]\s+\S", re.MULTILINE)
RISK_LEVEL_RE = re.compile(
    r"(\U0001f7e2\s*low|\U0001f7e1\s*medium|\U0001f534\s*high|\blow\b|\bmedium\b|\bhigh\b)",
    re.IGNORECASE,
)
REVERSIBILITY_RE = re.compile(r"\bone[-\s]?way\b|\btwo[-\s]?way\b", re.IGNORECASE)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="check-finding.py",
        description="Validate a QA finding markdown body before it becomes a board row.",
    )
    parser.add_argument("--body-file", required=True, help="Path to the finding markdown file.")
    parser.add_argument("--kind", default=None, choices=list(KINDS), help="Finding kind.")
    parser.add_argument("--priority", default=None, choices=list(PRIORITIES), help="Finding priority.")
    parser.add_argument("--category", default=None, choices=list(CATEGORIES), help="Finding category.")
    parser.add_argument("--route", default=None, help="Route the finding applies to.")
    args = parser.parse_args(argv)
    return args


def section_body(body, name):
    """Return the text under the heading matching name, up to the next heading."""
    pattern = re.compile(
        r"^#{1,6}[ \t]+(?P<title>.+?)[ \t]*$", re.MULTILINE
    )
    wanted = name.lower()
    collected = []
    inside = False
    for match in pattern.finditer(body):
        title = match.group("title").strip().lower()
        if inside:
            break
        if title == wanted:
            inside = True
            start = match.end()
            continue
    if not inside:
        return None
    rest = body[start:]
    next_heading = re.search(r"^#{1,6}[ \t]+", rest, re.MULTILINE)
    if next_heading:
        rest = rest[: next_heading.start()]
    return rest.strip()


def strip_code(body):
    text = FENCE_RE.sub("", body)
    return INLINE_CODE_RE.sub("", text)


def check_placeholders(body):
    problems = []
    prose = strip_code(body)
    if re.search(r"(^|[^A-Za-z0-9_])TBD\b", prose, re.IGNORECASE):
        problems.append("body still contains a 'TBD' placeholder")
    if "TODO:" in prose:
        problems.append("body still contains a 'TODO:' placeholder")
    if "FIXME" in prose:
        problems.append("body still contains a 'FIXME' placeholder")
    if PLACEHOLDER_ANGLE_RE.search(prose) or PLACEHOLDER_DOTS_RE.search(prose):
        problems.append("body still contains an angle-bracket placeholder")
    return problems


def check_evidence(section):
    problems = []
    lowered = section.lower()
    for word in EVIDENCE_WORDS:
        if word not in lowered:
            problems.append(
                "## Evidence must mention the " + word + " output (screenshot path, console output, network output, or spec/test path)"
            )
    lines = [line for line in section.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        lowered_line = line.lower()
        if "not captured" not in lowered_line:
            continue
        inline = lowered_line.split("not captured", 1)[1].strip(" :-\t")
        following = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if not inline and not following:
            problems.append("## Evidence says 'not captured' without a reason")
    return problems


def check_risk(section):
    problems = []
    if not RISK_LEVEL_RE.search(section):
        problems.append("## Risk must state a level (low, medium, or high)")
    if not REVERSIBILITY_RE.search(section):
        problems.append("## Risk must say whether the change is one-way or two-way to reverse")
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    if len(lines) < 2:
        problems.append("## Risk needs a blast-radius line describing who breaks if the change is wrong")
    return problems


def validate(body):
    problems = []
    sections = {}
    for name in REQUIRED_SECTIONS:
        sections[name] = section_body(body, name)
        content = sections[name]
        if content is None:
            problems.append("body is missing required section: ## " + name)
        elif not content.strip():
            problems.append("required section is empty: ## " + name)

    summary = sections["Summary"]
    if summary and summary.strip():
        if len([line for line in summary.splitlines() if line.strip()]) > 3:
            problems.append("## Summary should be one sentence")

    repro = sections["Repro steps"]
    if repro and repro.strip() and len(NUMBERED_RE.findall(repro)) < 2:
        problems.append("## Repro steps needs at least 2 numbered steps")

    acceptance = sections["Acceptance criteria"]
    if acceptance and acceptance.strip() and len(CHECKBOX_RE.findall(acceptance)) < 2:
        problems.append("## Acceptance criteria needs at least 2 '- [ ]' checkboxes")

    evidence = sections["Evidence"]
    if evidence and evidence.strip():
        problems.extend(check_evidence(evidence))

    risk = sections["Risk"]
    if risk and risk.strip():
        problems.extend(check_risk(risk))

    problems.extend(check_placeholders(body))
    return problems


def main(argv):
    args = parse_args(argv)
    try:
        with open(args.body_file, "r", encoding="utf-8") as handle:
            body = handle.read()
    except OSError as error:
        sys.stderr.write("check-finding: cannot read body file: " + str(error) + "\n")
        return 66

    problems = validate(body)
    if problems:
        sys.stderr.write("check-finding: finding body is weak\n")
        for problem in problems:
            sys.stderr.write("  - " + problem + "\n")
        return 66

    sys.stdout.write("check-finding: body accepted\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
