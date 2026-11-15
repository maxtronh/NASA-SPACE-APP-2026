"""
Qwen 2.5 Flight Science Copilot Unit Tests — Milestone M9
Verifies model inspection (honest metadata), ChatML prompt generation,
and the deterministic structured scientific reasoning oracle.
"""

import pytest
from backend.app.exploration.qwen_engine import (
    QwenEngine,
    QwenChatRequest,
    qwen_copilot_engine,
)


class TestQwenEngineModelInspection:
    def test_model_metadata_inspection(self):
        """Assert Qwen model metadata matches the on-disk LoRA adapter specs."""
        meta = qwen_copilot_engine.metadata
        assert meta.base_model == "Qwen/Qwen2.5-0.5B-Instruct"
        assert meta.peft_type == "LORA"
        assert meta.lora_rank == 16
        assert meta.lora_alpha == 32
        assert "q_proj" in meta.target_modules
        assert "v_proj" in meta.target_modules
        assert meta.tokenizer_vocab_size == 151643
        # Honest disclosure: adapter present on disk, but no live model loaded.
        assert meta.adapter_present is True
        assert meta.model_loaded is False
        assert meta.status == "ADAPTER_PRESENT_FALLBACK_MODE"
        assert meta.inference_capability == "deterministic_scientific_fallback_only"

    def test_model_not_loaded_disclosure(self):
        """Assert the engine honestly reports no live inference capability."""
        assert qwen_copilot_engine.model_loaded is False
        assert qwen_copilot_engine.adapter_present is True
        assert qwen_copilot_engine.metadata.model_loaded is False

    def test_chatml_prompt_formatting(self):
        """Assert ChatML prompt adheres to <|system|>/<|end|> syntax."""
        history = [
            {"role": "user", "content": "What is Hohmann transfer?"},
            {"role": "assistant", "content": "It is an elliptical orbital transfer maneuver."},
        ]
        prompt = qwen_copilot_engine.format_chatml_prompt(
            "Calculate Earth to Mars delta-V", history
        )

        assert "<|system|>" in prompt
        assert "<|end|>" in prompt
        assert "<|user|>\nWhat is Hohmann transfer?<|end|>" in prompt
        assert "<|assistant|>\nIt is an elliptical orbital transfer maneuver.<|end|>" in prompt
        assert "<|user|>\nCalculate Earth to Mars delta-V<|end|>\n<|assistant|>" in prompt


class TestQwenScientificReasoningOracle:
    def test_earth_mars_transfer_sections(self):
        """Assert oracle returns structured sections for Earth-Mars Hohmann."""
        req = QwenChatRequest(query="Calculate delta-v for Earth to Mars")
        res = qwen_copilot_engine.chat(req)

        assert res.inference_mode == "deterministic_scientific_fallback"
        assert res.model_loaded is False
        assert res.adapter_present is True
        assert len(res.sections) >= 6
        kinds = {s.kind for s in res.sections}
        assert {"explanation", "formulas", "evidence", "proof", "api", "operations"} <= kinds
        # Evidence-grounded numeric values.
        assert "5.59" in res.response or "5.6" in res.response
        assert "258" in res.response or "259" in res.response
        assert res.tokens_generated > 10
        assert res.latency_ms >= 0
        assert res.api_path == "POST /api/v1/exploration/trajectory/calculate"

    def test_translunar_injection_sections(self):
        """Assert oracle returns structured sections for geocentric TLI."""
        req = QwenChatRequest(query="Calculate Earth to Lunar Gateway TLI delta-V")
        res = qwen_copilot_engine.chat(req)

        assert res.inference_mode == "deterministic_scientific_fallback"
        assert "Translunar" in res.response or "TLI" in res.response
        assert "3.14" in res.response or "3.1" in res.response
        assert "3.2" in res.response or "3." in res.response
        assert res.api_path == "POST /api/v1/exploration/trajectory/calculate"
        ops = next((s for s in res.sections if s.kind == "operations"), None)
        assert ops is not None and "3.2" in ops.body

    def test_silent_cool_flame_sections(self):
        """Assert oracle explains Damköhler number and low-temperature peroxy chemistry."""
        req = QwenChatRequest(query="Explain silent cool-flame rekindling risks and Damkohler number")
        res = qwen_copilot_engine.chat(req)

        assert res.inference_mode == "deterministic_scientific_fallback"
        assert "Damköhler" in res.response or "Damkohler" in res.response or "Da_cool" in res.response
        assert "RO2" in res.response or "peroxy" in res.response
        assert "microgravity" in res.response or "buoyant" in res.response or "Gr" in res.response
        da = next((s for s in res.sections if s.kind == "formulas"), None)
        assert da is not None and "Da_cool" in da.body
        api = next((s for s in res.sections if s.kind == "api"), None)
        assert api is not None and "/api/v1/exploration/copilot/chat" in api.api_path

    def test_artemis_gateway_eafhi_sections(self):
        """Assert oracle evaluates Artemis Gateway 34% O2 and 56.5 kPa flammability."""
        req = QwenChatRequest(query="Evaluate Artemis Gateway exploration atmosphere flammability")
        res = qwen_copilot_engine.chat(req)

        assert res.inference_mode == "deterministic_scientific_fallback"
        assert "34% O2" in res.response or "34%" in res.response
        assert "56.5 kPa" in res.response or "56.5" in res.response
        assert "0.166 g" in res.response or "lunar" in res.response or "NASA-STD-6001B" in res.response
        assert res.api_path == "POST /api/v1/safety/evaluate"
        eafhi = next((s for s in res.sections if s.kind == "formulas"), None)
        assert eafhi is not None and "clip" in eafhi.body and "0.0, 1.0" in eafhi.body

    def test_d2_law_sections(self):
        """Assert oracle explains droplet d²-law burning."""
        req = QwenChatRequest(query="Explain zero-gravity spherical droplet d2-law burning")
        res = qwen_copilot_engine.chat(req)

        assert res.inference_mode == "deterministic_scientific_fallback"
        assert "d²" in res.response or "d2" in res.response.lower()
        assert "0.428" in res.response
        d2 = next((s for s in res.sections if s.kind == "formulas"), None)
        assert d2 is not None and "d²(t)" in d2.body or "d^2" in d2.body.lower()

    def test_qwen_lora_honest_disclosure_sections(self):
        """Assert oracle reports Qwen/LoRA honestly with no live inference."""
        req = QwenChatRequest(query="Explain Qwen 2.5 LoRA model and adapter")
        res = qwen_copilot_engine.chat(req)

        assert res.inference_mode == "deterministic_scientific_fallback"
        assert "peft" in res.response.lower() or "not installed" in res.response.lower()
        assert "deterministic_scientific_fallback" in res.response.lower()
        model_sec = next((s for s in res.sections if s.kind == "explanation"), None)
        assert model_sec is not None and "NOT available" in model_sec.body
        assert res.api_path == "GET /api/v1/exploration/model/metadata"

    def test_active_face_context_injection(self):
        """Assert specifying active_face_id returns detailed telemetry context."""
        req = QwenChatRequest(query="Provide operational status", active_face_id=4)
        res = qwen_copilot_engine.chat(req)

        assert res.active_face is not None
        assert res.active_face["id"] == 4
        assert "Cryovolcanism" in res.active_face["name"]
        assert "Europa" in res.active_face["key_constant"] or "Enceladus" in res.active_face["key_constant"]
        assert res.api_path is not None and "/faces-25/" in res.api_path

    def test_zero_crash_on_edge_queries(self):
        """Assert engine never raises an unhandled exception even on abnormal inputs."""
        edge_queries = [
            "",
            "   ",
            "???!!!",
            "1234567890",
            "DROP TABLE users;",
            "A" * 1000,
        ]
        for eq in edge_queries:
            req = QwenChatRequest(query=eq)
            res = qwen_copilot_engine.chat(req)
            assert res is not None
            assert len(res.response) > 0
            assert res.latency_ms < 100.0
            assert res.inference_mode == "deterministic_scientific_fallback"

    def test_training_history_inspection(self):
        """Assert engine loads training metrics file or reports absence honestly."""
        history = qwen_copilot_engine.get_training_history()
        assert history is not None
        assert "status" in history
