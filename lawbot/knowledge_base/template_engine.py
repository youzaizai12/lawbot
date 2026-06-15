"""
法律文书模板引擎
支持：变量替换、条件渲染、列表渲染、从对话提取信息
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import os


class DocumentTemplateEngine:
    """法律文书模板填充引擎"""

    # 提取模式正则表达式
    PATTERNS = {
        # 人名
        'name': [
            r'我(?:叫|是|姓)([^，。,，\s]{2,4})',
            r'原告(?:叫|是|姓)([^，。,，\s]{2,4})',
            r'姓名[:：]([^，。,，\s]{2,4})',
            r'申请人(?:叫|是|姓)([^，。,，\s]{2,4})',
            r'本人(?:叫|姓)([^，。,，\s]{2,4})',
        ],
        # 对方/被告名称
        'defendant_name': [
            r'对方(?:叫|是|姓)([^，。,，\s]{2,8})',
            r'被告(?:叫|是|姓)([^，。,，\s]{2,8})',
            r'欠款人[:：]([^，。,，\s]{2,8})',
            r'(?:公司|单位)[叫名称]?([\u4e00-\u9fa5]{2,20}公司)',
            r'被申请人(?:叫|是|姓)([^，。,，\s]{2,8})',
        ],
        # 金额
        'amount': [
            r'(\d+(?:\.\d+)?)\s*万?\s*元',
            r'金额[为是](\d+(?:\.\d+)?)\s*元',
            r'欠[了我]?(\d+(?:\.\d+)?)\s*元',
            r'赔偿(\d+(?:\.\d+)?)\s*元',
            r'工资(\d+(?:\.\d+)?)\s*元',
        ],
        # 日期
        'date': [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(\d{4}-\d{1,2}-\d{1,2})',
            r'(\d{1,2}月\d{1,2}日)',
        ],
        # 工作年限
        'work_years': [
            r'工作(\d+(?:\.\d+)?)\s*年',
            r'入职(\d+(?:\.\d+)?)\s*年',
            r'工作了(\d+(?:\.\d+)?)\s*年',
        ],
        # 利率
        'interest_rate': [
            r'利率(\d+(?:\.\d+)?)%',
            r'年化(\d+(?:\.\d+)?)%',
            r'月息(\d+(?:\.\d+)?)[分厘]',
        ],
        # 罪名
        'crime': [
            r'涉嫌([\u4e00-\u9fa5]{2,10})罪',
            r'构成([\u4e00-\u9fa5]{2,10})罪',
            r'罪名[是为]([\u4e00-\u9fa5]{2,10})',
        ],
        # 公司名称
        'company': [
            r'([\u4e00-\u9fa5]{2,30}(?:公司|有限公司|股份有限公司|集团))',
        ],
    }

    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), 'document_templates')
        self.templates_dir = templates_dir
        self.templates = self._load_templates_index()
        print(f"✅ 模板引擎初始化完成，共加载 {len(self.templates.get('templates', []))} 个模板")

    def _load_templates_index(self) -> Dict:
        """加载模板索引"""
        index_path = os.path.join(self.templates_dir, 'templates_index.json')
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        print("⚠️ 未找到模板索引文件，请检查路径")
        return {"templates": []}

    def get_all_templates(self) -> List[Dict]:
        """获取所有模板列表"""
        return self.templates.get('templates', [])

    def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """根据ID获取模板"""
        for tpl in self.templates.get('templates', []):
            if tpl['id'] == template_id:
                return self._load_template_file(tpl['file'])
        return None

    def get_template_by_type(self, doc_type: str, scene: str = None) -> Optional[Dict]:
        """根据文书类型和场景获取模板"""
        for tpl in self.templates.get('templates', []):
            if tpl['type'] == doc_type:
                if scene is None or scene in tpl.get('scenes', []):
                    return self._load_template_file(tpl['file'])
        return None

    def _load_template_file(self, file_path: str) -> Optional[Dict]:
        """加载模板文件"""
        full_path = os.path.join(self.templates_dir, file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        print(f"⚠️ 模板文件不存在: {full_path}")
        return None

    def extract_info_from_text(self, text: str, scene: str = "contract") -> Dict[str, Any]:
        """从文本中提取信息"""
        extracted = {
            "plaintiff_name": "", "applicant_name": "", "defendant_name": "", "respondent_name": "",
            "amount": "", "total_price": "", "salary": "",
            "date": datetime.now().strftime("%Y年%m月%d日"),
            "sign_date": datetime.now().strftime("%Y年%m月%d日"),
            "work_years": "",
            "interest_rate": "",
            "crime_charge": "",
            "court_name": "有管辖权的人民法院",
            "arbitration_commission": "有管辖权的劳动人事争议仲裁委员会",
            "contract_name": "",
            "facts": "",
        }

        # 提取人名
        for pattern in self.PATTERNS['name']:
            match = re.search(pattern, text)
            if match:
                extracted["plaintiff_name"] = match.group(1)
                extracted["applicant_name"] = match.group(1)
                break

        # 提取对方名称
        for pattern in self.PATTERNS['defendant_name']:
            match = re.search(pattern, text)
            if match:
                extracted["defendant_name"] = match.group(1)
                extracted["respondent_name"] = match.group(1)
                break

        # 提取金额
        amounts = []
        for pattern in self.PATTERNS['amount']:
            matches = re.findall(pattern, text)
            for m in matches:
                amount_str = m if isinstance(m, str) else m[0]
                amounts.append(amount_str)
        if amounts:
            extracted["amount"] = amounts[0]
            extracted["total_price"] = amounts[0]

        # 提取日期
        for pattern in self.PATTERNS['date']:
            match = re.search(pattern, text)
            if match:
                extracted["date"] = match.group(1)
                extracted["sign_date"] = match.group(1)
                break

        # 提取工作年限
        for pattern in self.PATTERNS['work_years']:
            match = re.search(pattern, text)
            if match:
                extracted["work_years"] = match.group(1)
                break

        # 提取利率
        for pattern in self.PATTERNS['interest_rate']:
            match = re.search(pattern, text)
            if match:
                extracted["interest_rate"] = match.group(1)
                break

        # 提取罪名
        for pattern in self.PATTERNS['crime']:
            match = re.search(pattern, text)
            if match:
                extracted["crime_charge"] = match.group(1)
                break

        # 提取公司名
        for pattern in self.PATTERNS['company']:
            match = re.search(pattern, text)
            if match and not extracted["defendant_name"]:
                extracted["defendant_name"] = match.group(1)
                extracted["respondent_name"] = match.group(1)
                break

        # 提取事实描述
        fact_patterns = [
            r'事实(?:经过|情况|是)[：:]\s*([^。]+[。])',
            r'事情是这样的[：:]\s*([^。]+[。])',
            r'情况(?:如下|是)[：:]\s*([^。]+[。])',
        ]
        for pattern in fact_patterns:
            match = re.search(pattern, text)
            if match:
                extracted["facts"] = match.group(1)
                break
        if not extracted["facts"] and len(text) > 30:
            extracted["facts"] = text[:300]

        # 根据场景设置默认法院/仲裁委
        if scene == "labor":
            extracted["court_name"] = "有管辖权的劳动仲裁委员会"

        return extracted

    def extract_info_from_context(self, context: List[Dict], scene: str) -> Dict[str, Any]:
        """从对话历史中提取信息"""
        all_text = " ".join([
            item.get('user', '') for item in context[-15:]
            if item.get('user')
        ])
        return self.extract_info_from_text(all_text, scene)

    def _render_variable(self, text: str, data: Dict[str, Any]) -> str:
        """渲染单个变量 {{var_name}}"""

        def replacer(match):
            key = match.group(1)
            value = data.get(key, '')
            if value is None:
                return '【待补充】'
            elif isinstance(value, list):
                if value:
                    return '；'.join(str(v) for v in value)
                return '【待补充】'
            elif not str(value).strip():
                return '【待补充】'
            return str(value)

        return re.sub(r'\{\{(\w+)\}\}', replacer, text)

    def _render_list(self, text: str, data: Dict[str, Any]) -> str:
        """渲染列表 {{#list_name}}...{{/list_name}}"""
        pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'

        def replacer(match):
            list_name = match.group(1)
            inner = match.group(2)
            items = data.get(list_name, [])
            if not items:
                return ''

            results = []
            for idx, item in enumerate(items, 1):
                item_str = str(item)
                # 先处理内部变量
                rendered = inner.replace('{{index}}', str(idx))
                rendered = rendered.replace('{{item}}', item_str)
                # 处理嵌套变量
                rendered = self._render_variable(rendered, {list_name: items, 'index': idx, 'item': item_str})
                results.append(rendered)
            return '\n'.join(results)

        return re.sub(pattern, replacer, text, flags=re.DOTALL)

    def _render_condition(self, text: str, data: Dict[str, Any]) -> str:
        """渲染条件 {{#condition}}...{{/condition}}"""
        pattern = r'\{\{#(\w+)\}\}(.*?)\{\{/\1\}\}'

        # 注意：这会在处理列表之后处理，避免冲突

        def replacer(match):
            cond_name = match.group(1)
            inner = match.group(2)
            value = data.get(cond_name)

            # 判断条件是否成立
            if value and str(value).strip() and str(value) != '【待补充】':
                if isinstance(value, list) and len(value) == 0:
                    return ''
                return inner
            return ''

        return re.sub(pattern, replacer, text, flags=re.DOTALL)

    def render_template(self, template: Dict, data: Dict[str, Any]) -> Tuple[str, Dict]:
        """渲染模板，返回(文档内容, 缺失字段列表)"""
        result = []
        missing_fields = []

        # 收集所有缺失字段
        def check_missing_fields_in_section(fields_list):
            for field in fields_list:
                key = field.get('key')
                required = field.get('required', False)
                value = data.get(key, '')
                if required and (not value or value == '【待补充】'):
                    missing_fields.append({
                        'key': key,
                        'label': field.get('label', key),
                        'type': field.get('type', 'string')
                    })

        # 标题
        title = template.get('title', '法律文书')
        title = self._render_variable(title, data)
        result.append(title)
        result.append('')

        # 逐段渲染
        for section in template.get('structure', []):
            template_text = section.get('template', '')
            if not template_text:
                continue

            # 检查该section的必填字段
            fields = section.get('fields', [])
            check_missing_fields_in_section(fields)

            # 渲染列表（先处理列表，因为列表内部可能还有变量）
            rendered = self._render_list(template_text, data)
            # 渲染条件
            rendered = self._render_condition(rendered, data)
            # 渲染变量
            rendered = self._render_variable(rendered, data)

            if rendered.strip():
                result.append(rendered)
                result.append('')

        # 渲染页脚（如果有）
        footer = template.get('footer', '')
        if footer:
            footer = self._render_variable(footer, data)
            if footer.strip():
                result.append(footer)

        return '\n'.join(result), missing_fields

    def get_template_examples(self, template: Dict) -> Dict[str, Any]:
        """获取模板的示例数据"""
        examples = {}

        for section in template.get('structure', []):
            fields = section.get('fields', [])
            section_examples = section.get('examples', {})

            for field in fields:
                key = field.get('key')
                if key in section_examples:
                    examples[key] = section_examples[key]
                elif field.get('example'):
                    examples[key] = field.get('example')
                elif field.get('default'):
                    examples[key] = field.get('default')

        # 添加自动字段
        examples['date'] = datetime.now().strftime("%Y年%m月%d日")
        examples['sign_date'] = datetime.now().strftime("%Y年%m月%d日")

        return examples

    def auto_fill_with_ai(self, data: Dict, missing_fields: List[Dict], context: str) -> Dict:
        """使用AI自动填充缺失字段（可选功能）"""
        if not missing_fields:
            return data

        missing_labels = [f['label'] for f in missing_fields]
        prompt = f"""请根据以下对话内容，提取缺失的信息：

对话内容：{context[:1000]}

需要提取的信息：{', '.join(missing_labels)}

请直接输出JSON格式，只包含提取到的信息：
{{}}
"""
        # 这里可以调用AI接口
        # 简化版：返回原数据
        return data


def format_document_for_display(content: str) -> str:
    """格式化文档用于前端显示"""
    # 添加基本格式
    lines = content.split('\n')
    formatted = []
    for line in lines:
        if line.strip():
            # 检测标题（如果全是中文且长度适中）
            if len(line) < 30 and not line.startswith(' ') and line.strip():
                formatted.append(f'<h3 style="text-align:center; margin:16px 0;">{line}</h3>')
            else:
                formatted.append(f'<p style="margin:8px 0; line-height:1.6;">{line}</p>')
        else:
            formatted.append('<br>')
    return ''.join(formatted)


# 测试代码
if __name__ == '__main__':
    engine = DocumentTemplateEngine()

    # 测试提取功能
    test_text = "我叫张三，被李四的公司拖欠工资8000元，工作了2年。"
    extracted = engine.extract_info_from_text(test_text, "labor")
    print("提取结果:", extracted)

    # 测试模板加载
    template = engine.get_template_by_type("complaint")
    if template:
        print("模板名称:", template.get('name'))