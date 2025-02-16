from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch


def classify_text(query: str):
    tokenizer = AutoTokenizer.from_pretrained(
        "ProtectAI/deberta-v3-base-prompt-injection-v2"
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        "ProtectAI/deberta-v3-base-prompt-injection-v2"
    )

    classifier = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        truncation=True,
        max_length=512,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    )
    
    return classifier(query)
