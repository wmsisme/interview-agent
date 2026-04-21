import logging
import os
import requests
from typing import List, Dict, Any
from ..config.default import RAG_SERVICE_URL, RAG_ENABLED, RAG_MODE, CHROMA_DB_PATH, EMBEDDING_MODEL_PATH, RAG_TOP_K

logger = logging.getLogger(__name__)

class RagService:
    def __init__(self):
        self.enabled = RAG_ENABLED
        self.mode = RAG_MODE
        self.top_k = RAG_TOP_K
        
        if not self.enabled:
            logger.info("RAG服务已禁用")
            return
            
        if self.mode == "http":
            self.service_url = RAG_SERVICE_URL
            logger.info(f"RAG服务模式: HTTP, URL: {self.service_url}")
        elif self.mode == "local":
            try:
                import chromadb
                from chromadb.config import Settings
                from sentence_transformers import SentenceTransformer
                
                self.chroma_client = chromadb.PersistentClient(
                    path=os.path.abspath(CHROMA_DB_PATH),
                    settings=Settings(allow_reset=True, anonymized_telemetry=False)
                )
                
                logger.info(f"本地RAG服务初始化成功, ChromaDB路径: {CHROMA_DB_PATH}")
                
                try:
                    self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_PATH)
                    logger.info(f"嵌入模型加载成功: {EMBEDDING_MODEL_PATH}")
                except Exception as e:
                    logger.warning(f"无法加载本地嵌入模型 {EMBEDDING_MODEL_PATH}: {e}, 将使用ChromaDB内置嵌入")
                    self.embedding_model = None
                    
            except ImportError as e:
                logger.error(f"本地RAG服务依赖缺失: {e}, 请安装 chromadb 和 sentence-transformers")
                self.enabled = False
            except Exception as e:
                logger.error(f"本地RAG服务初始化失败: {e}")
                self.enabled = False
        else:
            logger.error(f"未知的RAG模式: {self.mode}, 禁用RAG服务")
            self.enabled = False
    
    def search_questions(self, query: str, collection: str = "backend", top_k: int = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            logger.warning("RAG服务已禁用")
            return []
        
        if top_k is None:
            top_k = self.top_k
            
        if self.mode == "http":
            return self._search_http(query, collection, top_k)
        elif self.mode == "local":
            return self._search_local(query, collection, top_k)
        else:
            return []
    
    def _search_http(self, query: str, collection: str, top_k: int) -> List[Dict[str, Any]]:
        try:
            url = f"{self.service_url}/search"
            
            request_body = {
                "query": query,
                "collection": collection,
                "top_k": top_k
            }
            
            response = requests.post(url, json=request_body, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get("results", [])
            
        except Exception as e:
            logger.error(f"HTTP RAG搜索失败: {str(e)}")
            return []
    
    def _search_local(self, query: str, collection: str, top_k: int) -> List[Dict[str, Any]]:
        try:
            if not hasattr(self, 'chroma_client'):
                logger.error("ChromaDB客户端未初始化")
                return []
            
            collection_obj = self.chroma_client.get_collection(name=collection)
            
            if self.embedding_model:
                query_embedding = self.embedding_model.encode(query).tolist()
                results = collection_obj.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["metadatas", "documents", "distances"]
                )
            else:
                results = collection_obj.query(
                    query_texts=[query],
                    n_results=top_k,
                    include=["metadatas", "documents", "distances"]
                )
            
            formatted_results = []
            if results and results.get("ids"):
                for i in range(len(results["ids"][0])):
                    doc_id = results["ids"][0][i]
                    document = results["documents"][0][i]
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0.0
                    
                    formatted_results.append({
                        "id": doc_id,
                        "content": document,
                        "metadata": metadata,
                        "score": 1.0 - distance if distance <= 1.0 else 1.0 / (1.0 + distance),
                        "distance": distance
                    })
            
            logger.info(f"本地RAG搜索完成, 查询: '{query}', 集合: {collection}, 结果数: {len(formatted_results)}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"本地RAG搜索失败: {str(e)}")
            return []
    
    def search_with_filter(self, query: str, collection: str, top_k: int = None, filters: Dict = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            logger.warning("RAG服务已禁用")
            return []
        
        if top_k is None:
            top_k = self.top_k
            
        if self.mode == "http":
            return self._search_with_filter_http(query, collection, top_k, filters)
        elif self.mode == "local":
            return self._search_with_filter_local(query, collection, top_k, filters)
        else:
            return []
    
    def _search_with_filter_http(self, query: str, collection: str, top_k: int, filters: Dict) -> List[Dict[str, Any]]:
        try:
            url = f"{self.service_url}/search"
            
            request_body = {
                "query": query,
                "collection": collection,
                "top_k": top_k
            }
            
            if filters:
                request_body["filters"] = filters
            
            response = requests.post(url, json=request_body, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get("results", [])
            
        except Exception as e:
            logger.error(f"HTTP RAG过滤搜索失败: {str(e)}")
            return []
    
    def _search_with_filter_local(self, query: str, collection: str, top_k: int, filters: Dict) -> List[Dict[str, Any]]:
        try:
            if not hasattr(self, 'chroma_client'):
                logger.error("ChromaDB客户端未初始化")
                return []
            
            collection_obj = self.chroma_client.get_collection(name=collection)
            
            where_filter = None
            if filters:
                where_filter = {}
                for key, value in filters.items():
                    if isinstance(value, dict):
                        where_filter[key] = value
                    else:
                        where_filter[key] = {"$eq": value}
            
            if self.embedding_model:
                query_embedding = self.embedding_model.encode(query).tolist()
                results = collection_obj.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter,
                    include=["metadatas", "documents", "distances"]
                )
            else:
                results = collection_obj.query(
                    query_texts=[query],
                    n_results=top_k,
                    where=where_filter,
                    include=["metadatas", "documents", "distances"]
                )
            
            formatted_results = []
            if results and results.get("ids"):
                for i in range(len(results["ids"][0])):
                    doc_id = results["ids"][0][i]
                    document = results["documents"][0][i]
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0.0
                    
                    formatted_results.append({
                        "id": doc_id,
                        "content": document,
                        "metadata": metadata,
                        "score": 1.0 - distance if distance <= 1.0 else 1.0 / (1.0 + distance),
                        "distance": distance
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"本地RAG过滤搜索失败: {str(e)}")
            return []
    
    def search_both(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        if not self.enabled:
            logger.warning("RAG服务已禁用")
            return []
        
        if top_k is None:
            top_k = self.top_k
            
        backend_results = self.search_questions(query, "backend", top_k)
        frontend_results = self.search_questions(query, "frontend", top_k)
        
        all_results = backend_results + frontend_results
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return all_results[:top_k]
    
    def get_collections(self) -> List[Dict[str, Any]]:
        if not self.enabled:
            return []
        
        if self.mode == "http":
            return self._get_collections_http()
        elif self.mode == "local":
            return self._get_collections_local()
        else:
            return []
    
    def _get_collections_http(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.service_url}/collections"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get("collections", [])
            
        except Exception as e:
            logger.error(f"获取HTTP RAG集合失败: {str(e)}")
            return []
    
    def _get_collections_local(self) -> List[Dict[str, Any]]:
        try:
            if not hasattr(self, 'chroma_client'):
                logger.error("ChromaDB客户端未初始化")
                return []
            
            collections = self.chroma_client.list_collections()
            result = []
            
            for collection in collections:
                collection_info = {
                    "name": collection.name,
                    "metadata": collection.metadata or {},
                    "count": collection.count() if hasattr(collection, 'count') else 0
                }
                result.append(collection_info)
            
            return result
            
        except Exception as e:
            logger.error(f"获取本地RAG集合失败: {str(e)}")
            return []
    
    def get_collection_summary(self, collection: str) -> str:
        """获取集合的摘要信息"""
        if not self.enabled:
            return ""
        try:
            if self.mode == "local":
                # 简单返回集合名称和文档数量
                if hasattr(self, 'chroma_client'):
                    col = self.chroma_client.get_collection(name=collection)
                    count = col.count() if hasattr(col, 'count') else 0
                    return f"集合 '{collection}' 包含 {count} 个文档"
            return ""
        except Exception as e:
            logger.warning(f"获取集合摘要失败: {str(e)}")
            return ""

    def health_check(self) -> bool:
        if not self.enabled:
            return False
            
        if self.mode == "http":
            return self._health_check_http()
        elif self.mode == "local":
            return self._health_check_local()
        else:
            return False
    
    def _health_check_http(self) -> bool:
        try:
            url = f"{self.service_url}/health"
            
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            result = response.json()
            return result.get("status") == "ok"
            
        except Exception as e:
            logger.error(f"HTTP RAG健康检查失败: {str(e)}")
            return False
    
    def _health_check_local(self) -> bool:
        try:
            if not hasattr(self, 'chroma_client'):
                return False
            
            collections = self.chroma_client.list_collections()
            return len(collections) > 0
            
        except Exception as e:
            logger.error(f"本地RAG健康检查失败: {str(e)}")
            return False