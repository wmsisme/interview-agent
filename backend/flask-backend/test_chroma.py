import sys
import os
sys.path.append('.')
import chromadb
from chromadb.config import Settings
print('Testing ChromaDB connection...')
client = chromadb.PersistentClient(
    path='../../chroma_db',
    settings=Settings(allow_reset=True, anonymized_telemetry=False)
)
collections = client.list_collections()
print('Number of collections:', len(collections))
for c in collections:
    print(f'  - {c.name}: {c.count()} documents')
    # 尝试获取一些样本
    try:
        results = c.peek(limit=1)
        if results['ids']:
            print(f'    Sample id: {results["ids"][0][:50]}...')
    except Exception as e:
        print(f'    Error peeking: {e}')
print('Done.')