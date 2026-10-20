import pytest
from backend.app.config import (
    INDICTRANS2_ALLOWLIST,
    INDICTRANS2_EN_INDIC_MODEL_NAME,
    INDICTRANS2_INDIC_EN_MODEL_NAME,
    INDICTRANS2_EN_INDIC_REVISION,
    INDICTRANS2_INDIC_EN_REVISION,
)
from backend.app.translator import IndicTrans2Engine, IndicToEnEngine


def test_indictrans2_allowlist_contents():
    """Assert allowlist contains only official AI4Bharat repositories and correct pinned revisions."""
    expected_repos = {
        "ai4bharat/indictrans2-en-indic-dist-200M",
        "ai4bharat/indictrans2-indic-en-dist-200M",
    }
    assert set(INDICTRANS2_ALLOWLIST.keys()) == expected_repos, (
        f"Allowlist must contain only official AI4Bharat repos, got: {set(INDICTRANS2_ALLOWLIST.keys())}"
    )
    assert INDICTRANS2_ALLOWLIST[INDICTRANS2_EN_INDIC_MODEL_NAME] == "2cfd0a20057756d756bf3e53528f492afc52f91a"
    assert INDICTRANS2_ALLOWLIST[INDICTRANS2_INDIC_EN_MODEL_NAME] == "d66a2122ad6d28184f3dc3797b652bd80ae3f65f"
    assert INDICTRANS2_EN_INDIC_REVISION == "2cfd0a20057756d756bf3e53528f492afc52f91a"
    assert INDICTRANS2_INDIC_EN_REVISION == "d66a2122ad6d28184f3dc3797b652bd80ae3f65f"


def test_non_allowlisted_repo_raises_in_indictrans2_engine():
    """Assert IndicTrans2Engine refuses to load non-allowlisted repo IDs."""
    with pytest.raises(ValueError, match="not in the approved IndicTrans2 allowlist"):
        IndicTrans2Engine(model_name="benfranklinms/indictrans2-indic-en-dist-200M")

    with pytest.raises(ValueError, match="not in the approved IndicTrans2 allowlist"):
        IndicTrans2Engine(model_name="unauthorized/unvetted-repo")


def test_non_allowlisted_repo_raises_in_indic_to_en_engine():
    """Assert IndicToEnEngine refuses to load non-allowlisted repo IDs."""
    with pytest.raises(ValueError, match="not in the approved IndicTrans2 allowlist"):
        IndicToEnEngine(model_name="benfranklinms/indictrans2-indic-en-dist-200M")

    with pytest.raises(ValueError, match="not in the approved IndicTrans2 allowlist"):
        IndicToEnEngine(model_name="evil-actor/malicious-model")
