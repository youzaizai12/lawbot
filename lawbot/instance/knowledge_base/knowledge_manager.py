"""
知识库管理器 - 独立的知识库管理模块
支持增删改查知识条目
"""

import os
import json
from typing import List, Dict, Optional
from .vector_store import VectorStore


class KnowledgeManager:
    def __init__(self, data_path: str = "knowledge_base/data/legal_knowledge.json"):
        print("1. 开始初始化知识库管理器...")
        self.data_path = data_path
        self.vector_store = VectorStore()
        print("2. VectorStore 初始化完成")
        self.knowledge_data = {}

        os.makedirs(os.path.dirname(data_path), exist_ok=True)

        print("3. 加载数据文件...")
        self._load_data()
        print(f"✅ 加载知识库: {len(self.knowledge_data)} 个分类")

        # 直接构建索引，不要异步超时
        print("4. 开始构建索引...")
        self._build_index()
        print("5. 知识库管理器初始化完成")

    def _load_data(self):
        """加载知识库数据"""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.knowledge_data = json.load(f)
                print(f"✅ 加载知识库: {len(self.knowledge_data)} 个分类")
            except Exception as e:
                print(f"加载知识库失败: {e}")
                self.knowledge_data = {}
        else:
            self.knowledge_data = {}
            print("⚠️ 知识库文件不存在，创建新知识库")

    def _save_data(self):
        """保存知识库数据"""
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_data, f, ensure_ascii=False, indent=2)

    def _build_index(self):
        """构建索引 - 只执行一次"""
        # 检查是否已经有文档
        if len(self.vector_store.documents) > 0:
            print("索引已存在，跳过构建")
            return

        print("开始构建索引...")
        for category, data in self.knowledge_data.items():
            # 添加主要内容
            self.vector_store.add_document(
                content=data.get("content", ""),
                metadata={"category": category, "type": "knowledge"}
            )
            # 添加案例
            for case in data.get("cases", []):
                case_text = f"【案例】{case['title']}: {case['summary']}"
                self.vector_store.add_document(
                    content=case_text,
                    metadata={"category": category, "type": "case"}
                )
        print("索引构建完成")

    def add_category(self, category: str, title: str, content: str, keywords: List[str],
                     cases: List[Dict] = None) -> bool:
        """添加知识分类"""
        if category in self.knowledge_data:
            print(f"分类 '{category}' 已存在")
            return False

        self.knowledge_data[category] = {
            "title": title,
            "keywords": keywords,
            "content": content,
            "cases": cases or []
        }

        # 添加到向量索引
        self.vector_store.add_document(
            content=content,
            metadata={"category": category, "type": "knowledge", "title": title}
        )

        for case in cases or []:
            case_text = f"【案例】{case['title']}: {case['summary']}"
            self.vector_store.add_document(
                content=case_text,
                metadata={"category": category, "type": "case", "title": case['title']}
            )

        self._save_data()
        print(f"✅ 添加分类: {category}")
        return True

    def update_category(self, category: str, **kwargs) -> bool:
        """更新知识分类"""
        if category not in self.knowledge_data:
            print(f"分类 '{category}' 不存在")
            return False

        # 删除旧索引
        self.vector_store.delete_by_metadata("category", category)

        # 更新数据
        for key, value in kwargs.items():
            if key in self.knowledge_data[category]:
                self.knowledge_data[category][key] = value

        # 重新添加索引
        data = self.knowledge_data[category]
        self.vector_store.add_document(
            content=data.get("content", ""),
            metadata={"category": category, "type": "knowledge", "title": data.get("title", category)}
        )

        for case in data.get("cases", []):
            case_text = f"【案例】{case['title']}: {case['summary']}"
            self.vector_store.add_document(
                content=case_text,
                metadata={"category": category, "type": "case", "title": case['title']}
            )

        self._save_data()
        print(f"✅ 更新分类: {category}")
        return True

    def delete_category(self, category: str) -> bool:
        """删除知识分类"""
        if category not in self.knowledge_data:
            return False

        # 删除向量索引
        self.vector_store.delete_by_metadata("category", category)

        # 删除数据
        del self.knowledge_data[category]

        self._save_data()
        print(f"✅ 删除分类: {category}")
        return True

    def add_case(self, category: str, case_title: str, case_summary: str) -> bool:
        """添加案例到指定分类"""
        if category not in self.knowledge_data:
            print(f"分类 '{category}' 不存在")
            return False

        new_case = {"title": case_title, "summary": case_summary}
        self.knowledge_data[category]["cases"].append(new_case)

        # 添加到向量索引
        case_text = f"【案例】{case_title}: {case_summary}"
        self.vector_store.add_document(
            content=case_text,
            metadata={"category": category, "type": "case", "title": case_title}
        )

        self._save_data()
        print(f"✅ 添加案例: {case_title}")
        return True

    def delete_case(self, category: str, case_index: int) -> bool:
        """删除案例"""
        if category not in self.knowledge_data:
            return False

        cases = self.knowledge_data[category]["cases"]
        if case_index < 0 or case_index >= len(cases):
            return False

        removed = cases.pop(case_index)

        # 重建索引（简单处理：重新构建整个分类的索引）
        self._rebuild_category_index(category)

        self._save_data()
        print(f"✅ 删除案例: {removed['title']}")
        return True

    def _rebuild_category_index(self, category: str):
        """重建指定分类的索引"""
        # 删除旧索引
        self.vector_store.delete_by_metadata("category", category)

        # 重新添加
        data = self.knowledge_data[category]
        self.vector_store.add_document(
            content=data.get("content", ""),
            metadata={"category": category, "type": "knowledge", "title": data.get("title", category)}
        )

        for case in data.get("cases", []):
            case_text = f"【案例】{case['title']}: {case['summary']}"
            self.vector_store.add_document(
                content=case_text,
                metadata={"category": category, "type": "case", "title": case['title']}
            )

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索知识库"""
        return self.vector_store.search(query, top_k)

    def get_all_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self.knowledge_data.keys())

    def get_category(self, category: str) -> Optional[Dict]:
        """获取分类详情"""
        return self.knowledge_data.get(category)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        total_cases = sum(len(data.get("cases", [])) for data in self.knowledge_data.values())
        return {
            "total_categories": len(self.knowledge_data),
            "total_cases": total_cases,
            "vector_stats": self.vector_store.get_stats()
        }

    def export_json(self, output_path: str = None):
        """导出知识库为JSON"""
        if output_path is None:
            output_path = self.data_path.replace('.json', '_export.json')

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 导出知识库到: {output_path}")
        return output_path

    def import_json(self, import_path: str):
        """从JSON导入知识库"""
        with open(import_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)

        # 清空现有数据
        self.vector_store.clear()
        self.knowledge_data = new_data

        # 重新构建索引
        self._build_index()
        self._save_data()

        print(f"✅ 导入知识库: {len(new_data)} 个分类")


# 全局知识库实例
knowledge_manager = KnowledgeManager()