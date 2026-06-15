项目简介
本项目是一个基于RAG（检索增强生成）技术的智能法律咨询系统。系统采用B/S架构，集成了本地知识库检索、智能体Agent工具调用、长期记忆增强、多模态支持（图像分析+语音输入）以及增强版文书模板引擎等核心功能，为用户提供专业、准确、可追溯的法律咨询服务。

核心功能
功能模块	说明
双模式对话	普通模式（面向当事人）+ 专业模式（面向律师/法律从业者）
RAG检索增强	本地向量知识库检索，每次回答有据可依
14类场景识别	民间借贷、劳动纠纷、交通事故、婚姻家庭、刑事法律、房产纠纷、合同纠纷、侵权责任、诉讼程序、公司法律、知识产权、消费者权益、行政法律、继承法律
智能体Agent	法律条文检索、相似案例检索、赔偿计算、时效检查、文书草拟、用户提醒
长期记忆	用户档案管理 + 对话摘要存储，支持跨会话记忆
多模态支持	图像分析（欠条/合同/判决书识别）+ 语音输入
文书生成	模板填充 + AI智能生成双模式，支持docx/txt导出
可视化工具	RAG检索过程可视化 + Agent调用时序图
技术架构

技术栈
层级	技术
前端	HTML5/CSS3/JavaScript, Axios
后端	Python Flask, SQLAlchemy ORM
数据库	SQLite
AI服务	DeepSeek API
向量检索	TF-IDF + 余弦相似度（自实现）
文档导出	python-docx
项目结构
text

lowbot/

├── app.py                      # Flask主应用

├── knowledge_base/             # 知识库模块

│   ├── __init__.py

│   ├── knowledge_manager.py    # 知识库管理器

│   ├── vector_store.py         # 向量存储引擎

│   ├── template_engine.py      # 文书模板引擎

│   ├── data/

│   │   └── legal_knowledge.json # 知识库数据（约11,700条案例）

│   ├── index/                   # 向量索引存储

│   └── document_templates/      # 文书模板文件

├── tools/                       # 管理工具

│   └── knowledge_tool.py        # 知识库命令行工具

├── templates/

│   └── index.html               # 前端页面

├── stress.py                    # 压力测试脚本

├── batch_import_laws.py         # 批量数据导入脚本

└── requirements.txt             # Python依赖

数据统计
分类	案例数量
交通事故	2,920条
婚姻家庭	2,193条
劳动纠纷	2,098条
民间借贷	1,401条
法律咨询	1,324条
房产纠纷	1,073条
诉讼程序	410条
合同纠纷	126条
刑事法律	71条
其他	93条
总计	约11,709条
快速开始
1. 环境要求
Python 3.8+

pip

2. 安装依赖
bash
pip install flask flask-sqlalchemy requests axios python-docx matplotlib numpy
3. 启动服务
bash
python app.py
4. 访问系统
打开浏览器访问：http://localhost:5004

API接口
接口	方法	说明
/	GET	首页
/chat	POST	普通模式聊天
/chat-pro	POST	专业模式聊天
/rag-search	POST	知识库检索
/rag-stats	GET	知识库统计
/generate-document	POST	AI生成文书
/generate-document-v2	POST	模板填充文书
/export-document	POST	导出文档
/template-list	GET	获取模板列表
/analyze-image	POST	图像分析
/user-profile	GET/POST	用户档案管理
/pro-stat	GET	统计信息
/risk-logs	GET	风险日志
/rag-visual	GET	RAG可视化页面
/agent-diagram	GET	Agent时序图
知识库管理
查看统计信息
bash
python tools/knowledge_tool.py stats
列出所有分类
bash
python tools/knowledge_tool.py list
搜索知识库
bash
python tools/knowledge_tool.py search "拖欠工资"
批量导入数据
bash
python batch_import_laws.py
压力测试
bash
python stress.py
核心亮点
1. RAG检索增强
自实现TF-IDF向量化 + 余弦相似度检索

14类法律场景知识库，约11,700条高质量案例

检索结果优先注入AI提示词，回答有据可依

2. 智能体Agent
六大专业工具：法律条文检索、相似案例检索、赔偿计算、时效检查、文书草拟、用户提醒

意图识别 → 并行调用 → 结果聚合 → AI增强

3. 长期记忆
UserProfile用户档案表（跨会话个人信息）

ConversationSummary对话摘要表（自动提取关键信息）

支持跨会话记忆唤醒

4. 多模态支持
图像分析：欠条/借条/合同/判决书智能识别

语音输入：浏览器原生SpeechRecognition API

5. 增强版文书模板
模板填充 + AI智能生成双模式

自动提取对话信息填充模板

缺失字段检测与引导补充

支持docx/txt格式导出

移动端前端界面
<img width="506" height="975" alt="image" src="https://github.com/user-attachments/assets/f63885b2-ecb3-4dfa-ad8d-927931134792" />

PC端前端界面
<img width="1276" height="737" alt="image" src="https://github.com/user-attachments/assets/97f65538-ea45-4611-9cd3-b8010ab3cf73" />

