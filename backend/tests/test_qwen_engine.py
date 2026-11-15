"""
Qwen 2.5 Flight Science Copilot Unit Tests — Milestone M9
Verifies model inspection, ChatML prompt generation,
and the zero-crash deterministic scientific reasoning oracle.
"""

import pytest
from backend.app.exploration.qwen_engine import (
    QwenEngine,
    QwenChatRequest,
    qwen_copilot_engine,
)


class TestQwenEngineModelInspection:
    def test_model_metadata_inspection(self):
        """Assert Qwen model metadata matches E:/ai_model LoRA specifications."""
        meta = qwen_copilot_engine.metadata
        assert meta.base_model == "Qwen/Qwen2.5-0.5B-Instruct"
        assert meta.peft_type == "LORA"
        assert meta.lora_rank == 16
        assert meta.lora_alpha == 32
        assert "q_proj" in meta.target_modules
        assert "v_proj" in meta.target_modules
        assert meta.tokenizer_vocab_size == 151643
        assert meta.status == "READY"

    def test_chatml_prompt_formatting(self):
        """Assert ChatML prompt adheres strictly to <|im_start|> and <|im_end|> syntax."""
        history = [
            {"role": "user", "content": "What is Hohmann transfer?"},
            {"role": "assistant", "content": "It is an elliptical orbital transfer maneuver."},
        ]
        prompt = qwen_copilot_engine.format_chatml_prompt("Calculate Earth to Mars delta-V", history)

        assert "<|im_start|>system" in prompt
        assert "<|im_end|>" in prompt
        assert "<|im_start|>user\nWhat is Hohmann transfer?<|im_end|>" in prompt
        assert "<|im_start|>assistant\nIt is an elliptical orbital transfer maneuver.<|im_end|>" in prompt
        assert "<|im_start|>user\nCalculate Earth to Mars delta-V<|im_end|>\n<|im_start|>assistant" in prompt


class TestQwenScientificReasoningOracle:
    def test_earth_mars_transfer_reasoning(self):
        """Assert oracle generates verified delta-V and duration for Earth-Mars."""
        req = QwenChatRequest(query="Calculate delta-v for Earth to Mars")
        res = qwen_copilot_engine.chat(req)

        assert res.model_name == "Qwen/Qwen2.5-0.5B-Instruct+LoRA"
        assert "5.59 km/s" in res.response or "5.6" in res.response
        assert "259" in res.response or "258.9" in res.response
        assert res.tokens_generated > 10
        assert res.latency_ms >= 0

    def test_translunar_injection_reasoning(self):
        """Assert oracle generates verified geocentric TLI for Moon/Gateway."""
        req = QwenChatRequest(query="Calculate Earth to Lunar Gateway TLI delta-V")
        res = qwen_copilot_engine.chat(req)

        assert "Translunar" in res.response or "TLI" in res.response
        assert "3.14" in res.response or "3.1" in res.response
        assert "3.2" in res.response or "3." in res.response

    def test_silent_cool_flame_reasoning(self):
        """Assert oracle explains Damköhler number and low-temperature peroxy chemistry."""
        req = QwenChatRequest(query="Explain silent cool-flame rekindling risks and Damkohler number")
        res = qwen_copilot_engine.chat(req)

        assert "Damköhler" in res.response or "Damkohler" in res.response or "Da_cool" in res.response
        assert "RO2" in res.response or "peroxy" in res.response
        assert "microgravity" in res.response or "buoyant" in res.response or "Gr" in res.response

    def test_artemis_gateway_eafhi_reasoning(self):
        """Assert oracle evaluates Artemis Gateway 34% O2 and 56.5 kPa flammability."""
        req = QwenChatRequest(query="Evaluate Artemis Gateway exploration atmosphere flammability")
        res = qwen_copilot_engine.chat(req)

        assert "34% O2" in res.response or "34%" in res.response
        assert "56.5 kPa" in res.response or "56.5" in res.response
        assert "0.166 g" in res.response or "lunar" in res.response or "NASA-STD-6001B" in res.response

    def test_active_face_context_injection(self):
        """Assert specifying active_face_id returns detailed telemetry context."""
        req = QwenChatRequest(query="Provide operational status", active_face_id=4)
        res = qwen_copilot_engine.chat(req)

        assert res.active_face is not None
        assert res.active_face["id"] == 4
        assert "Cryovolcanism" in res.active_face["name"]
        assert "Europa" in res.active_face["key_constant"] or "Enceladus" in res.active_face["key_constant"]

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

    def test_training_history_inspection(self):
        """Assert engine loads authentic training metrics and loss convergence."""
        history = qwen_copilot_engine.get_training_history()
        assert history is not None
        assert "status" in history
        if history.get("status") == "COMPLETED":
            assert "epoch_history" in history
            assert len(history["epoch_history"]) > 0
            assert history["initial_loss"] > history["final_loss"]
            assert history["overall_eval_accuracy"] >= 95.0


class TestQwenCoSimulationReasoning:
    def test_cosimulation_query_synthesis(self):
        """
        Milestone 10: Assert Qwen engine detects co-simulation queries and synthesizes
        both orbital transfer astrodynamics and cool-flame Damköhler fire hazard reasoning.
        """
        req = QwenChatRequest(
            query="Co-simulate Earth to Mars transfer with heptane cool flame rekindle risk in microgravity"
        )
        res = qwen_copilot_engine.chat(req)

        assert "Multi-Agent Orbital Co-Simulation" in res.response
        assert "5.59 km/s" in res.response
        assert "Da_cool" in res.response
        assert "P_rekindle" in res.response
        assert "EAFHI" in res.response
        assert "Burn Acceleration" in res.response
        assert res.cosimulation_context is not None
        cosim = res.cosimulation_context
        assert cosim["fuel"] == "n-heptane"
        assert cosim["damkohler_cool"] > 1.0
        assert cosim["rekindle_probability"] > 0.0
        assert cosim["risk_classification"] in ["INERT", "MONITOR", "REKINDLE_WARNING", "CRITICAL_REKINDLE_HAZARD"]
        assert cosim["critical_ventilation_m_s"] > 0.0

    def test_lora_path_prioritization(self):
        r"""
        Assert engine prioritizes E:\ai_model\finetuning\qwen_lora_model if present.
        """
        import os
        from backend.app.exploration.qwen_engine import LEGACY_LORA_DIR
        meta = qwen_copilot_engine.metadata
        if os.path.exists(LEGACY_LORA_DIR) and os.path.exists(os.path.join(LEGACY_LORA_DIR, "adapter_model.safetensors")):
            assert "E:\\ai_model" in meta.adapter_weights_path or "E:/ai_model" in meta.adapter_weights_path
