/**
 * Shared helpers for local LLM provider state.
 * Fleet contract: provider/model selection persists under llm_provider / llm_model.
 */

export const LLM_PROVIDER_KEY = "llm_provider";
export const LLM_MODEL_KEY = "llm_model";

export function readStoredLlm(
  defaultProvider = "local",
  defaultModel = "",
): {
  provider: string;
  model: string;
} {
  let provider = defaultProvider;
  let model = defaultModel;
  try {
    provider = localStorage.getItem(LLM_PROVIDER_KEY) || defaultProvider;
    model = localStorage.getItem(LLM_MODEL_KEY) || defaultModel;
  } catch {
    /* private mode */
  }
  return { provider, model };
}

export function persistLlm(provider: string, model: string): void {
  try {
    localStorage.setItem(LLM_PROVIDER_KEY, provider);
    localStorage.setItem(LLM_MODEL_KEY, model);
  } catch {
    /* private mode */
  }
}
