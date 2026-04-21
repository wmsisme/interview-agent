import sys
import os
sys.path.append('.')
from app.services.rag_service import RagService
from app.config.default import RAG_ENABLED, RAG_MODE, CHROMA_DB_PATH, EMBEDDING_MODEL_PATH
print('RAG_ENABLED:', RAG_ENABLED)
print('RAG_MODE:', RAG_MODE)
print('CHROMA_DB_PATH:', CHROMA_DB_PATH)
print('EMBEDDING_MODEL_PATH:', EMBEDDING_MODEL_PATH)
rag = RagService()
print('rag.enabled:', rag.enabled)
print('rag.mode:', rag.mode)
if rag.enabled:
    print('Testing search...')
    results = rag.search_questions('什么是Java', 'java_backend', top_k=2)
    print('Results count:', len(results))
    for r in results:
        print(f"  - {r.get('id')}: score={r.get('score')}")
else:
    print('RAG service disabled.')
    # 检查初始化错误
    # 可能是导入错误
    try:
        import chromadb
        print('chromadb imported')
    except ImportError as e:
        print('chromadb import error:', e)
    try:
        from sentence_transformers import SentenceTransformer
        print('sentence_transformers imported')
    except ImportError as e:
        print('sentence_transformers import error:', e)