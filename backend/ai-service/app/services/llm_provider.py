import logging
from app.services.interfaces import LLMProvider

logger = logging.getLogger(__name__)


class HuggingFaceLLMProvider(LLMProvider):
    """
    Downloads and runs a small causal LM directly from Hugging Face (transformers).
    Requires network access to huggingface.co on first run (weights are cached locally after that).
    """

    def __init__(self, model_name: str):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        logger.info(f"Loading Hugging Face model: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, torch_dtype=torch.float32
        )
        self.model.eval()
        logger.info("Model loaded successfully")

    def generate(self, prompt: str, max_new_tokens: int = 120) -> str:
        import torch

        messages = [{"role": "user", "content": prompt}]
        inputs = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
        )
        with torch.no_grad():
            output = self.model.generate(
                **inputs, max_new_tokens=max_new_tokens, do_sample=False
            )
        text = self.tokenizer.decode(
            output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True
        )
        return text.strip()


class MockLLMProvider(LLMProvider):
    """No network/model download required — used for local dev, tests, and CI."""

    def generate(self, prompt: str, max_new_tokens: int = 120) -> str:
        return (
            "[MOCK EXPLANATION] Based on course title and content overlap, "
            "this prior course appears to satisfy the equivalent Adelaide course requirement."
        )


def get_llm_provider(provider_name: str, model_name: str) -> LLMProvider:
    if provider_name == "huggingface":
        return HuggingFaceLLMProvider(model_name)
    if provider_name == "mock":
        return MockLLMProvider()
    raise ValueError(f"Unknown LLM provider: {provider_name}")
