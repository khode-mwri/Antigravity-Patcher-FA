"""Contract tests for :mod:`patcher.i18n`, the trilingual UI string catalog.

The GUI layer looks every user-visible label up through this module, so the
tests pin down the parts the rest of the application relies on:

* key parity      -- EN/FA/RU always expose exactly the same keys;
* fallback        -- active language, then English, then the key itself;
* formatting      -- ``{target}``/``{version}``/``{tag}`` work in every
  language and a missing argument never raises;
* language state  -- codes and aliases are accepted case-insensitively,
  unknown values are rejected without changing the current language, and only
  ``fa`` is right-to-left;
* encoding        -- Persian strings use the Persian letters ی (U+06CC) and
  ک (U+06A9), never the Arabic look-alikes (U+064A) / (U+0643).

Everything here is pure Python: no display, network or Tk is touched, so the
suite runs unchanged on a headless Linux CI box.
"""

import pytest

from patcher import i18n

# Arabic look-alike letters, written as escapes so this file itself stays free
# of them (tests/test_strings.py scans the whole source tree for the literals).
ARABIC_YEH = "\u064a"
ARABIC_KAF = "\u0643"

#: Expected display order of the supported languages.
EXPECTED_ORDER = ["en", "fa", "ru"]

CATALOGS = {"en": i18n.EN, "fa": i18n.FA, "ru": i18n.RU}

#: One representative value for every placeholder the catalogs use.
FORMAT_SAMPLES = {
    "confirm_patch_msg": {"target": "Antigravity IDE"},
    "confirm_restore_msg": {"target": "Antigravity IDE"},
    "running_patch": {"target": "Antigravity CLI (agy)"},
    "running_restore": {"target": "Antigravity CLI (agy)"},
    "updates_latest": {"version": "1.4.3"},
    "updates_available": {"tag": "v2.0.0", "version": "1.4.3"},
}

@pytest.fixture(autouse=True)
def _reset_language():
    """Restore the module-level active language after every test."""
    previous = i18n.get_language()
    try:
        yield
    finally:
        i18n.set_language(previous)

def test_languages_are_ordered_en_fa_ru_with_labels():
    assert list(i18n.LANGUAGES) == EXPECTED_ORDER
    assert i18n.LANGUAGES["en"] == "English"
    assert i18n.LANGUAGES["fa"] == "فارسی"
    assert i18n.LANGUAGES["ru"] == "Русский"
    assert i18n.available_languages() == list(i18n.LANGUAGES.items())

def test_default_language_is_english():
    assert i18n.DEFAULT_LANGUAGE == "en"
    assert i18n.set_language("en") is True
    assert i18n.get_language() == "en"

@pytest.mark.parametrize("code", EXPECTED_ORDER)
def test_catalogs_have_exactly_the_same_keys_as_english(code):
    """No language may drift: every key in EN must be present, and nothing extra."""
    reference = set(i18n.EN)
    assert "app_brand" in reference, "the EN catalog looks empty/broken"

    missing = reference - set(CATALOGS[code])
    extra = set(CATALOGS[code]) - reference
    assert not missing, "%s is missing keys: %s" % (code, sorted(missing))
    assert not extra, "%s has extra keys: %s" % (code, sorted(extra))

@pytest.mark.parametrize("code", EXPECTED_ORDER)
def test_catalogs_have_no_empty_values(code):
    empty = [key for key, value in CATALOGS[code].items() if not value.strip()]
    assert not empty, "%s has empty values for: %s" % (code, empty)

@pytest.mark.parametrize("code", EXPECTED_ORDER)
def test_tr_returns_text_of_the_active_language(code):
    assert i18n.set_language(code)
    for key in i18n.EN:
        assert i18n.tr(key) == CATALOGS[code][key]

def test_tr_falls_back_to_english_for_a_language_without_a_catalog(monkeypatch):
    """If the active code has no catalog (e.g. stale state), English is used."""
    monkeypatch.setattr(i18n, "_current_language", "de")
    assert i18n.tr("patch") == i18n.EN["patch"]
    assert i18n.tr("about_body") == i18n.EN["about_body"]

@pytest.mark.parametrize("code", EXPECTED_ORDER)
def test_tr_returns_the_key_itself_for_unknown_keys(code):
    assert i18n.set_language(code)
    assert i18n.tr("definitely-not-a-catalog-key") == "definitely-not-a-catalog-key"

def test_tr_returns_key_with_format_arguments_applied_for_unknown_keys():
    assert i18n.tr("missing_{name}", name="thing") == "missing_thing"

@pytest.mark.parametrize("code", EXPECTED_ORDER)
@pytest.mark.parametrize("key", sorted(FORMAT_SAMPLES))
def test_tr_formats_placeholders_in_every_language(code, key):
    assert i18n.set_language(code)
    kwargs = FORMAT_SAMPLES[key]
    expected = CATALOGS[code][key].format(**kwargs)
    assert i18n.tr(key, **kwargs) == expected
    for value in kwargs.values():
        assert value in expected

@pytest.mark.parametrize("code", EXPECTED_ORDER)
def test_tr_never_raises_when_a_format_argument_is_missing(code):
    assert i18n.set_language(code)
    # updates_available needs {tag} and {version}; supply only one.
    rendered = i18n.tr("updates_available", tag="v9.9.9")
    assert isinstance(rendered, str)
    assert "v9.9.9" in rendered
    assert "{version}" in rendered, "the missing placeholder must survive verbatim"

    # No arguments at all: the template must come back unchanged, not raise.
    rendered = i18n.tr("confirm_patch_msg")
    assert isinstance(rendered, str)
    assert "{target}" in rendered

@pytest.mark.parametrize(
    "value, expected",
    [
        ("en", "en"),
        ("fa", "fa"),
        ("ru", "ru"),
        ("EN", "en"),
        ("Fa", "fa"),
        ("RU", "ru"),
        (" persian ", "fa"),
        ("Farsi", "fa"),
        ("RUSSIAN", "ru"),
    ],
    ids=["en", "fa", "ru", "EN", "Fa", "RU", "persian", "Farsi", "RUSSIAN"],
)
def test_set_language_accepts_codes_and_aliases(value, expected):
    assert i18n.set_language(value) is True
    assert i18n.get_language() == expected

@pytest.mark.parametrize(
    "value",
    ["de", "fr", "", "english", "persiann", "russ", None, 42],
    ids=["de", "fr", "empty", "english", "persiann", "russ", "none", "int"],
)
def test_set_language_rejects_invalid_values_without_changing_state(value):
    assert i18n.set_language("fa") is True
    assert i18n.set_language(value) is False
    assert i18n.get_language() == "fa"

@pytest.mark.parametrize(
    "code, rtl",
    [("en", False), ("fa", True), ("ru", False)],
    ids=["en", "fa", "ru"],
)
def test_is_rtl_true_only_for_persian(code, rtl):
    assert i18n.set_language(code)
    assert i18n.is_rtl() is rtl

def test_persian_strings_use_persian_letters_not_arabic_variants():
    """Persian text must use ی/ک (U+06CC/U+06A9), never Arabic U+064A/U+0643."""
    offenders = []
    persian_strings = dict(i18n.FA)
    persian_strings["LANGUAGES[fa]"] = i18n.LANGUAGES["fa"]
    for key, value in persian_strings.items():
        for char, name in ((ARABIC_YEH, "Arabic yeh U+064A"), (ARABIC_KAF, "Arabic kaf U+0643")):
            if char in value:
                offenders.append("%s: %s in %r" % (key, name, value))
    assert not offenders, (
        "Arabic look-alike letters found (use Persian ی U+06CC / ک U+06A9):\n"
        + "\n".join(offenders)
    )
    # Sanity in the opposite direction: the catalog really does use ی/ک.
    assert any("ی" in value for value in i18n.FA.values())
    assert any("ک" in value for value in i18n.FA.values())

def test_supported_languages_expose_the_required_catalog_keys():
    """Every translation key referenced by the GUI contract exists in all catalogs."""
    required = {
        "app_brand", "app_tagline", "language", "refresh", "browse", "cancel",
        "close", "status_title", "status_scanning", "found", "not_found",
        "patched", "not_patched", "unknown", "version", "path", "size",
        "backup_available", "sec_targets", "sec_log", "sec_tools", "sec_about",
        "target_ide", "target_manager", "target_cli", "target_vscode",
        "target_vscode_binary", "patch", "restore", "patch_all", "restore_all",
        "pick_path", "detected_auto", "confirm_title", "confirm_patch_msg",
        "confirm_restore_msg", "running_patch", "running_restore", "done_ok",
        "done_fail", "already_patched_note", "no_backup_note", "need_admin_note",
        "busy_title", "busy_msg", "open_releases", "open_issues", "star_repo",
        "check_updates", "updates_latest", "updates_available", "telegram",
        "repo", "license", "about_body", "log_empty_hint", "lang_changed_hint",
        "dlg_success_title", "dlg_error_title",
    }
    for code in EXPECTED_ORDER:
        assert required <= set(CATALOGS[code]), (
            "%s is missing required keys: %s" % (code, sorted(required - set(CATALOGS[code])))
        )
