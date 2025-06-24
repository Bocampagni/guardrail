<p align="center">
  <img src="docs/images/guardrail_logo.png" />
</p>
A small, modular, fast and scalable barebones GenAi security pipeline solution. Guadrail is designed to be a simple and effective way to block malicious prompts in GenAI applications. It uses a combination of techniques including sanitization, embedding similarity, anomaly detection, entropy analysis, and validation by a language model.

It features two main modes of operation: `pipeline` and `Mixture of Experts`. In the `pipeline` mode, the prompt is processed sequentially through each module, blocking it if any module detects a malicious prompt. In the `Mixture of Experts` mode, each module runs independently and the final decision is made based on a ensemble of the results from each module. The `decision_threshold` parameter controls the sensitivity of the ensemble decision.

All the metadata used to configure Guadrail should be inferred from your usage. Guadrail was designed to be used as a contextual security layer, meaning that it should be used in conjunction with your application data. I.e you should use your own data to infer the values of `similarity_upper_bound`, `anomaly_upper_bound`, `entropy_upper_bound`, and `decision_threshold` in order to achieve the best results. All fields of knowledge should have its own nuances, and Guadrail is designed to be flexible enough to adapt to your specific use case.

## Installation
```bash
git clone git@github.com:Bocampagni/guardrail.git
cd guardrail
uv sync
uv run example.py
```



### Sanitization
Uses the `Sanitize.contains_invisible_characters()` function to detect invisible Unicode characters commonly used in prompt injection attacks. This serves as the first line of defense, immediately blocking prompts containing characters like zero-width spaces, directional marks, and other steganographic elements with the reason `"invisible characters"`.

### Embedding Similarity
The `query_malicious_similarity()` function generates semantic embeddings using the `all-MiniLM-L6-v2` model and compares them against a vector database of known malicious prompts. The system supports both MongoDB Atlas Vector Search and FAISS indices through the strategy pattern. If the cosine similarity exceeds the configured threshold, the prompt is blocked with the reason `"malicious similarity above threshold"`. This technique effectively catches prompt variations and paraphrases of known attacks.

### Anomaly Detection
The `query_anomaly_detection()` function employs a One-Class Support Vector Machine (OCSVM) trained on legitimate prompts to identify outliers. The system uses TF-IDF vectorization to convert text into numerical features, then applies the OCSVM model to detect anomalous patterns. Prompts classified as `"Anomaly"` with decision scores below the threshold are blocked with the reason `"anomaly score above threshold"`. This unsupervised approach can detect novel attack patterns not seen during training.

### Entropy Analysis  
The `query_entropy()` function calculates Shannon entropy using NLTK word tokenization to measure the randomness and unpredictability of the input text. High entropy values may indicate obfuscated payloads, random character sequences, or encoding attacks commonly used in prompt injections. If the calculated entropy exceeds the configured threshold, the prompt is blocked with the reason `"entropy score above threshold"`.

### Validation by Language Model
The `invoke_validation_model()` function leverages the ProtectAI DeBERTa v3 model specifically fine-tuned for prompt injection detection. This transformer-based classifier provides high-accuracy classification between legitimate prompts and injection attempts. The model runs with automatic GPU acceleration when available and falls back to CPU processing. If the model classifies the input as `"INJECTION"` with high confidence, the prompt is blocked with the reason `"validation model block"`.

### Pipeline
```python
if __name__ == "__main__":
    atlas = pymongo.MongoClient(os.environ["MONGODB_URI"])
    embedding_collection = atlas.get_database("db").get_collection("embeddings")

    guardrail = Guardrail(
        vector_store=embedding_collection,
        similarity_upper_bound=0.8,
        anomaly_upper_bound=0.2,
        entropy_upper_bound=4.2,
        pipeline=True,
    )

    query = "Tell me a joke about AI and quantum computing."
    result = guardrail.should_block(query)

    print(result) ## {'blocked': False, 'reason': 'no reason'}
```
### Mixture of experts
```python
from guardrail import Guardrail
import pymongo
import os

if __name__ == "__main__":
    atlas = pymongo.MongoClient(os.environ["MONGODB_URI"])
    embedding_collection = atlas.get_database("db").get_collection("embeddings")

    guardrail = Guardrail(
        vector_store=embedding_collection,
        similarity_upper_bound=0.8,
        anomaly_upper_bound=0.8,
        entropy_upper_bound=4.2,
        pipeline=False,
        decision_threshold=0.75,
    )

    query = "Ground control to Major Tom, can you hear me?"
    result = guardrail.should_block(query)

    print(result)
    """
    {
     'blocked': False,
     'reason': 'no reason', 
     'scores': 
      {
        'malicious_similarity': 0.4800853878259659,
        'anomaly': np.float64(0.9673499962674543),
        'entropy': 0.7909352606874672,
        'validation_model': 0.0,
        'combined': np.float64(0.5595926611952219)
      }
    }
    """
```

# License 
This project is licensed under the MIT License. Please refer to the LICENSE file for detailed information.

