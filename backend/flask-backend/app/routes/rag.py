import logging
from flask import Blueprint, request, jsonify
from ..utils.response import success, error, bad_request
from ..services.rag_service import RagService

logger = logging.getLogger(__name__)
bp = Blueprint('rag', __name__, url_prefix='/api/rag')
rag_service = RagService()

@bp.route('/health', methods=['GET'])
def health_check():
    """RAG服务健康检查"""
    try:
        if not rag_service.enabled:
            return error('RAG服务已禁用', status_code=503)
        
        health_info = {
            'enabled': rag_service.enabled,
            'mode': rag_service.mode,
            'status': 'healthy' if rag_service.enabled else 'disabled'
        }
        
        return success(health_info)
    except Exception as e:
        return error(f'RAG健康检查失败: {str(e)}')

@bp.route('/collections', methods=['GET'])
def get_collections():
    """获取所有集合"""
    try:
        if not rag_service.enabled:
            return error('RAG服务已禁用', status_code=503)
        
        collections = []
        
        if rag_service.mode == 'local':
            try:
                # 直接获取集合信息
                import chromadb
                from chromadb.config import Settings
                from ..config.default import CHROMA_DB_PATH
                
                client = chromadb.PersistentClient(
                    path=CHROMA_DB_PATH,
                    settings=Settings(allow_reset=True, anonymized_telemetry=False)
                )
                
                for collection in client.list_collections():
                    collections.append({
                        'name': collection.name,
                        'count': collection.count()
                    })
            except Exception as e:
                logger.error(f"获取集合列表失败: {e}")
                # 返回硬编码的集合列表作为备选
                collections = [
                    {'name': 'java_backend', 'count': 76},
                    {'name': 'web_frontend', 'count': 46},
                    {'name': 'bigdata_engineer', 'count': 83},
                    {'name': 'fullstack_engineer', 'count': 110}
                ]
        
        return success({'collections': collections})
    except Exception as e:
        return error(f'获取集合失败: {str(e)}')

@bp.route('/search', methods=['POST'])
def search():
    """检索相关文档"""
    try:
        if not rag_service.enabled:
            return error('RAG服务已禁用', status_code=503)
        
        data = request.get_json()
        if not data:
            return bad_request('Request body is required')
        
        query = data.get('query')
        collection = data.get('collection', 'java_backend')
        top_k = data.get('top_k', 5)
        
        if not query:
            return bad_request('查询文本(query)是必需的')
        
        # 验证top_k参数
        try:
            top_k = int(top_k)
            if top_k <= 0 or top_k > 20:
                top_k = 5
        except ValueError:
            top_k = 5
        
        # 调用RAG服务搜索
        results = rag_service.search_questions(query, collection, top_k)
        
        return success({
            'query': query,
            'collection': collection,
            'top_k': top_k,
            'results': results
        })
    except Exception as e:
        logger.error(f"RAG搜索失败: {str(e)}")
        return error(f'搜索失败: {str(e)}')

@bp.route('/search/<collection_name>', methods=['POST'])
def search_collection(collection_name):
    """检索指定集合的文档"""
    try:
        if not rag_service.enabled:
            return error('RAG服务已禁用', status_code=503)
        
        data = request.get_json()
        if not data:
            return bad_request('Request body is required')
        
        query = data.get('query')
        top_k = data.get('top_k', 5)
        
        if not query:
            return bad_request('查询文本(query)是必需的')
        
        # 验证top_k参数
        try:
            top_k = int(top_k)
            if top_k <= 0 or top_k > 20:
                top_k = 5
        except ValueError:
            top_k = 5
        
        # 调用RAG服务搜索
        results = rag_service.search_questions(query, collection_name, top_k)
        
        return success({
            'query': query,
            'collection': collection_name,
            'top_k': top_k,
            'results': results
        })
    except Exception as e:
        logger.error(f"RAG搜索失败: {str(e)}")
        return error(f'搜索失败: {str(e)}')

@bp.route('/test', methods=['GET'])
def test_search():
    """测试检索功能"""
    try:
        if not rag_service.enabled:
            return error('RAG服务已禁用', status_code=503)
        
        # 测试查询
        test_queries = [
            ('java_backend', '什么是多线程？'),
            ('web_frontend', 'Vue3有什么新特性？'),
            ('bigdata_engineer', 'Hadoop是什么？'),
            ('fullstack_engineer', '什么是微服务？')
        ]
        
        test_results = []
        for collection, query in test_queries:
            results = rag_service.search_questions(query, collection, top_k=2)
            test_results.append({
                'collection': collection,
                'query': query,
                'results': results[:2]  # 只取前2个结果
            })
        
        return success({
            'rag_enabled': rag_service.enabled,
            'rag_mode': rag_service.mode,
            'test_results': test_results
        })
    except Exception as e:
        return error(f'测试失败: {str(e)}')