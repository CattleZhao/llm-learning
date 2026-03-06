# src/main.py
import os
import sys
from dotenv import load_dotenv

from .qa_module import QAModule
from .summary_module import SummaryModule
from .structured_output import StructuredExtractor

# 加载环境变量
load_dotenv()

def print_menu():
    """打印菜单"""
    print("\n" + "="*50)
    print("大模型基础API应用")
    print("="*50)
    print("1. 问答 (Q&A)")
    print("2. 文档摘要")
    print("3. 结构化输出")
    print("4. 退出")
    print("="*50)

def qa_mode():
    """问答模式"""
    print("\n--- 问答模式 ---")
    question = input("请输入问题（或输入'back'返回）: ")
    if question.lower() == 'back':
        return

    context = input("是否有上下文信息？(直接跳过) : ") or None

    qa = QAModule(provider="glm")
    answer = qa.ask(question, context)
    print(f"\n答案: {answer}\n")

def summary_mode():
    """摘要模式"""
    print("\n--- 文档摘要模式 ---")
    print("请输入要摘要的文本（输入'END'结束输入）:")

    lines = []
    while True:
        line = input()
        if line.strip() == 'END':
            break
        lines.append(line)

    text = '\n'.join(lines)
    if not text.strip():
        print("未输入内容")
        return

    max_length = input("最大摘要长度（可选，直接跳过）: ") or None
    if max_length:
        max_length = int(max_length)

    summary = SummaryModule(provider="glm")
    result = summary.summarize(text, max_length)
    print(f"\n摘要: {result}\n")

def structured_mode():
    """结构化输出模式"""
    print("\n--- 结构化输出模式 ---")
    print("请输入包含人物信息的文本:")

    text = input("> ")
    if not text.strip():
        print("未输入内容")
        return

    extractor = StructuredExtractor(provider="glm")
    result = extractor.extract_person_info(text)
    print(f"\n提取结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    print()

def main():
    """主函数"""
    # 检查API密钥
    if not os.getenv("ZHIPUAI_API_KEY"):
        print("错误: 请在.env文件中配置ZHIPUAI_API_KEY")
        print("复制 .env.example 到 .env 并填入你的密钥")
        sys.exit(1)

    while True:
        print_menu()
        choice = input("请选择功能 (1-4): ").strip()

        if choice == '1':
            qa_mode()
        elif choice == '2':
            summary_mode()
        elif choice == '3':
            structured_mode()
        elif choice == '4':
            print("再见！")
            break
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main()
