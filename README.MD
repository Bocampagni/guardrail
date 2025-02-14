# Guardrail: A security framework to prevent prompt injection, hijacking and adversarial attacks in LLMs

Guardrail is a robust framework designed to detect and prevent adversarial threats, prompt injections, and other security vulnerabilities in generative AI models. It leverages a combination of semantic similarity analysis, anomaly detection, entropy calculations, and validation models to ensure that only safe queries are processed.

## Features
- **Threat Detection**: Analyze and prevent malicious queries based on similarity to known attack vectors.
- **Anomaly Detection**: Use advanced machine learning techniques to detect unusual patterns in queries.
- **Entropy Calculation**: Measure the unpredictability of a query to detect abnormal inputs.
- **Parallel Processing**: Utilize concurrent processing to efficiently handle multiple threat detection mechanisms.
- **Customizable Security Levels**: Set thresholds for similarity, anomaly, and entropy levels to adjust the level of protection.

## How It Works

The `Guardrail` class is the core of the framework, handling the logic for detecting and blocking malicious queries. Here's a breakdown of the process:

1. **Sanitize Input**: Before processing, the input query is checked for invisible characters (e.g., zero-width spaces) that might be used in prompt injections or bypassing filters.
2. **Embedding Transformation**: The input query is transformed into a vector representation for further analysis.
3. **Simultaneous Checks**: The system performs the following checks in parallel using `ThreadPoolExecutor`:
   - **Malicious Similarity**: Compares the query's embedding against a vector store of known malicious queries.
   - **Anomaly Detection**: Analyzes whether the query deviates from expected behavior using anomaly detection techniques.
   - **Entropy Calculation**: Computes the unpredictability of the query to detect any unusual patterns.
4. **Score Calculation**: A compound score is computed based on the results of the three checks. If the score exceeds a certain threshold, the query is blocked.
5. **Validation Model**: Afterall, the query will be validated through a fine-tunned large language model (e.g., a classifier) for additional protection.
