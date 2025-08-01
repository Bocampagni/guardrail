# Guardrail: Uma Solução Modular e Escalável de Segurança para GenAI

Guardrail é uma solução simples, rápida, modular e escalável de segurança para aplicações GenAI. O objetivo do artefato é bloquear prompts maliciosos utilizando uma combinação de técnicas como sanitização, similaridade semântica, detecção de anomalias, análise de entropia e validação com modelo de linguagem.

O artigo descreve os modos de operação da ferramenta — `pipeline` e `Mixture of Experts` — e apresenta os resultados de experimentos que demonstram sua eficácia em ambientes reais de execução de modelos GenAI.

# Estrutura do readme.md

- Título do projeto e objetivo
- Estrutura do repositório e resumo do README
- Selos considerados
- Informações básicas do ambiente
- Dependências globais e benchmarks
- Preocupações com segurança
- Instalação
- Teste mínimo
- Experimentos com reivindicações
- LICENSE

# Selos Considerados

SeloD + SeloF + SeloS + SeloR

# Informações básicas

- **Sistema operacional suportado**: Linux

- **Requisitos de hardware**:

  - CPU moderna
  - (Opcional) GPU com suporte CUDA
  - Mínimo de 4 GB de RAM
  - Espaço em disco: aproximadamente 500 MB

- **Requisitos de software**:

  - Python 3.12+
  - `uv` (gerenciador de ambientes)
  - MongoDB Atlas ou FAISS para embeddings
  - (Opcional) CUDA/cuDNN para execução acelerada

# Dependências

- `sentence-transformers==2.2.2` — embeddings
- `faiss-cpu==1.7.4` ou MongoDB Vector Search
- `scikit-learn` — OneClassSVM
- `nltk` — entropia
- `transformers`, `torch` — modelo DeBERTa da ProtectAI
- `uv` — ambiente reprodutível

# Preocupações com segurança

- A entrada é apenas texto, sem execução externa.
- Evite usar dados sensíveis diretamente.
- GPUs compartilhadas devem ser monitoradas quanto a vazamento de memória.

# Instalação

```bash
git clone git@github.com:Bocampagni/guardrail.git
cd guardrail
uv sync
```

# Teste mínimo

```bash
uv run example.py
```

Saída esperada:

```json
{
  'blocked': False, 
  'reason': 'no reason'
}
```

# Experimentos

Os exemplos a seguir ilustram as principais funcionalidades do Guardrail.

## Reivindicação #1: Pipeline básica (example.py)

Executa os módulos em sequência e bloqueia na primeira violação.

```python
from guardrail import Guardrail

...
guardrail = Guardrail(
    vector_store=embedding_collection,
    similarity_upper_bound=0.8,
    anomaly_upper_bound=0.2,
    entropy_upper_bound=4.2,
    pipeline=True,
)

result = guardrail.should_block("Tell me a joke about AI.")
print(result)
```

## Reivindicação #2: Mixture of Experts (benchmark.py)

Todos os módulos são executados independentemente. A decisão final é ponderada.

```python
guardrail = Guardrail(
    vector_store=embedding_collection,
    similarity_upper_bound=0.8,
    anomaly_upper_bound=0.8,
    entropy_upper_bound=4.2,
    pipeline=False,
    decision_threshold=0.75,
)

result = guardrail.should_block("Ground control to Major Tom")
print(result)
```

Resultado esperado: um dicionário com `blocked`, `reason` e `scores` de cada módulo.

# LICENSE

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo `LICENSE` no repositório para mais detalhes.

