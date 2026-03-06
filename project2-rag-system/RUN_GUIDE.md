# 项目2运行指南

## 📋 前置要求

- Python 3.10+
- pip 包管理器
- 文本编辑器（可选）

---

## 🚀 快速开始（5分钟）

### 1. 克隆项目

```bash
git clone https://github.com/CattleZhao/llm-learning.git
cd llm-learning/project2-rag-system
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置API密钥

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的 ZHIPUAI_API_KEY
# Windows: notepad .env
# Mac: nano .env
```

在 `.env` 中配置：
```env
ZHIPUAI_API_KEY=你的密钥
```

### 4. 运行应用

```bash
# 方式1: 使用启动脚本（推荐）
./run.sh

# 方式2: 直接运行
streamlit run src/app.py
```

应用会自动打开浏览器：`http://localhost:8501`

---

## 📖 使用说明

### 添加文档

**方式1: 粘贴文本**
1. 在左侧"文档管理"标签页
2. 在文本框中粘贴文档内容
3. 输入文档名称（可选）
4. 点击"添加文本到知识库"

**方式2: 上传文件**
1. 点击"选择文档"
2. 选择 `.txt` 或 `.md` 文件
3. 点击"处理上传的文件"

### 提问

1. 切换到"智能问答"标签页
2. 输入问题
3. 点击"提问"按钮
4. 查看答案和相关来源

---

## 🔧 常见问题

### Q: 提示 "ModuleNotFoundError"

**A**: 依赖没装好，运行：
```bash
pip install -r requirements.txt
```

### Q: 提示 "ZHIPUAI_API_KEY not found"

**A**: 检查 `.env` 文件是否存在，并正确填写密钥。

### Q: 应用打不开

**A**: 检查端口8501是否被占用，或手动指定端口：
```bash
streamlit run src/app.py --server.port 8502
```

### Q: 如何停止应用

**A**: 在终端按 `Ctrl + C`

---

## 📁 项目结构

```
project2-rag-system/
├── src/
│   ├── app.py               # Streamlit主应用
│   ├── document_loader.py   # 文档加载器
│   ├── text_splitter.py     # 文本分块器
│   ├── embeddings.py        # 向量嵌入
│   ├── vector_store.py      # 向量存储
│   ├── rag_chain.py         # RAG问答链
│   └── llm_client.py        # LLM客户端
├── data/
│   ├── documents/           # 上传的文档（可选）
│   └── chroma/              # 向量数据库（自动生成）
├── .env                     # API密钥配置
├── requirements.txt         # Python依赖
└── run.sh                   # 启动脚本
```

---

## 🎯 功能演示流程

1. **添加知识**
   - 粘贴一段关于Python的文本
   - 添加到知识库

2. **提问**
   - 问："Python是什么？"
   - 查看基于你添加的文本生成的答案

3. **查看来源**
   - 答案下方显示相关文档片段
   - 知道答案来自哪些文档

---

## 💡 提示

- 首次运行会下载依赖，需要几分钟
- 向量数据存储在 `data/chroma/` 目录
- 可以多次添加文档，会累积到知识库
- 点击"清空知识库"可以重新开始

---

## 🐛 故障排除

### Windows用户

如果遇到激活虚拟环境失败：
```bash
# 尝试
python -m venv venv
venv\Scripts\activate
```

如果遇到编码问题：
```bash
# 设置环境变量
set PYTHONIOENCODING=utf-8
```

### Mac/Linux用户

如果遇到权限问题：
```bash
chmod +x run.sh
```

---

需要帮助？查看项目README或提Issue到GitHub！
