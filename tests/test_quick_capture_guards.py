"""
Tests for false-positive guards in quick_capture.py's tag and
section/subsection token extraction.

Found while wiring the web control panel's "press Enter to create" box to
the same grammar as `tm add` (TODOs.md Issue 4 follow-up): the panel
reuses `parse_quick_capture` directly, and a panel test caught a
pre-existing bug that also affects the CLI itself —

  `tm add "Fix bug #1234"` silently renamed the task to "Fix bug" and
  invented a tag "1234", because any "#word" was treated as a tag with
  no regard for whether it looked like an issue/PR/ticket reference.

  `tm add "Pay rent / utilities split"` silently treated "/ utilities"
  as a section token, mangling the name and setting a bogus section.

Both are fixed at the source in quick_capture.py, so the CLI and the web
panel (which share this exact code) are protected identically.
"""
from taskmd.quick_capture import parse_quick_capture


class TestTagExtractionFalsePositives:
    def test_purely_numeric_hashtag_not_treated_as_tag(self):
        r = parse_quick_capture("Fix bug #1234")
        assert r.name == "Fix bug #1234"
        assert r.tags == []

    def test_pr_number_not_treated_as_tag(self):
        r = parse_quick_capture("Review PR #45 for team")
        assert r.name == "Review PR #45 for team"
        assert r.tags == []

    def test_ticket_number_not_treated_as_tag(self):
        r = parse_quick_capture("Investigate ticket #99887")
        assert "#99887" in r.name
        assert r.tags == []

    def test_alphanumeric_hashtag_still_a_real_tag(self):
        # "q3" has a letter, so it's a legitimate tag, not a bare reference.
        r = parse_quick_capture("Submit report #q3")
        assert r.name == "Submit report"
        assert r.tags == ["q3"]

    def test_word_hashtag_still_extracted_normally(self):
        r = parse_quick_capture("Buy milk #errand")
        assert r.name == "Buy milk"
        assert r.tags == ["errand"]

    def test_multiple_tags_mixed_numeric_and_word(self):
        r = parse_quick_capture("Fix bug #1234 #urgent #q3")
        assert "#1234" in r.name
        assert set(r.tags) == {"urgent", "q3"}

    def test_numeric_tag_with_trailing_letters_is_a_real_tag(self):
        # "123abc" is not *purely* numeric, so it's treated as an intentional tag.
        r = parse_quick_capture("Task #123abc")
        assert r.tags == ["123abc"]


class TestSectionExtractionFalsePositives:
    def test_slash_with_surrounding_spaces_not_a_section_token(self):
        r = parse_quick_capture("Pay rent / utilities split")
        assert r.name == "Pay rent / utilities split"
        assert r.section is None

    def test_and_or_slash_not_a_section_token(self):
        r = parse_quick_capture("Task with and/or logic")
        assert "and/or" in r.name
        assert r.section is None

    def test_date_like_slash_not_a_section_token(self):
        r = parse_quick_capture("Date is 6/25 for the meeting")
        assert "6/25" in r.name
        assert r.section is None

    def test_legitimate_section_token_still_works(self):
        r = parse_quick_capture("Submit report /Work")
        assert r.name == "Submit report"
        assert r.section == "Work"

    def test_legitimate_section_and_subsection_tokens_still_work(self):
        r = parse_quick_capture("Buy milk #errand @tomorrow /Personal //Shopping")
        assert r.name == "Buy milk"
        assert r.section == "Personal"
        assert r.sub == "Shopping"

    def test_documented_help_text_example_still_works(self):
        # Exact example from `tm help`'s Quick Capture section.
        r = parse_quick_capture("Review PR !2 @+3d /Work //Docs [check CI first]")
        assert r.name == "Review PR"
        assert r.section == "Work"
        assert r.sub == "Docs"
        assert r.pri == 2
        assert r.rem == "check CI first"
