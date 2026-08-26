import json
from datetime import date
from unittest.mock import MagicMock

from apps.analytics.investigation.models import (
    ContributionAnalysis,
    Contributor,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationSummary,
)
from apps.analytics.narrator.models import InvestigationNarrative
from apps.analytics.narrator.narrator import (
    DeterministicFallbackNarrator,
    generate_investigation_narrative,
)
from apps.analytics.narrator.prompt import build_narrator_prompt


def _create_mock_investigation(
    metric: str = "total_gmv", direction: str = "increase"
) -> InvestigationResponse:
    """Helper to generate mock InvestigationResponse."""
    req = InvestigationRequest(
        metric=metric,
        current_start=date(2017, 11, 24),
        current_end=date(2017, 11, 24),
        baseline_start=date(2017, 11, 17),
        baseline_end=date(2017, 11, 17),
        dimensions=["customer_state", "product_category_name"],
    )

    tot_cur = 152653.74 if direction == "increase" else 20000.0
    tot_base = 29209.07 if direction == "increase" else 100000.0
    tot_chg = tot_cur - tot_base
    tot_pct = (tot_chg / tot_base) * 100.0

    return InvestigationResponse(
        request=req,
        summary=InvestigationSummary(
            metric=metric,
            direction="increase" if tot_chg > 0 else "decrease",
            total_current=tot_cur,
            total_baseline=tot_base,
            total_change=tot_chg,
            total_change_pct=tot_pct,
            primary_positive_dimension="customer_state",
            primary_positive_contributor="SP",
            primary_negative_dimension="product_category_name",
            primary_negative_contributor="audio",
        ),
        analyses=[
            ContributionAnalysis(
                metric=metric,
                dimension="customer_state",
                current_start=req.current_start,
                current_end=req.current_end,
                baseline_start=req.baseline_start,
                baseline_end=req.baseline_end,
                total_current=tot_cur,
                total_baseline=tot_base,
                total_change=tot_chg,
                total_change_pct=tot_pct,
                top_positive_contributors=[
                    Contributor(
                        dimension="customer_state",
                        value="SP",
                        current_value=40000.0,
                        baseline_value=10000.0,
                        absolute_change=30000.0,
                        percentage_change=300.0,
                        contribution_pct=24.3,
                        rank=1,
                    )
                ],
                top_negative_contributors=[],
                all_contributors_count=1,
            ),
            ContributionAnalysis(
                metric=metric,
                dimension="product_category_name",
                current_start=req.current_start,
                current_end=req.current_end,
                baseline_start=req.baseline_start,
                baseline_end=req.baseline_end,
                total_current=tot_cur,
                total_baseline=tot_base,
                total_change=tot_chg,
                total_change_pct=tot_pct,
                top_positive_contributors=[
                    Contributor(
                        dimension="product_category_name",
                        value="cama_mesa_banho",
                        current_value=20000.0,
                        baseline_value=5000.0,
                        absolute_change=15000.0,
                        percentage_change=300.0,
                        contribution_pct=12.15,
                        rank=1,
                    )
                ],
                top_negative_contributors=[
                    Contributor(
                        dimension="product_category_name",
                        value="audio",
                        current_value=500.0,
                        baseline_value=1000.0,
                        absolute_change=-500.0,
                        percentage_change=-50.0,
                        contribution_pct=-0.41,
                        rank=1,
                    )
                ],
                all_contributors_count=2,
            ),
        ],
    )


# 1. Test deterministic fallback works without LLM API key
def test_narrator_deterministic_fallback_generation() -> None:
    """Test that fallback creates a complete narrative with all required sections."""
    inv = _create_mock_investigation()
    narrative = DeterministicFallbackNarrator.generate(inv)

    assert isinstance(narrative, InvestigationNarrative)
    assert narrative.narrator_type == "deterministic_fallback"
    assert "TOTAL_GMV" in narrative.title
    assert len(narrative.key_findings) >= 2
    assert len(narrative.root_causes) >= 1
    assert len(narrative.contributing_factors) >= 1
    assert len(narrative.recommended_next_steps) >= 1
    assert len(narrative.evidence_references) >= 3
    assert "causal identification" in narrative.disclaimer.lower()


# 2. Test evidence preservation in fallback narrative
def test_narrator_evidence_numbers_preserved() -> None:
    """Test that numbers cited in the narrative match evidence exactly."""
    inv = _create_mock_investigation()
    narrative = DeterministicFallbackNarrator.generate(inv)

    refs_text = " ".join(narrative.evidence_references)
    assert "30000" in refs_text or "30,000" in refs_text
    assert "SP" in refs_text
    assert "cama_mesa_banho" in refs_text


# 3. Test prompt generation contract
def test_build_narrator_prompt_contract() -> None:
    """Test that prompt includes strict evidence contract and json."""
    inv = _create_mock_investigation()
    prompt = build_narrator_prompt(inv)

    assert "STRICT EVIDENCE CONTRACT" in prompt
    assert "NO CAUSALITY FROM ASSOCIATION" in prompt
    assert "VERIFIED NUMERICAL EVIDENCE" in prompt
    assert "total_gmv" in prompt.lower()


# 4. Test LLM provider integration with mock
def test_narrator_with_mocked_llm_provider() -> None:
    """Test successful LLM generation with structured JSON response."""
    inv = _create_mock_investigation()

    mock_llm_response = {
        "title": "Black Friday 2017 Total GMV Investigation",
        "executive_summary": "Total GMV increased by +422.62% during Black Friday.",
        "anomaly_statement": "A surge was observed on 2017-11-24.",
        "key_findings": [
            "SP was the top contributing region accounting for 24.3% of the increase.",
            "cama_mesa_banho led category growth with +R$ 15,000.00.",
        ],
        "root_causes": ["Regional expansion and high demand in SP."],
        "contributing_factors": ["Minor contraction in audio (-R$ 500.00)."],
        "recommended_next_steps": ["Maintain fulfillment capacity in SP."],
        "evidence_references": ["Total change: R$ 123,444.67 (+422.62%)."],
        "disclaimer": "Observed associations do not assert causal identification.",
    }

    mock_provider = MagicMock()
    mock_provider.generate.return_value = json.dumps(mock_llm_response)

    narrative = generate_investigation_narrative(
        investigation=inv, provider=mock_provider
    )

    assert narrative.narrator_type == "llm"
    assert narrative.title == "Black Friday 2017 Total GMV Investigation"
    assert len(narrative.key_findings) == 2
    assert "SP" in narrative.key_findings[0]


# 5. Test LLM provider error falls back safely to deterministic
def test_narrator_llm_failure_falls_back_safely() -> None:
    """Test that LLM error triggers clean deterministic fallback."""
    inv = _create_mock_investigation()

    mock_provider = MagicMock()
    mock_provider.generate.side_effect = RuntimeError("OpenAI API 500 Error")

    narrative = generate_investigation_narrative(
        investigation=inv, provider=mock_provider
    )

    assert narrative.narrator_type == "deterministic_fallback"
    assert "TOTAL_GMV" in narrative.title


# 6. Test handling of empty contributor lists
def test_narrator_empty_contributors_handling() -> None:
    """Test that empty slice changes produce valid text without crashing."""
    req = InvestigationRequest(
        metric="orders_count",
        current_start=date(2018, 5, 1),
        current_end=date(2018, 5, 1),
        baseline_start=date(2018, 4, 1),
        baseline_end=date(2018, 4, 1),
        dimensions=["customer_state"],
    )
    inv_empty = InvestigationResponse(
        request=req,
        summary=InvestigationSummary(
            metric="orders_count",
            direction="unchanged",
            total_current=100.0,
            total_baseline=100.0,
            total_change=0.0,
            total_change_pct=0.0,
        ),
        analyses=[
            ContributionAnalysis(
                metric="orders_count",
                dimension="customer_state",
                current_start=req.current_start,
                current_end=req.current_end,
                baseline_start=req.baseline_start,
                baseline_end=req.baseline_end,
                total_current=100.0,
                total_baseline=100.0,
                total_change=0.0,
                total_change_pct=0.0,
                top_positive_contributors=[],
                top_negative_contributors=[],
                all_contributors_count=0,
            )
        ],
    )

    narrative = DeterministicFallbackNarrator.generate(inv_empty)
    assert narrative.narrator_type == "deterministic_fallback"
    assert len(narrative.key_findings) > 0
    assert len(narrative.root_causes) > 0
