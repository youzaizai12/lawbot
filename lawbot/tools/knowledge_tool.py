#!/usr/bin/env python
"""
知识库命令行管理工具
用法:
    python tools/knowledge_tool.py list                    # 列出所有分类
    python tools/knowledge_tool.py add                     # 添加分类（交互式）
    python tools/knowledge_tool.py delete <分类名>          # 删除分类
    python tools/knowledge_tool.py search <关键词>          # 搜索知识库
    python tools/knowledge_tool.py export                  # 导出知识库
    python tools/knowledge_tool.py stats                   # 查看统计
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_base.knowledge_manager import KnowledgeManager


def print_help():
    print("""
知识库管理工具 - 使用方法:
============================================================
  list                    列出所有知识分类
  add                     添加新分类（交互式）
  delete <分类名>          删除指定分类
  update <分类名>          更新分类（交互式）
  add-case <分类名>        添加案例到分类
  search <关键词>          搜索知识库
  export                  导出知识库为JSON
  import <文件路径>        从JSON导入知识库
  stats                   查看统计信息
  help                    显示帮助
============================================================
""")


def list_categories(km):
    """列出所有分类"""
    categories = km.get_all_categories()
    if not categories:
        print("暂无分类")
        return

    print("\n📚 知识库分类:")
    print("-" * 40)
    for i, cat in enumerate(categories, 1):
        data = km.get_category(cat)
        case_count = len(data.get("cases", []))
        print(f"  {i}. {cat} (案例: {case_count}个)")
    print("-" * 40)


def add_category_interactive(km):
    """交互式添加分类"""
    print("\n📝 添加新分类")
    print("-" * 40)

    category = input("分类名称 (如: 房产纠纷): ").strip()
    if not category:
        print("分类名称不能为空")
        return

    if category in km.get_all_categories():
        print(f"分类 '{category}' 已存在")
        return

    title = input("标题 (默认同分类名): ").strip() or category
    print("关键词 (用逗号分隔): ")
    keywords_input = input("> ").strip()
    keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else []

    print("知识内容 (输入完成后输入 END 结束):")
    content_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        content_lines.append(line)
    content = "\n".join(content_lines)

    if not content:
        print("内容不能为空")
        return

    print("添加案例? (y/n): ", end="")
    add_cases = input().strip().lower() == 'y'
    cases = []

    if add_cases:
        while True:
            print("\n--- 添加案例 ---")
            case_title = input("案例标题 (输入空结束): ").strip()
            if not case_title:
                break
            case_summary = input("案例摘要: ").strip()
            cases.append({"title": case_title, "summary": case_summary})

    km.add_category(category, title, content, keywords, cases)
    print(f"✅ 分类 '{category}' 添加成功!")


def delete_category(km, category):
    """删除分类"""
    if category not in km.get_all_categories():
        print(f"分类 '{category}' 不存在")
        return

    confirm = input(f"确认删除分类 '{category}'? (y/n): ").strip().lower()
    if confirm == 'y':
        km.delete_category(category)
        print(f"✅ 已删除分类 '{category}'")


def add_case_interactive(km, category):
    """交互式添加案例"""
    if category not in km.get_all_categories():
        print(f"分类 '{category}' 不存在")
        return

    print(f"\n📝 为 '{category}' 添加案例")
    case_title = input("案例标题: ").strip()
    if not case_title:
        print("标题不能为空")
        return

    case_summary = input("案例摘要: ").strip()
    if not case_summary:
        print("摘要不能为空")
        return

    km.add_case(category, case_title, case_summary)


def search_knowledge(km, query):
    """搜索知识库"""
    results = km.search(query, top_k=5)

    if not results:
        print(f"未找到与 '{query}' 相关的内容")
        return

    print(f"\n🔍 搜索: '{query}'")
    print("-" * 50)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. [相关度: {result['score']:.3f}]")
        print(f"   分类: {result['metadata'].get('category', '未知')}")
        print(f"   类型: {result['metadata'].get('type', '知识')}")
        print(f"   内容: {result['content'][:200]}...")
    print("-" * 50)


def show_stats(km):
    """显示统计信息"""
    stats = km.get_stats()
    print("\n📊 知识库统计")
    print("-" * 40)
    print(f"  分类数量: {stats['total_categories']}")
    print(f"  案例数量: {stats['total_cases']}")
    print(f"  向量片段: {stats['vector_stats']['total_documents']}")
    print(f"  词汇表大小: {stats['vector_stats']['vocabulary_size']}")
    print("-" * 40)


def main():
    km = KnowledgeManager()

    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == "help":
        print_help()
    elif command == "list":
        list_categories(km)
    elif command == "add":
        add_category_interactive(km)
    elif command == "delete" and len(sys.argv) >= 3:
        delete_category(km, sys.argv[2])
    elif command == "add-case" and len(sys.argv) >= 3:
        add_case_interactive(km, sys.argv[2])
    elif command == "search" and len(sys.argv) >= 3:
        search_knowledge(km, " ".join(sys.argv[2:]))
    elif command == "export":
        km.export_json()
    elif command == "import" and len(sys.argv) >= 3:
        km.import_json(sys.argv[2])
    elif command == "stats":
        show_stats(km)
    else:
        print(f"未知命令: {command}")
        print_help()


if __name__ == "__main__":
    main()