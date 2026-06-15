# knowledge_base/vector_store.py
"""
向量存储引擎 - 从 JSON 文件读取知识库
"""

import os
import pickle
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


class VectorStore:
    """向量存储引擎"""

    def __init__(self, index_path: str = "knowledge_base/index/vector_index.pkl"):
        self.index_path = index_path
        self.documents = []
        self.document_vectors = []
        self.document_metadata = []
        self.vocabulary = {}
        self.initialized = False

        # 确保目录存在
        os.makedirs(os.path.dirname(index_path), exist_ok=True)

        self._load_or_init()

    def _load_or_init(self):
        """加载已有索引或初始化"""
        if os.path.exists(self.index_path):
            try:
                print("📂 正在加载已有向量索引...")
                with open(self.index_path, 'rb') as f:
                    data = pickle.load(f)
                    self.documents = data.get('documents', [])
                    self.document_vectors = data.get('vectors', [])
                    self.document_metadata = data.get('metadata', [])
                    self.vocabulary = data.get('vocabulary', {})
                    self.initialized = True
                print(f"✅ 加载向量索引: {len(self.documents)} 个片段")
            except Exception as e:
                print(f"⚠️ 加载索引失败: {e}")
                print("🔨 将重新构建知识库...")
                self._build_knowledge_base()
        else:
            print("📂 未找到向量索引，正在构建...")
            self._build_knowledge_base()

    def _simple_segment(self, text: str) -> List[str]:
        """简单的中文分词"""
        common_terms = [
            "民间借贷", "借款", "欠款", "利息", "诉讼时效", "借条", "转账", "还款",
            "劳动合同", "工资", "加班费", "辞退", "经济补偿", "双倍工资", "工伤", "社保",
            "离婚", "抚养权", "财产分割", "彩礼", "家暴", "婚姻", "夫妻共同财产",
            "交通事故", "交强险", "赔偿", "伤残", "误工费", "医疗费", "责任认定",
            "盗窃", "诈骗", "故意伤害", "拘留", "逮捕", "取保候审", "自首", "量刑",
            "房产纠纷", "买卖合同", "租赁合同", "物业纠纷", "过户", "产权",
            "起诉", "诉讼", "法院", "开庭", "判决", "执行", "证据", "仲裁",
            "公司", "股东", "股权", "法定代表人", "注册资本", "破产",
            "专利", "商标", "著作权", "版权", "知识产权", "侵权",
            "消费者", "维权", "退货", "假一赔三", "欺诈", "产品质量"
        ]

        words = []
        i = 0
        text_lower = text.lower()

        while i < len(text):
            matched = False
            for term in sorted(common_terms, key=len, reverse=True):
                if term in text_lower[i:i + len(term)]:
                    words.append(term)
                    i += len(term)
                    matched = True
                    break
            if not matched:
                words.append(text[i])
                i += 1

        return words

    def _build_vocabulary(self, documents: List[str]):
        """构建词汇表"""
        word_set = set()
        for doc in documents:
            words = self._simple_segment(doc)
            word_set.update(words)

        self.vocabulary = {word: idx for idx, word in enumerate(sorted(word_set))}

    def _text_to_vector(self, text: str) -> np.ndarray:
        """文本转向量"""
        if not self.vocabulary:
            return np.zeros(1)

        words = self._simple_segment(text)
        vector = np.zeros(len(self.vocabulary))

        word_count = defaultdict(int)
        for word in words:
            if word in self.vocabulary:
                word_count[word] += 1

        for word, count in word_count.items():
            idx = self.vocabulary[word]
            idf = np.log(len(self.documents) / (1 + sum(1 for d in self.documents if word in d)))
            vector[idx] = count * idf

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector

    def _chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """将长文本分块"""
        if not text:
            return []
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                for sep in ['。', '！', '？', '\n', '；', '，']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start + chunk_size // 2:
                        end = last_sep + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap if end < len(text) else end

        return chunks

    def _build_knowledge_base(self):
        """从 JSON 文件构建向量知识库"""
        import time
        start_time = time.time()

        print("=" * 60)
        print("🔨 正在构建向量知识库...")
        print(f"⏳ 开始时间: {time.strftime('%H:%M:%S')}")
        print("⏳ 这个过程可能需要 2-5 分钟，请耐心等待...")
        print("=" * 60)

        # 从 JSON 文件读取知识库数据
        json_path = "knowledge_base/data/legal_knowledge.json"

        if not os.path.exists(json_path):
            print(f"❌ 错误: 找不到知识库文件 {json_path}")
            print("   请确保 knowledge_base/data/legal_knowledge.json 存在")
            return

        print(f"📚 正在读取知识库文件: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            legal_knowledge = json.load(f)

        print(f"📚 加载知识库文件: {len(legal_knowledge)} 个分类")

        # 统计总案例数
        total_cases = sum(len(data.get("cases", [])) for data in legal_knowledge.values())
        print(f"📄 总案例数: {total_cases}")

        # 构建文档片段
        self.documents = []
        self.document_metadata = []

        print("\n📄 正在处理文档片段...")

        # 计算总数
        total_chunks = 0
        for category, data in legal_knowledge.items():
            content = data.get("content", "")
            content_chunks = self._chunk_text(content)
            total_chunks += len(content_chunks) + len(data.get("cases", []))

        print(f"   预计处理 {total_chunks} 个文档片段")

        processed = 0

        for category, data in legal_knowledge.items():
            # 添加主体内容的分块
            content = data.get("content", "")
            title = data.get("title", category)
            content_chunks = self._chunk_text(content)

            for idx, chunk in enumerate(content_chunks):
                if chunk and len(chunk) > 10:
                    self.documents.append(chunk)
                    self.document_metadata.append({
                        "category": category,
                        "type": "knowledge",
                        "title": title,
                        "chunk_id": idx
                    })
                    processed += 1
                    if processed % 50 == 0:
                        print(f"  处理进度: {processed}/{total_chunks}")

            # 添加案例
            for case in data.get("cases", []):
                case_title = case.get("title", "")
                case_summary = case.get("summary", "")
                if case_title and case_summary:
                    case_text = f"【案例】{case_title}: {case_summary}"
                    self.documents.append(case_text)
                    self.document_metadata.append({
                        "category": category,
                        "type": "case",
                        "title": case_title
                    })
                    processed += 1
                    if processed % 50 == 0:
                        print(f"  处理进度: {processed}/{total_chunks}")

        print(f"  ✅ 文档片段完成: {len(self.documents)} 个")

        if len(self.documents) == 0:
            print("❌ 错误: 没有生成任何文档片段")
            return

        # 构建词汇表
        print("\n📖 正在构建词汇表...")
        self._build_vocabulary(self.documents)
        print(f"  ✅ 词汇表大小: {len(self.vocabulary)}")

        # 构建向量
        print("\n🔢 正在计算向量...")
        self.document_vectors = []
        for i, doc in enumerate(self.documents):
            vec = self._text_to_vector(doc)
            self.document_vectors.append(vec)
            if (i + 1) % 100 == 0:
                print(f"  向量计算进度: {i + 1}/{len(self.documents)}")

        # 保存索引
        print("\n💾 正在保存索引...")
        self._save()

        end_time = time.time()
        self.initialized = True

        print("\n" + "=" * 60)
        print("✅ 向量知识库构建完成!")
        print(f"   文档片段: {len(self.documents)}")
        print(f"   词汇表大小: {len(self.vocabulary)}")
        print(f"   知识分类: {len(legal_knowledge)} 个")
        print(f"   总案例数: {total_cases}")
        print(f"⏱️ 总耗时: {end_time - start_time:.1f} 秒")
        print("=" * 60)

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索最相关的知识库内容"""
        if not self.initialized or not self.documents:
            return []

        query_vector = self._text_to_vector(query)

        if len(query_vector) == 0 or np.linalg.norm(query_vector) == 0:
            return []

        similarities = []
        for vec in self.document_vectors:
            if len(vec) == len(query_vector):
                sim = np.dot(query_vector, vec)
            else:
                sim = 0
            similarities.append(sim)

        if len(similarities) <= top_k:
            indices = list(range(len(similarities)))
        else:
            indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in indices:
            if similarities[idx] > 0.05:
                results.append({
                    "content": self.documents[idx],
                    "score": float(similarities[idx]),
                    "metadata": self.document_metadata[idx]
                })

        return results

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_documents": len(self.documents),
            "vocabulary_size": len(self.vocabulary),
            "index_path": self.index_path,
            "initialized": self.initialized
        }

    def add_document(self, content: str, metadata: Dict) -> int:
        """添加文档片段"""
        self.documents.append(content)
        self.document_metadata.append(metadata)

        self._build_vocabulary(self.documents)
        vector = self._text_to_vector(content)
        self.document_vectors.append(vector)

        self._save()
        return len(self.documents) - 1

    def delete_by_metadata(self, key: str, value: str) -> int:
        """根据元数据删除文档"""
        to_delete = []
        for i, meta in enumerate(self.document_metadata):
            if meta.get(key) == value:
                to_delete.append(i)

        for idx in sorted(to_delete, reverse=True):
            del self.documents[idx]
            del self.document_vectors[idx]
            del self.document_metadata[idx]

        if self.documents:
            self._build_vocabulary(self.documents)
            new_vectors = []
            for doc in self.documents:
                new_vectors.append(self._text_to_vector(doc))
            self.document_vectors = new_vectors

        self._save()
        return len(to_delete)

    def _save(self):
        """保存索引"""
        with open(self.index_path, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'vectors': self.document_vectors,
                'metadata': self.document_metadata,
                'vocabulary': self.vocabulary
            }, f)

    def clear(self):
        """清空所有数据"""
        self.documents = []
        self.document_vectors = []
        self.document_metadata = []
        self.vocabulary = {}
        self._save()