"""Tests for llm_provider, the Groq/vLLM abstraction.

Two properties matter most here.

First, defaults must reproduce current Groq behaviour exactly. An unconfigured
deployment has to behave as it did before this module existed, because the same
codebase serves production and the migration environment.

Second, error classification must work against both providers. The previous
implementation matched only Groq's error text. Against vLLM the model-not-found
strings would not have matched, so the extractor fallback in mi_evaluation would
never have triggered and the whole evaluation would have failed instead of
quietly retrying. The vLLM message shapes are pinned below so that regression
cannot return silently.
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import llm_provider


MANAGED_VARS = (
    "MI_LLM_BASE_URL",
    "MI_LLM_API_KEY",
    "MI_LLM_CHAT_MODEL",
    "MI_LLM_EVAL_MODEL",
    "MI_LLM_EXTRACTOR_MODEL",
    "MI_LLM_TIMEOUT_S",
    "MI_LLM_EVAL_TIMEOUT_S",
    "MI_LLM_MAX_RETRIES",
    "GROQ_API_KEY",
)


class ProviderTestCase(unittest.TestCase):
    def setUp(self):
        self._saved = {n: os.environ.get(n) for n in MANAGED_VARS}
        for n in MANAGED_VARS:
            os.environ.pop(n, None)

    def tearDown(self):
        for n, v in self._saved.items():
            if v is None:
                os.environ.pop(n, None)
            else:
                os.environ[n] = v


class TestDefaultsReproduceGroq(ProviderTestCase):
    def test_base_url_defaults_to_groq(self):
        self.assertEqual(
            llm_provider.load_settings().base_url,
            "https://api.groq.com/openai/v1",
        )

    def test_model_defaults_match_the_names_the_suite_asserts(self):
        s = llm_provider.load_settings()
        # These exact strings are asserted by test_evaluation.py and
        # tests/test_mi_evaluation.py. Changing them breaks those tests, which
        # is the intended tripwire.
        self.assertEqual(s.chat_model, "llama-3.1-8b-instant")
        self.assertEqual(s.extractor_model, "llama-3.1-8b-instant")
        self.assertEqual(s.eval_model, "llama-3.3-70b-versatile")

    def test_is_groq_is_true_by_default(self):
        self.assertTrue(llm_provider.load_settings().is_groq)

    def test_evaluator_gets_a_longer_timeout_than_chat(self):
        s = llm_provider.load_settings()
        self.assertGreater(s.eval_timeout_s, s.timeout_s)

    def test_evaluator_has_a_token_cap(self):
        # vLLM defaults generation to the remaining context window, so an
        # unbounded evaluator call can run for minutes.
        s = llm_provider.load_settings()
        self.assertIsNotNone(s.eval_max_tokens)
        self.assertGreater(s.eval_max_tokens, 0)


class TestEnvironmentOverrides(ProviderTestCase):
    def test_base_url_override_switches_provider(self):
        os.environ["MI_LLM_BASE_URL"] = "http://cn1234:8000/v1"
        s = llm_provider.load_settings()
        self.assertEqual(s.base_url, "http://cn1234:8000/v1")
        self.assertFalse(s.is_groq)

    def test_model_overrides_are_honoured(self):
        os.environ["MI_LLM_CHAT_MODEL"] = "chat-8b"
        os.environ["MI_LLM_EVAL_MODEL"] = "eval-70b"
        os.environ["MI_LLM_EXTRACTOR_MODEL"] = "extract-8b"
        s = llm_provider.load_settings()
        self.assertEqual(s.chat_model, "chat-8b")
        self.assertEqual(s.eval_model, "eval-70b")
        self.assertEqual(s.extractor_model, "extract-8b")

    def test_explicit_api_key_wins_over_environment(self):
        # Preserves today's per-student credential model, where the key comes
        # from Streamlit session state rather than the environment.
        os.environ["MI_LLM_API_KEY"] = "from-env"
        self.assertEqual(llm_provider.load_settings("from-caller").api_key, "from-caller")

    def test_falls_back_to_groq_api_key_for_existing_deployments(self):
        os.environ["GROQ_API_KEY"] = "legacy"
        self.assertEqual(llm_provider.load_settings().api_key, "legacy")

    def test_numeric_overrides_survive_garbage(self):
        os.environ["MI_LLM_TIMEOUT_S"] = "not-a-number"
        os.environ["MI_LLM_MAX_RETRIES"] = ""
        s = llm_provider.load_settings()
        self.assertEqual(s.timeout_s, 30.0)
        self.assertEqual(s.max_retries, 2)


class TestClientSurface(ProviderTestCase):
    def test_client_exposes_chat_completions_create(self):
        # More than twenty tests drive this exact path through FakeClient. If
        # the abstraction ever wraps it in a bespoke facade, they all break.
        client = llm_provider.make_client(llm_provider.load_settings("k"))
        self.assertTrue(hasattr(client, "chat"))
        self.assertTrue(hasattr(client.chat, "completions"))
        self.assertTrue(callable(client.chat.completions.create))

    def test_client_builds_without_a_credential(self):
        # vLLM commonly ignores the credential, but the SDK requires a
        # non-empty value, so a placeholder is substituted.
        client = llm_provider.make_client(llm_provider.load_settings())
        self.assertIsNotNone(client)


class TestUnknownModelClassification(ProviderTestCase):
    """The failure mode that motivated this module."""

    def test_matches_groq_phrasing(self):
        self.assertTrue(
            llm_provider.is_unknown_model(
                Exception("model_not_found: The model does not exist")
            )
        )

    def test_matches_vllm_phrasing(self):
        # vLLM returns: The model `llama-3.1-8b-instant` does not exist.
        self.assertTrue(
            llm_provider.is_unknown_model(
                Exception("The model `llama-3.1-8b-instant` does not exist.")
            )
        )

    def test_matches_a_404_by_status_code(self):
        class Failure(Exception):
            status_code = 404

        self.assertTrue(llm_provider.is_unknown_model(Failure("something")))

    def test_does_not_match_unrelated_errors(self):
        self.assertFalse(llm_provider.is_unknown_model(Exception("rate limited")))
        self.assertFalse(llm_provider.is_unknown_model(Exception("bad gateway")))


class TestOtherClassifiers(ProviderTestCase):
    def test_unsupported_response_format(self):
        self.assertTrue(
            llm_provider.is_unsupported_response_format(
                Exception("response_format is not supported")
            )
        )
        self.assertTrue(
            llm_provider.is_unsupported_response_format(
                Exception("json_object mode unavailable")
            )
        )
        self.assertFalse(
            llm_provider.is_unsupported_response_format(Exception("timeout"))
        )

    def test_auth_errors(self):
        self.assertTrue(llm_provider.is_auth_error(Exception("401 Unauthorized")))
        self.assertTrue(llm_provider.is_auth_error(Exception("Invalid API Key")))
        self.assertTrue(llm_provider.is_auth_error(Exception("authentication failed")))
        self.assertFalse(llm_provider.is_auth_error(Exception("model not found")))

    def test_auth_error_by_status_code(self):
        class Failure(Exception):
            status_code = 403

        self.assertTrue(llm_provider.is_auth_error(Failure("denied")))

    def test_retryable_is_false_for_plain_exceptions(self):
        self.assertFalse(llm_provider.is_retryable(Exception("nope")))


class TestDescribeEndpoint(ProviderTestCase):
    def test_describes_groq(self):
        self.assertIn("Groq", llm_provider.describe_endpoint())

    def test_describes_self_hosted(self):
        os.environ["MI_LLM_BASE_URL"] = "http://cn1234:8000/v1"
        described = llm_provider.describe_endpoint()
        self.assertIn("self-hosted", described)
        self.assertIn("cn1234", described)


if __name__ == "__main__":
    unittest.main()
