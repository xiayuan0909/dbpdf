import os
import json
import sys
import requests
from typing import Dict, Any, List

class MessageHandler:
    def __init__(self):
        # DeepSeek API配置
        from dotenv import load_dotenv
        load_dotenv()
        self.api_key = os.environ.get('DEEPSEEK_API_KEY', '')
        
        # 如果环境变量为空，使用硬编码的测试密钥（仅用于开发测试）
        if not self.api_key:
            self.api_key = "sk-3909ba8edfbc49da8f0792a7bd68b358"  # 替换为你的真实API密钥
        
        # DeepSeek API 地址
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
        # 从文件加载文档内容
        self.document_content = self.load_document_content()
        
    def load_document_content(self) -> str:
        """从处理后的文件中加载文档内容"""
        content = []
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'processed_data')
        
        # 尝试加载文件1的内容
        try:
            file1_path = os.path.join(data_dir, 'file1_text.json')
            if os.path.exists(file1_path):
                with open(file1_path, 'r', encoding='utf-8') as f:
                    file1_content = json.load(f)
                    if file1_content:
                        content.append("【文档1内容】")
                        content.extend(file1_content)
        except Exception as e:
            print(f"加载文件1内容失败: {e}")
            
        # 尝试加载文件2的内容
        try:
            file2_path = os.path.join(data_dir, 'file2_text.json')
            if os.path.exists(file2_path):
                with open(file2_path, 'r', encoding='utf-8') as f:
                    file2_content = json.load(f)
                    if file2_content:
                        content.append("【文档2内容】")
                        content.extend(file2_content)
        except Exception as e:
            print(f"加载文件2内容失败: {e}")
            
        return "\n\n".join(content) if content else ""
        
    def handle_message(self, message: str) -> str:
        """处理用户消息，直接调用DeepSeek API生成回答"""
        try:
            if not self.document_content:
                return "未找到任何文档内容。请先上传PDF文件。"
            
            # 直接调用DeepSeek API生成回答
            response = self.call_deepseek_api(message, self.document_content)
            return response
            
        except Exception as e:
            print(f"处理消息时出错: {str(e)}")
            return f"处理您的请求时发生错误，请稍后再试。"
    
    def call_deepseek_api(self, query: str, context: str) -> str:
        """调用DeepSeek API生成回答"""
        if not self.api_key:
            return "API密钥未配置，无法调用DeepSeek模型。请配置DEEPSEEK_API_KEY环境变量。"
            
        try:
            # 处理特殊类型的问题，比如关于助手身份的问题
            if query.lower() in ["你是谁", "你是什么", "你叫什么", "你的身份是什么", "你是哪个模型"]:
                return """我是一个文档助手，专门用来回答与上传文档相关的问题。我的工作是分析文档内容，提取相关信息，并以清晰、准确的方式回答您的问题。

我不是独立的AI，而是一个专门为解读您上传的PDF文档而设计的工具。如果您有任何关于文档内容的问题，请随时提问，我会尽力从文档中找到相关信息来回答您。"""
                
            # 构建更强大的系统提示
            system_prompt = """你是一个专业的PDF文档分析助手。你的主要功能是帮助用户理解他们上传的PDF文档内容。请严格遵循以下原则:

1. 身份意识：当被问到你是谁时，清楚地表明你是"PDF文档助手"，专门用于分析和回答关于用户上传文档的问题。
2. 内容权威：回答必须严格基于文档内容，不要添加未在文档中明确陈述的信息。
3. 透明度：如果文档中没有足够信息回答问题，明确说明"文档中没有提供相关信息"，并具体指出缺少什么信息。
4. 精确引用：引用文档中的具体段落、页码或章节来支持你的回答。
5. 结构清晰：组织回答时使用适当的段落、列表或标题，提高可读性。
6. 简洁性：提供完整但简洁的回答，避免不必要的冗长。

记住：你是专门用来帮助用户理解他们上传的文档内容的工具。对于文档范围之外的问题，请明确表示这超出了当前文档的范围。"""

            # 构建更好的用户提示 - 减少文档内容长度以避免超出限制
            doc_excerpt = context[:8000] if len(context) > 8000 else context
            context_intro = f"""【文档内容摘要】\n\n{doc_excerpt}\n\n【文档内容摘要结束】"""
            
            if len(context) > 8000:
                context_intro += "\n\n(注：由于文档较长，上面仅显示部分内容。)"
            
            user_prompt = f"""问题: {query}

请基于提供的文档内容回答上述问题。记住:
1. 如果这个问题是关于你自己的，请表明你是一个PDF文档助手，专门用于回答关于上传文档的问题
2. 如果是关于文档内容的问题，请仅使用文档中的信息回答
3. 如果文档中没有相关信息，请直接说明
4. 回答要简洁、准确且有条理"""
            
            # 准备API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context_intro},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,  # 降低温度以获得更精确的回答
                "max_tokens": 2000
            }
            
            # 在请求前添加日志
            print(f"正在向 {self.api_url} 发送请求...")
            
            # 添加SSL验证禁用选项来解决SSL问题（仅用于开发环境）
            response = requests.post(
                self.api_url, 
                headers=headers, 
                json=payload,
                verify=False,  # 禁用SSL验证
                timeout=30  # 增加超时时间
            )
            
            print(f"收到响应状态码: {response.status_code}")
            response.raise_for_status()  # 检查HTTP错误
            
            # 解析响应
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "无法从DeepSeek API获取有效回答。请检查API响应格式是否有变化。"
                
        except requests.exceptions.RequestException as e:
            print(f"调用DeepSeek API时出错: {str(e)}")
            return f"调用DeepSeek API时出错: {str(e)}"
            
    def reload_document_content(self):
        """重新加载文档内容"""
        self.document_content = self.load_document_content()
        return len(self.document_content) > 0