"""Unit and integration tests for Phase 5C AI Investigation Layer."""

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from apps.ai.investigator import (
    extract_evidence_payload,
    investigate_with_ai,
)
from apps.ai.models import AIInvestigationResponse
from apps.ai.prompts import build_investigation_prompt
from apps.ai.provider import (
    DeterministicFallbackProvider,
    OpenAICompatibleProvider,
)
from apps.analytics.rootcause.models import (
    AnomalySummary,
    DimensionContributor,
    OperationalIndicators,
    RootCauseInvestigationRequest,
    RootCauseInvestigationResponse,
    VolumeValueDecomposition,
)


@pytest.fixture
def sample_root_cause_response() -> RootCauseInvestigationResponse:
    """Fixture providing deterministic root-cause response."""
    req = RootCauseInvestigationRequest(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        comparison_days=7,
        dimensions=["product_category", "customer_state"],
    )
    summary = AnomalySummary(
        metric="total_gmv",
        anomaly_date=date(2017, 11, 24),
        baseline_start_date=date(2017, 11, 17),
        baseline_end_date=date(2017, 11, 23),
        observed_value=152653.74,
        baseline_value=31524.93,
        absolute_change=121128.81,
        percentage_change=384.2,
        direction="increase",
    )
    decomp = VolumeValueDecomposition(
        observed_orders=1176.0,
        baseline_orders=207.0,
        observed_aov=129.81,
        baseline_aov=152.61,
        volume_effect=147944.71,
        aov_effect=-4709.80,
        interaction_effect=-22103.00,
        total_change=121128.81,
        volume_contribution_pct=122.14,
        aov_contribution_pct=-3.89,
        interaction_contribution_pct=-18.25,
    )
    contributors = [
        DimensionContributor(
            dimension="customer_state",
            dimension_value="SP",
            observed_value=50000.0,
            baseline_value=11448.32,
            absolute_change=38551.68,
            percentage_change=336.75,
            contribution_pct=31.83,
            direction="increase",
            rank=1,
        )
    ]
    ops = OperationalIndicators(
        observed_late_delivery_rate=20.0,
        baseline_late_delivery_rate=14.2,
        late_delivery_rate_change=5.8,
        observed_avg_delivery_days=17.2,
        baseline_avg_delivery_days=12.5,
        avg_delivery_days_change=4.7,
        observed_cancellation_rate=0.4,
        baseline_cancellation_rate=0.2,
        cancellation_rate_change=0.2,
        observed_avg_review_score=3.73,
        baseline_avg_review_score=3.94,
        avg_review_score_change=-0.21,
    )

    return RootCauseInvestigationResponse(
        request=req,
        summary=summary,
        decomposition=decomp,
        ranked_contributors=contributors,
        operational_indicators=ops,
        explanation="TOTAL_GMV increased +384.2% on 2017-11-24.",
        limitations="These findings identify associations, not causal relationships.",
    )


# 1. Test Evidence Extraction and Immutability
def test_evidence_extraction_preserves_numbers(
    sample_root_cause_response: RootCauseInvestigationResponse,
) -> None:
    """Test that numbers extracted into the payload match exactly."""
    evidence = extract_evidence_payload(sample_root_cause_response)

    assert evidence.metric == "total_gmv"
    assert evidence.anomaly_date == "2017-11-24"
    assert evidence.observed_value == 152653.74
    assert evidence.baseline_value == 31524.93
    assert evidence.percentage_change == 384.2
    assert evidence.orders_observed == 1176.0
    assert evidence.orders_baseline == 207.0
    assert evidence.volume_effect == 147944.71
    assert len(evidence.top_contributors) == 1
    assert evidence.top_contributors[0]["dimension_value"] == "SP"

    # Verify original response was not modified
    assert sample_root_cause_response.summary.observed_value == 152653.74


# 2. Test Prompt Construction
def test_build_investigation_prompt_structure(
    sample_root_cause_response: RootCauseInvestigationResponse,
) -> None:
    """Test that prompt contains the verified evidence payload."""
    evidence = extract_evidence_payload(sample_root_cause_response)
    prompt = build_investigation_prompt(evidence)

    assert "VERIFIED EVIDENCE PAYLOAD:" in prompt
    assert "152653.74" in prompt
    assert "total_gmv" in prompt
    assert "SP" in prompt


# 3. Test Successful Generation with Mocked LLM Provider
def test_investigate_with_mocked_llm_provider(
    sample_root_cause_response: RootCauseInvestigationResponse,
) -> None:
    """Test successful generation using a mocked LLMProvider."""
    mock_provider = MagicMock()
    mock_provider.model = "mock-gpt-4o"
    mock_provider.generate.return_value = json.dumps(
        {
            "investigation_title": "Executive Memo: GMV Spike on 2017-11-24",
            "executive_summary": (
                "GMV surged +384.2% driven primarily by order volume expansion."
            ),
            "key_findings": [
                "Total GMV reached R$ 152,653.74 versus R$ 31,524.93 baseline.",
                "Orders increased by +469.3%.",
            ],
            "business_interpretation": [
                "Demand surge aligned with Black Friday holiday commercial event."
            ],
            "recommended_actions": [
                "Maintain sufficient fulfillment staffing for post-event dispatch."
            ],
            "limitations": ["Identifies statistical contributions, not causal proof."],
        }
    )

    ai_resp = investigate_with_ai(
        root_cause_response=sample_root_cause_response,
        provider=mock_provider,
    )

    assert isinstance(ai_resp, AIInvestigationResponse)
    assert ai_resp.investigation_title == "Executive Memo: GMV Spike on 2017-11-24"
    assert len(ai_resp.key_findings) == 2
    assert ai_resp.is_fallback is False
    assert "Black Friday" in ai_resp.business_interpretation[0]


# 4. Test Valid Real-Provider Response with Mocked HTTP
@patch("httpx.Client.post")
def test_openai_compatible_provider_mocked_http_success(
    mock_post: MagicMock,
) -> None:
    """Test OpenAICompatibleProvider handles valid HTTP response."""
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "investigation_title": "Executive Memo",
                                "executive_summary": "GMV surged.",
                                "key_findings": ["Finding 1"],
                                "business_interpretation": ["Interpretation"],
                                "recommended_actions": ["Action 1"],
                                "limitations": ["Correlation only"],
                            }
                        )
                    }
                }
            ]
        },
    )

    provider = OpenAICompatibleProvider(api_key="sk-test-key-12345")
    raw_response = provider.generate("Test prompt")
    data = json.loads(raw_response)
    assert data["investigation_title"] == "Executive Memo"


# 5. Test Missing API Key Raises Error on Direct OpenAI Provider Init
def test_missing_api_key_raises_value_error() -> None:
    """Test OpenAICompatibleProvider requires API key."""
    with pytest.raises(ValueError, match="LLM_API_KEY is not configured"):
        OpenAICompatibleProvider(api_key="")


# 6. Test Provider Timeout / Network Failure Fallback Safety
def test_provider_timeout_falls_back_safely(
    sample_root_cause_response: RootCauseInvestigationResponse,
) -> None:
    """Test that provider timeout exception falls back cleanly without crashing."""
    mock_provider = MagicMock()
    mock_provider.generate.side_effect = TimeoutError("Request timed out")

    ai_resp = investigate_with_ai(
        root_cause_response=sample_root_cause_response,
        provider=mock_provider,
    )

    assert isinstance(ai_resp, AIInvestigationResponse)
    assert ai_resp.is_fallback is True
    assert ai_resp.model == "deterministic-rule-synthesizer"


# 7. Test Malformed LLM Response Fallback Safety
def test_malformed_llm_response_falls_back_safely(
    sample_root_cause_response: RootCauseInvestigationResponse,
) -> None:
    """Test that malformed JSON from the LLM triggers fallback without crashing."""
    mock_provider = MagicMock()
    mock_provider.generate.return_value = "NOT VALID JSON AT ALL!!!"

    ai_resp = investigate_with_ai(
        root_cause_response=sample_root_cause_response,
        provider=mock_provider,
    )

    assert isinstance(ai_resp, AIInvestigationResponse)
    assert ai_resp.is_fallback is True
    assert "TOTAL_GMV" in ai_resp.executive_summary
    assert len(ai_resp.key_findings) >= 2


# 8. Test Deterministic Fallback Provider Directly
def test_deterministic_fallback_provider_directly(
    sample_root_cause_response: RootCauseInvestigationResponse,
) -> None:
    """Test DeterministicFallbackProvider executes completely offline."""
    provider = DeterministicFallbackProvider()
    evidence = extract_evidence_payload(sample_root_cause_response)
    prompt = build_investigation_prompt(evidence)

    raw_json = provider.generate(prompt=prompt)
    data = json.loads(raw_json)

    assert "investigation_title" in data
    assert "TOTAL_GMV" in data["executive_summary"]
    assert "+384.2%" in data["executive_summary"]
    assert len(data["recommended_actions"]) >= 2


# 9. Test Empty Contributor List Handling
def test_empty_contributors_handling(
    sample_root_cause_response: RootCauseInvestigationResponse,
) -> None:
    """Test that empty contributor lists generate valid responses without error."""
    sample_root_cause_response.ranked_contributors = []
    ai_resp = investigate_with_ai(
        root_cause_response=sample_root_cause_response,
        provider=DeterministicFallbackProvider(),
    )

    assert isinstance(ai_resp, AIInvestigationResponse)
    assert "TOTAL_GMV" in ai_resp.executive_summary


# 10. Test Immutability of Evidence Under Investigation
def test_evidence_immutability_under_investigation(
    sample_root_cause_response: RootCauseInvestigationResponse,
) -> None:
    """Verify that calling investigate_with_ai does not mutate source data."""
    initial_val = sample_root_cause_response.summary.observed_value
    initial_decomp = sample_root_cause_response.decomposition.volume_effect  # type: ignore[union-attr]

    ai_resp = investigate_with_ai(sample_root_cause_response)

    assert sample_root_cause_response.summary.observed_value == initial_val
    assert (
        sample_root_cause_response.decomposition.volume_effect  # type: ignore[union-attr]
        == initial_decomp
    )
    assert isinstance(ai_resp, AIInvestigationResponse)
