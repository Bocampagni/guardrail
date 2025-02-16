from app.guardrail import VectorStore
from app.atlas import AtlasVectorStore
from app.chain import ChainVectorStore

def config_vector_store(store: VectorStore):
    return AtlasVectorStore if store.type == "ATLAS" else ChainVectorStore
