"""
综合导入所有法律数据
数据源：
1. train目录：大量JSON文件
2. test目录：测试集JSON文件
3. sample_result.json：问答数据集
"""

import os
import sys
import json
import glob
from collections import defaultdict

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from knowledge_base.knowledge_manager import KnowledgeManager

# ====================== 配置 ======================
# 三个数据源的路径
DATA_PATHS = {
    "train": r"D:\360Downloads\laws_qa_data\laws_data\9d3f0f41-c7df-4211-a32a-9e1fc74f8a68\train",
    "test": r"D:\360Downloads\laws_qa_data\laws_data\88b4cb28-8955-4122-9caf-7ea192a129bf\test",
    "sample": r"D:\360Downloads\laws_qa_data\laws_data\sample_result.json"
}

# 关键词到分类的映射
CATEGORY_MAPPING = {
    "民间借贷": ["借钱", "欠钱", "借条", "借款", "债务", "利息", "高利贷", "欠款", "还款", "借贷", "担保", "保证人",
                 "砍头息", "本金", "利率"],
    "劳动纠纷": ["工资", "辞退", "加班", "社保", "劳动合同", "工伤", "仲裁", "开除", "裁员", "拖欠工资", "经济补偿",
                 "双倍工资", "试用期", "五险一金", "劳动法", "辞退", "赔偿金"],
    "交通事故": ["车祸", "追尾", "撞人", "交强险", "赔偿", "伤残", "酒驾", "醉驾", "肇事", "交通", "事故", "责任认定",
                 "逃逸", "保险", "理赔"],
    "婚姻家庭": ["离婚", "抚养权", "财产分割", "彩礼", "家暴", "婚姻", "出轨", "抚养费", "结婚", "夫妻", "感情破裂",
                 "同居", "继承"],
    "刑事法律": ["盗窃", "诈骗", "拘留", "逮捕", "判刑", "取保候审", "自首", "故意伤害", "抢劫", "罪名", "刑事责任",
                 "刑期", "缓刑"],
    "房产纠纷": ["房产", "房子", "购房", "租房", "房东", "租客", "物业", "产权", "过户", "买卖合同", "小产权", "宅基地",
                 "拆迁", "安置"],
    "合同纠纷": ["合同", "违约", "解除合同", "定金", "违约金", "格式条款", "缔约过失", "买卖合同", "租赁合同"],
    "侵权责任": ["侵权", "伤害", "赔偿", "人身损害", "名誉权", "隐私权", "高空抛物", "动物致害", "产品责任",
                 "医疗损害"],
    "诉讼程序": ["起诉", "诉讼", "法院", "开庭", "判决", "执行", "诉讼时效", "证据", "管辖", "上诉", "仲裁"],
    "公司法律": ["公司", "股东", "股权", "法定代表人", "注册资本", "公司章程", "破产", "清算", "董事", "监事"],
    "知识产权": ["专利", "商标", "著作权", "版权", "知识产权", "侵权", "盗版"],
    "消费者权益": ["消费者", "维权", "退货", "假一赔三", "欺诈", "产品质量", "食品安全", "315"],
    "行政法律": ["行政处罚", "行政复议", "行政诉讼", "行政拘留", "行政许可", "政府"],
    "继承法律": ["继承", "遗嘱", "遗产", "法定继承", "遗赠", "公证"],
}

# 过滤关键词（低质量/广告内容）
FILTER_KEYWORDS = [
    "请采纳", "好评", "点击头像", "电话咨询", "来电咨询", "免费咨询",
    "微信", "手机号", "加微信", "面谈", "律所", "律师费", "代理费",
    "点赞", "评价", "金牌律师", "团队", "主任律师", "我的主页",
    "点击我的头像", "手机同号", "加我微信", "扫一扫"
]

MIN_ANSWER_LENGTH = 30
MAX_ANSWER_LENGTH = 1500

# 用于去重的问题缓存
seen_questions = set()


def classify_question(question: str, cause: str = "") -> str:
    """根据问题内容和cause字段分类"""
    if cause and cause in CATEGORY_MAPPING:
        return cause

    if not question:
        return "法律咨询"

    question_lower = question.lower()
    for category, keywords in CATEGORY_MAPPING.items():
        for kw in keywords:
            if kw in question_lower:
                return category
    return "法律咨询"


def clean_text(text: str) -> str:
    """清理文本"""
    if not text:
        return ""
    # 移除多余空白
    text = ' '.join(text.split())
    # 移除特殊字符
    import re
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：""''《》【】、·～—（）\s]', '', text)
    return text.strip()


def is_valid_answer(answer: str) -> bool:
    """判断答案是否有效"""
    if not answer:
        return False
    if len(answer) < MIN_ANSWER_LENGTH:
        return False

    # 检查是否包含广告词
    for kw in FILTER_KEYWORDS:
        if kw in answer:
            return False

    # 检查是否是纯推荐律师的内容
    lawyer_patterns = ["我是X律师", "本律师", "我的团队", "律所", "委托律师"]
    lawyer_count = sum(1 for p in lawyer_patterns if p in answer)
    if lawyer_count >= 2 and len(answer) < 150:
        return False

    return True


def is_duplicate(question: str) -> bool:
    """检查是否重复"""
    key = question[:50]  # 用前50字作为去重key
    if key in seen_questions:
        return True
    seen_questions.add(key)
    return False


def load_json_files_from_dir(directory: str, source_name: str) -> list:
    """从目录加载所有JSON文件"""
    if not os.path.exists(directory):
        print(f"  ⚠️ 目录不存在: {directory}")
        return []

    files = glob.glob(os.path.join(directory, "*.json"))
    print(f"  📁 找到 {len(files)} 个文件")

    data_list = []
    error_count = 0

    for i, filepath in enumerate(files):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_source'] = source_name
                data['_source_file'] = os.path.basename(filepath)
                data_list.append(data)
        except Exception as e:
            error_count += 1

        if (i + 1) % 500 == 0:
            print(f"    已加载 {i + 1}/{len(files)} 个文件...")

    if error_count > 0:
        print(f"    ⚠️ {error_count} 个文件读取失败")

    return data_list


def load_sample_result(filepath: str) -> list:
    """加载 sample_result.json"""
    if not os.path.exists(filepath):
        print(f"  ⚠️ 文件不存在: {filepath}")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"  📁 找到 {len(data)} 条问答数据")

    # 转换为统一格式
    converted = []
    for item in data:
        converted.append({
            "question": "",  # sample_result没有question字段
            "answer": item.get("answer", ""),
            "id": item.get("id", ""),
            "_source": "sample_result",
            "_source_file": "sample_result.json"
        })

    return converted


def load_all_data() -> list:
    """加载所有数据源"""
    all_data = []

    print("\n📚 加载数据源:")
    print("-" * 50)

    # 1. 加载train目录
    print("\n[1/3] 加载 train 目录...")
    train_data = load_json_files_from_dir(DATA_PATHS["train"], "train")
    print(f"    成功加载 {len(train_data)} 条数据")
    all_data.extend(train_data)

    # 2. 加载test目录
    print("\n[2/3] 加载 test 目录...")
    test_data = load_json_files_from_dir(DATA_PATHS["test"], "test")
    print(f"    成功加载 {len(test_data)} 条数据")
    all_data.extend(test_data)

    # 3. 加载sample_result.json
    print("\n[3/3] 加载 sample_result.json...")
    sample_data = load_sample_result(DATA_PATHS["sample"])
    print(f"    成功加载 {len(sample_data)} 条数据")
    all_data.extend(sample_data)

    print("\n" + "=" * 50)
    print(f"📊 总计加载: {len(all_data)} 条原始数据")
    print("=" * 50)

    return all_data


def process_and_import(km: KnowledgeManager, data_list: list):
    """处理并导入数据"""
    # 按分类统计
    category_stats = defaultdict(int)
    category_cases = defaultdict(list)
    filtered_count = 0
    duplicate_count = 0

    for data in data_list:
        question = data.get("question", "")
        answer = data.get("answer", "")
        cause = data.get("cause", "")
        source = data.get("_source", "unknown")

        # 对于sample_result，没有question，尝试从answer中提取关键词
        if not question and answer:
            # 用答案的前50字作为问题
            question = answer[:50] + "..."

        # 去重检查
        if question and is_duplicate(question):
            duplicate_count += 1
            continue

        # 清理答案
        clean_answer = clean_text(answer)

        # 验证有效性
        if not is_valid_answer(clean_answer):
            filtered_count += 1
            continue

        # 确定分类
        category = classify_question(question, cause)

        # 提取标题
        if question:
            title = question[:35] + "..." if len(question) > 35 else question
        else:
            title = f"法律问答_{data.get('id', len(category_cases[category]))}"

        # 案例摘要
        summary = clean_answer[:200] + "..." if len(clean_answer) > 200 else clean_answer

        category_cases[category].append({
            "title": title,
            "summary": summary,
            "full_answer": clean_answer,
            "question": question,
            "source": source
        })
        category_stats[category] += 1

    # 显示过滤统计
    print(f"\n📊 数据处理统计:")
    print(f"  有效数据: {sum(category_stats.values())} 条")
    print(f"  过滤掉: {filtered_count} 条 (质量过低或广告)")
    print(f"  重复数据: {duplicate_count} 条")

    # 显示分类统计
    print(f"\n📊 分类统计:")
    for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count} 条")

    # 导入到知识库
    print(f"\n📚 导入到知识库...")

    for category, cases in category_cases.items():
        # 检查分类是否存在
        existing_categories = km.get_all_categories()

        if category not in existing_categories:
            # 创建新分类
            keywords = CATEGORY_MAPPING.get(category, [category])
            content = f"【{category}常见法律问答】\n\n包含 {len(cases)} 条典型法律问答，涵盖各类法律问题解答。"

            km.add_category(
                category=category,
                title=f"{category}法律知识库",
                content=content,
                keywords=keywords,
                cases=[]
            )
            print(f"  ✅ 创建分类: {category}")

        # 添加案例（每个分类最多150条）
        existing_category = km.get_category(category)
        existing_titles = set(c["title"] for c in existing_category.get("cases", []))

        added = 0
        for case in cases[:150]:
            if case["title"] not in existing_titles:
                km.add_case(category, case["title"], case["summary"])
                added += 1

        if added > 0:
            print(f"  📝 {category}: 添加 {added} 条案例")

    return category_stats


def export_backup(km: KnowledgeManager):
    """导出知识库备份"""
    backup_path = os.path.join(project_root, "knowledge_base_backup.json")

    # 获取所有分类数据
    backup_data = {}
    for category in km.get_all_categories():
        backup_data[category] = km.get_category(category)

    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 知识库已备份到: {backup_path}")


def main():
    print("=" * 70)
    print("法律问答数据综合导入工具")
    print("=" * 70)
    print("数据源:")
    for name, path in DATA_PATHS.items():
        print(f"  {name}: {path}")
    print("=" * 70)

    # 1. 加载所有数据
    print("\n🔍 正在加载数据...")
    all_data = load_all_data()

    if not all_data:
        print("❌ 没有找到任何数据")
        return

    # 2. 初始化知识库管理器
    print("\n🔧 初始化知识库...")
    km = KnowledgeManager()

    # 3. 处理并导入
    category_stats = process_and_import(km, all_data)

    # 4. 导出备份
    export_backup(km)

    # 5. 显示最终统计
    stats = km.get_stats()
    print("\n" + "=" * 70)
    print("📊 最终统计:")
    print(f"  知识库分类数: {stats['total_categories']}")
    print(f"  案例总数: {stats['total_cases']}")
    print(f"  向量片段数: {stats['vector_stats']['total_documents']}")
    print(f"  词汇表大小: {stats['vector_stats']['vocabulary_size']}")
    print("=" * 70)
    print("\n✅ 导入完成！")
    print("\n提示: 可以运行代码查看所有分类")


if __name__ == "__main__":
    main()