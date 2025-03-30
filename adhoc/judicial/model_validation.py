import torch
import pandas as pd
from transformers import AutoTokenizer
from transformers import AutoModelForPreTraining
from transformers import AutoModel

model = AutoModelForPreTraining.from_pretrained('neuralmind/bert-base-portuguese-cased')
tokenizer = AutoTokenizer.from_pretrained('neuralmind/bert-base-portuguese-cased', do_lower_case=False)
dataset = pd.read_csv('../v2/output/translated_text.csv')

for i in range(5):
    text = dataset.iloc[i]['prompt']
    print(text)
    input_ids = tokenizer(text, max_length=512, truncation=True, padding="max_length", return_tensors="pt")['input_ids']
    with torch.no_grad():
        last_hidden_states = model(input_ids)
    print(last_hidden_states)
    print('\n')
    print('---------------------------------------------------')
    
    