import ollama
import sys

MODEL_TO_CHECK = 'mxbai-embed-large'

def main():
    """
    A simple diagnostic tool to check the connection to Ollama and model availability.
    """
    print("--- Ollama Connection Diagnostic Tool ---")

    try:
        # 1. List local models to check for the required model
        print(f"\n[1/3] Checking for local model: '{MODEL_TO_CHECK}'...")
        local_models = ollama.list()['models']
        
        model_found = any(model['name'].startswith(MODEL_TO_CHECK) for model in local_models)
        
        if model_found:
            print(f"  ✓ SUCCESS: Model '{MODEL_TO_CHECK}' is available locally.")
        else:
            print(f"  ✗ FAILURE: Model '{MODEL_TO_CHECK}' not found locally.")
            print("      Available models:")
            if not local_models:
                print("        - No models found.")
            else:
                for model in local_models:
                    print(f"        - {model['name']}")
            print("\n      Suggestion: Run 'ollama pull {MODEL_TO_CHECK}' in your terminal.")
            sys.exit(1)

        # 2. Try to generate a test embedding
        print(f"\n[2/3] Attempting to generate a test embedding with '{MODEL_TO_CHECK}'...")
        test_prompt = "This is a test."
        response = ollama.embeddings(model=MODEL_TO_CHECK, prompt=test_prompt)
        
        if response.get("embedding") and len(response.get("embedding")) > 0:
            print(f"  ✓ SUCCESS: Successfully generated a test embedding.")
            print(f"      Vector dimension: {len(response.get('embedding'))}")
        else:
            print("  ✗ FAILURE: API call succeeded but did not return a valid embedding.")
            print(f"      Response: {response}")
            sys.exit(1)

        # 3. Check client connectivity
        print("\n[3/3] Verifying client connection...")
        client = ollama.Client()
        client.heartbeat()
        print("  ✓ SUCCESS: Ollama server is responsive.")

    except Exception as e:
        print(f"\n--- DIAGNOSTIC FAILED ---")
        print(f"An error occurred: {e}")
        print("\nPossible causes and suggestions:")
        print("  1. Is the Ollama service running? Check the 'Ollama Service' terminal window.")
        print("  2. Is there a network issue or firewall blocking the connection to http://localhost:11434?")
        print("  3. Did the Ollama service start correctly? Check for error messages in its terminal.")
        sys.exit(1)

    print("\n--- Diagnosis Complete: All checks passed! ---")
    print("Your Python environment can successfully connect to the Ollama service and use the required model.")

if __name__ == "__main__":
    main()
