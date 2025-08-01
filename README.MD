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

#### **Sistema Operacional Suportado**
- Linux (qualquer distribuição moderna com suporte a Python 3.12+)

#### **Requisitos de Hardware**
- Processador compatível com instruções básicas de 64 bits
- **(Opcional)** GPU com suporte a CUDA (para aceleração por hardware)
- Mínimo de **4 GB de RAM**
- Aproximadamente **500 MB de espaço livre em disco**

#### **Requisitos de Software**
- **Python** `>= 3.12`
- [`uv`](https://github.com/astral-sh/uv) – Gerenciador de ambientes e dependências
- **Armazenamento vetorial**:
  - [MongoDB Atlas](https://www.mongodb.com/atlas) com índice de busca vetorial **ou**
  - [FAISS](https://github.com/facebookresearch/faiss) para buscas locais **(Escolha já configurada no ambiente)**
- **(Opcional)** [CUDA](https://developer.nvidia.com/cuda-zone) e [cuDNN](https://developer.nvidia.com/cudnn) instalados para suporte a execução acelerada por GPU


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

Caso não possua o `uv`, a instalação pode ser feita via:
```bash
pip install uv
```

> Para a execução do Guardrail, seus notebooks, exemplos e benchmarks é necessário que o `uv` esteja instalado.

# Teste mínimo

```bash
make example
```

Saída esperada:

```json
{
  'blocked': False, 
  'reason': 'no reason'
}
```

# Experimentos

Os exemplos a seguir ilustram as principais funcionalidades do Guardrail. Em ambas as configurações, a regra `make benchmark` é utilizada. Onde o primeiro argumento `mode` é o modo de execução, cujo domínio inclui `(sequential, parallel)` e o segundo argumento é um número inteiro, responsável por dizer a quantidades de entradas que serão utilizadas na validação, com a seleção sendo feita de forma aleatória.

## Reivindicação #1: Pipeline

Executa os módulos em sequência e bloqueia na primeira violação.

```bash
make benchmark mode=sequential queries=100
```

O resultado esperado é um dicionário com as chaves `blocked` e `reason`.

## Reivindicação #2: Mixture of Experts

Todos os módulos são executados independentemente. A decisão final é ponderada.

```bash
make benchmark mode=parallel queries=100
```

Resultado esperado: um dicionário com `blocked`, `reason` e `scores` de cada módulo.

# LICENSE

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo `LICENSE` no repositório para mais detalhes.

