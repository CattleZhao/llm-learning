# LLM Learning Path

> 从Java后端到大模型应用开发的学习之旅

## 项目简介

这是一个系统性学习大模型技术的个人项目，通过4个递进式项目掌握大模型应用开发的核心技能。

## 学习路线

```
阶段1（2-3周）：基础API调用 → 阶段2（4-6周）：RAG应用 → 阶段3（6-8周）：Agent应用 → 阶段4（3-4周）：多Agent协作
     ↓                            ↓                          ↓                            ↓
  理解大模型                   向量检索+上下文              多步推理+工具                  多Agent对话
  API使用                      增强应用                    自动化决策                      团队协作
```

## 项目结构

```
llm-learning/
├── docs/
│   └── plans/                    # 设计文档
│       ├── 2026-03-05-llm-learning-roadmap-design.md
│       ├── 2026-03-05-project1-basic-api-implementation.md
│       ├── 2026-03-05-project2-rag-system-implementation.md
│       ├── 2026-03-05-project3-code-agent-implementation.md
│       ├── 2026-03-07-project3-langchain-version-design.md
│       ├── 2026-03-07-project3-langchain-implementation.md
│       └── 2026-03-09-project4-multiagent-design.md
├── project1-basic-api/           # 项目1：基础API应用
├── project2-rag-system/          # 项目2：RAG知识库问答
├── project3-code-agent/          # 项目3：代码助手Agent
├── project3-code-agent-langchain/ # 项目3：LangChain版本
├── project4-multiagent/          # 项目4：多Agent协作团队
└── README.md
```

## 学习目标

- 掌握大模型API调用和Prompt Engineering
- 理解并实现RAG（检索增强生成）系统
- 开发智能Agent应用
- 掌握多Agent协作框架（AutoGen、CrewAI）
- 积累可展示的项目经验，助力职业转型

## 技术栈

- **语言**: Python
- **框架**: LangChain / LlamaIndex
- **Agent框架**: AutoGen / CrewAI
- **向量数据库**: ChromaDB
- **Web框架**: Streamlit / FastAPI

## 进度

- [x] 项目1：大模型基础应用
- [x] 项目2：RAG知识库问答系统
- [x] 项目3：代码助手Agent
- [ ] 项目4：多Agent协作团队

## 资源

- [学习路线设计文档](docs/plans/2026-03-05-llm-learning-roadmap-design.md)
- [Project 4 设计文档](docs/plans/2026-03-09-project4-multiagent-design.md)

## License

MIT
