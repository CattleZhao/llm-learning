#!/usr/bin/env python3
"""
历史文档批量导入脚本

用法:
    python scripts/import_history.py --dir knowledge_base/raw/analyses/
    python scripts/import_history.py --file report.pdf
"""
import argparse
import logging
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import DocumentImporter, get_vector_store

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="导入历史分析文档")
    parser.add_argument("--dir", help="批量导入目录")
    parser.add_argument("--file", help="单个文件")
    parser.add_argument("--pattern", default="*.pdf", help="文件匹配模式")

    args = parser.parse_args()

    vector_store = get_vector_store()
    importer = DocumentImporter(vector_store=vector_store)

    if args.file:
        # 单个文件导入
        logger.info(f"导入文件: {args.file}")

        try:
            result = importer.import_pdf(args.file)
            logger.info(f"✅ 导入成功: {result.get('source_file')}")
        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")

    elif args.dir:
        # 批量导入
        dir_path = Path(args.dir)

        if not dir_path.exists():
            logger.error(f"目录不存在: {args.dir}")
            return

        logger.info(f"批量导入目录: {args.dir}")
        logger.info(f"匹配模式: {args.pattern}")

        results = importer.import_batch(str(dir_path), args.pattern)

        success = sum(1 for r in results if "error" not in r)
        failed = len(results) - success

        logger.info(f"\n导入完成:")
        logger.info(f"  ✅ 成功: {success}")
        logger.info(f"  ❌ 失败: {failed}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
