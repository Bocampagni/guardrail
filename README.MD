<p align="center">
   <img src="./docs/images/guardrail_logo.png"  width="250">
</p>

# Guardrail

**Guardrail** is a robust framework designed to detect and prevent adversarial threats, prompt injections, and other security vulnerabilities in generative AI models. It leverages a combination of semantic similarity analysis, anomaly detection, entropy calculations, and validation models to ensure that only safe queries are processed.

# Modules
### Sanitization
Uses the `Sanitize` module to check if the prompt contains invisible characters. If so, the prompt is immediately blocked with the reason `"invisible characters"`.

### Embedding Similarity
The `query_malicious_similarity(query)` method generates an embedding for the prompt and compares it with embeddings of known attacks. If the similarity exceeds the defined threshold, the prompt is blocked with the justification `"malicious similarity above threshold"`.

### Anomaly Detection
Through the `query_anomaly_detection(query)` method, the prompt is transformed into a vector and analyzed by an anomaly detection model. If the result indicates `"Anomaly"` with a score suggesting atypical behavior, the prompt is blocked with the reason `"anomaly score above threshold"`.

### Entropy Analysis
The `query_entropy(query)` method calculates the entropy of the prompt using NLTK tokenization. High entropy may indicate suspicious patterns, and if it exceeds the threshold, the prompt is blocked with the reason `"entropy score above threshold"`.

### Validation by Language Model
Finally, the `invoke_validation_model(query)` method calls the DeBERTa model to classify the prompt. If the model classifies the prompt as `"INJECTION"`, it is blocked with the reason `"validation model block"`.


# Install
```bash
git clone https://github.com/Bocampagni/guardrail.git
cd guardrail
pip install -r requirements.txt
```

# License 
This project is licensed under the MIT License. Please refer to the LICENSE file for detailed information.

# Future work
Monitoring on blocked queries can be persisted using Langfuse or Langsmith clients, which can be injected in `Guardrail` class. It's important to note that both must have some common interface in order to work in a transparent way.

I may upload this to Pypi, but re-work on abstractions should be done first.
