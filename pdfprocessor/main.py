# main.py
import os
import json
from datetime import datetime
from pdfprocessor.pdf_processor import PDFBatchProcessor
from pdfprocessor.knowledge_base import DeepSeekKnowledgeBase

class PDFComparisonSystem:
    def __init__(self, api_key: str):
        # 初始化核心组件
        self.processor = PDFBatchProcessor()
        self.kb = DeepSeekKnowledgeBase(api_key)
        
        # 路径配置
        self.config = {
            "input_dir": "./test_files/input",
            "processed_dir": "./processed_data",
            "index_dir": "./vector_index",
            "output_dir": "./comparison_results"
        }
        
        # 创建必要目录
        for path in self.config.values():
            os.makedirs(path, exist_ok=True)

    def process_pipeline(self):
        """完整处理流水线"""
        # 步骤1：PDF预处理
        print("正在处理PDF文件...")
        self.processor.process_directory(
            self.config["input_dir"],
            self.config["processed_dir"]
        )
        
        # 步骤2：构建知识库
        print("\n构建向量知识库...")
        json_files = [f for f in os.listdir(self.config["processed_dir"]) 
                     if f.endswith('.json')]
        
        for json_file in json_files:
            self.kb.load_processed_data(
                os.path.join(self.config["processed_dir"], json_file)
            )
        
        # 保存索引以便复用
        self.kb.save_index(self.config["index_dir"])
        
        # 步骤3：执行比对任务
        self.run_comparison()

    def run_comparison(self):
        """执行比对逻辑（结合网页6/7的PDF比对原理）"""
        # 加载预构建的索引
        self.kb.load_index(self.config["index_dir"])
        
        while True:
            # 用户交互界面
            print("\n=== 潜艇图纸比对系统 ===")
            print("1. 输入待校对的图纸描述")
            print("2. 批量处理目录中的图纸")
            print("3. 退出系统")
            
            choice = input("请选择操作：")
            
            if choice == '1':
                query = input("请输入需要校对的问题描述（例如：'第15页推进器轴径尺寸是否合规'）：")
                self._execute_single_query(query)
            elif choice == '2':
                self._batch_process()
            elif choice == '3':
                break
            else:
                print("无效输入，请重新选择")

    def _execute_single_query(self, query: str):
        """执行单次查询（网页5的API调用最佳实践）"""
        try:
            result = self.kb.query_knowledge(query)
            
            if result["status"] == "success":
                # 生成带时间戳的报告
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(
                    self.config["output_dir"],
                    f"comparison_{timestamp}.json"
                )
                
                with open(output_path, 'w') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                # 控制台格式化输出
                self._pretty_print(result["data"])
                print(f"\n结果已保存至：{output_path}")
            else:
                print(f"错误：{result['message']}")
        
        except Exception as e:
            print(f"系统错误：{str(e)}")

    def _batch_process(self):
        """批量处理模式"""
        task_file = input("请输入批量任务描述文件路径：")
        
        try:
            with open(task_file, 'r') as f:
                queries = [line.strip() for line in f if line.strip()]
            
            print(f"发现{len(queries)}个待处理任务")
            for idx, query in enumerate(queries, 1):
                print(f"\n处理任务 {idx}/{len(queries)}: {query}")
                self._execute_single_query(query)
        
        except FileNotFoundError:
            print("错误：指定文件不存在")

    def _pretty_print(self, data: dict):
        """美化输出"""
        print("\n=== 比对结果 ===")
        # 差异详情
        for diff in data["differences"]:
            print(f"[页码 {diff['position']}]")
            print(f"错误类型：{diff['error_type']}")
            print(f"检测值：{diff['original_value']}")
            print(f"标准值：{diff['expected_value']}")
            print(f"置信度：{diff['confidence']*100:.1f}%")
            print("-"*40)
        
        # 汇总统计
        summary = data["summary"]
        print(f"\n总错误数：{summary['total_errors']}")
        print("关键问题：")
        for issue in summary["critical_issues"]:
            print(f"• {issue}")
        
        print("\n修正建议：")
        for suggestion in summary["suggested_corrections"]:
            print(f"→ {suggestion}")

if __name__ == "__main__":
    # 从环境变量读取API密钥
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        raise ValueError("请设置环境变量DEEPSEEK_API_KEY")
    
    system = PDFComparisonSystem(api_key)
    system.process_pipeline()