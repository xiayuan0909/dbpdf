import os
import re
import json
from typing import List, Dict,Any
import requests
#from pdfplumber import PDFPlumberLoader
#from langchain.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from openai import OpenAI

class DeepSeekKnowledgeBase:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-large-zh-v1.5")
        self.vector_store = None
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _build_system_prompt(self) -> str:
        """构建系统级提示模板"""
        return json.dumps({
            "requirement": "作为图纸指标比对专家，请严格按以下规则输出：",
            "rules": [
                "1. 对比当前图纸与知识库的差异",
                "2. 识别尺寸标注/材料规格/装配关系的错误",
                "3. 按JSON格式输出比对结果"
            ],
            "response_format": {
                "differences": [{
                    "position": "图纸坐标/页码",
                    "error_type": "尺寸错误|材料不符|...",
                    "original_value": "原数据",
                    "expected_value": "知识库数据",
                    "confidence": 0.0-1.0
                }],
                "summary": {
                    "total_errors": "N",
                    "critical_issues": ["..."],
                    "suggested_corrections": ["..."]
                }
            },
            "example": {
                "differences": [{
                    "position": "Page12 (x:120,y:80)",
                    "error_type": "尺寸误差",
                    "original_value": "舱门直径350mm",
                    "expected_value": "400mm ±5mm",
                    "confidence": 0.95
                }],
                "summary": {
                    "total_errors": 3,
                    "critical_issues": ["耐压壳体厚度不足"],
                    "suggested_corrections": ["按GB/T12345标准修正"]
                }
            }
        }, ensure_ascii=False)

    def load_processed_data(self, json_path: str):
        with open(json_path, 'r') as f:
            data = json.load(f)
        texts = [chunk["text"] for chunk in data["chunks"]]
        embeddings = [chunk["embedding"] for chunk in data["chunks"]]
        metadatas = [chunk["metadata"] for chunk in data["chunks"]]
        if self.vector_store is None:
            self.vector_store = FAISS.from_embeddings(
                text_embeddings=list(zip(texts, embeddings)),
                embedding=self.embeddings,
                metadatas=metadatas
                )
        else:
            self.vector_store.add_embeddings(
            text_embeddings=list(zip(texts, embeddings)),
            metadatas=metadatas
                )


    def query_knowledge(self, question: str, top_k=5) -> Dict[str, Any]:
        """增强版查询方法"""
        # 1. 增强检索
        docs = self.vector_store.max_marginal_relevance_search(question, k=top_k)
        context = "\n".join([f"知识片段{i+1}: {doc.page_content}" for i, doc in enumerate(docs)])
        
        # 2. 构建消息列表
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt()
            },
            {
                "role": "user",
                "content": f"当前图纸问题：{question}\n相关知识库内容：{context}"
            }
        ]
        
        # 3. API调用
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2000,
            "response_format": {"type": "json_object"}  # 强制JSON输出
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=self.headers,
            json=payload
        )

        # 4. 增强解析
        try:
            result = json.loads(response.json()["choices"][0]["message"]["content"])
            return {
                "status": "success",
                "data": result,
                "metadata": {
                    "source_docs": [doc.metadata for doc in docs],
                    "model_used": "deepseek-chat-v3"
                }
            }
        except json.JSONDecodeError:
            return {
                "status": "error",
                "message": "Invalid JSON format",
                "raw_response": response.text
            }

    def save_index(self, path: str):
        """保存向量索引"""
        if self.vector_store is not None:
            # 添加安全序列化配置
            self.vector_store.save_local(
                folder_path=path,
                index_name="index.faiss",
                create_path=True
            )

            
    def load_index(self, path: str):
        """加载向量索引"""
        self.vector_store = FAISS.load_local(
            folder_path=path,
            embeddings=self.embeddings,
            index_name="index.faiss",
            allow_dangerous_deserialization=True,  # 显式启用安全风险确认
            normalize_L2=True  # 添加归一化选项
        )