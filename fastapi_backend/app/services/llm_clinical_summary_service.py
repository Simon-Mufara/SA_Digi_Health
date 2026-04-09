from app.core.config import settings


class LLMClinicalSummaryService:
    @staticmethod
    def generate_clinical_summary(
        diagnoses: list[str],
        medications: list[str],
        recent_visit_statuses: list[str],
        risk_factors: list[str],
    ) -> str:
        prompt = LLMClinicalSummaryService._build_prompt(
            diagnoses=diagnoses,
            medications=medications,
            recent_visit_statuses=recent_visit_statuses,
            risk_factors=risk_factors,
        )

        if settings.llm_provider.lower() == "mock":
            return LLMClinicalSummaryService._mock_completion(prompt)

        return LLMClinicalSummaryService._mock_completion(prompt)

    @staticmethod
    def _build_prompt(
        diagnoses: list[str],
        medications: list[str],
        recent_visit_statuses: list[str],
        risk_factors: list[str],
    ) -> str:
        diagnosis_text = ", ".join(diagnoses) if diagnoses else "none"
        medication_text = ", ".join(medications) if medications else "none"
        visit_text = ", ".join(recent_visit_statuses) if recent_visit_statuses else "none"
        risk_text = ", ".join(risk_factors) if risk_factors else "none"

        return (
            "Generate a concise clinical summary for a doctor using structured patient data. "
            "Highlight important history and risk factors. Keep it under 80 words. "
            f"Diagnoses: {diagnosis_text}. "
            f"Medications: {medication_text}. "
            f"Recent visit statuses: {visit_text}. "
            f"Risk factors: {risk_text}."
        )

    @staticmethod
    def _mock_completion(prompt: str) -> str:
        # Placeholder deterministic local implementation for production wiring.
        return "Clinical summary: " + prompt.split("Diagnoses:", 1)[-1].strip()