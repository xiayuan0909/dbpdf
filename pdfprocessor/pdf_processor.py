import os
import pickle
import json
import numpy as np
from PyPDF2 import PdfReader  # 使用PyPDF2代替PyMuPDF
from sentence_transformers import SentenceTransformer

class PDFBatchProcessor:
    def __init__(self):
        # 初始化向量模型
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # 用于保存已处理文件的文本和向量的字典
        self.processed_files = {
            'file1': {'text': [], 'vectors': []},
            'file2': {'text': [], 'vectors': []}
        }
        # 用于存储临时数据的目录
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'processed_data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 尝试从持久化存储加载已处理的数据
        self.load_processed_data()
    
    def load_processed_data(self):
        """从持久化存储加载已处理的数据"""
        for file_key in ['file1', 'file2']:
            text_path = os.path.join(self.data_dir, f'{file_key}_text.json')
            vectors_path = os.path.join(self.data_dir, f'{file_key}_vectors.pkl')
            
            if os.path.exists(text_path) and os.path.exists(vectors_path):
                try:
                    with open(text_path, 'r', encoding='utf-8') as f:
                        self.processed_files[file_key]['text'] = json.load(f)
                    
                    with open(vectors_path, 'rb') as f:
                        self.processed_files[file_key]['vectors'] = pickle.load(f)
                        
                    print(f"已加载 {file_key} 的处理数据: {len(self.processed_files[file_key]['text'])} 个文本块")
                except Exception as e:
                    print(f"加载处理数据时出错: {str(e)}")
    
    def save_processed_data(self, file_key):
        """将处理后的数据保存到持久化存储"""
        text_path = os.path.join(self.data_dir, f'{file_key}_text.json')
        vectors_path = os.path.join(self.data_dir, f'{file_key}_vectors.pkl')
        
        try:
            with open(text_path, 'w', encoding='utf-8') as f:
                json.dump(self.processed_files[file_key]['text'], f, ensure_ascii=False)
            
            with open(vectors_path, 'wb') as f:
                pickle.dump(self.processed_files[file_key]['vectors'], f)
            print(f"已保存 {file_key} 的处理数据")
            return True
        except Exception as e:
            print(f"保存处理数据时出错: {str(e)}")
            return False
    
    def process_uploaded_file(self, file_key, file_path):
        """处理上传的PDF文件并保存结果"""
        try:
            print(f"开始处理文件: {file_path}")
            # 读取和提取PDF文本
            text_chunks = self.extract_text_from_pdf(file_path)
            if not text_chunks:
                print(f"无法从文件提取文本: {file_path}")
                return False
            
            print(f"成功提取 {len(text_chunks)} 个文本块")
            
            # 对文本进行向量化
            vectors = self.vectorize_text(text_chunks)
            print(f"向量化完成，生成 {len(vectors)} 个向量")
            
            # 存储处理后的结果
            self.processed_files[file_key]['text'] = text_chunks
            self.processed_files[file_key]['vectors'] = vectors
            
            # 保存处理结果
            success = self.save_processed_data(file_key)
            
            return success
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def extract_text_from_pdf(self, pdf_path, chars_per_chunk=1000):
        """从PDF文件中提取文本，并按指定字符数分块"""
        text_chunks = []
        current_chunk = ""
        
        try:
            # 使用PyPDF2打开PDF文件
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                
                # 遍历每一页
                for page in reader.pages:
                    page_text = page.extract_text()
                    if not page_text.strip():
                        continue
                        
                    # 按段落拆分
                    paragraphs = page_text.split('\n\n')
                    
                    for paragraph in paragraphs:
                        # 如果段落为空，则跳过
                        if not paragraph.strip():
                            continue
                        
                        # 如果当前块加上新段落不超过限制，则添加到当前块
                        if len(current_chunk) + len(paragraph) <= chars_per_chunk:
                            current_chunk += paragraph + " "
                        else:
                            # 否则，保存当前块并开始新块
                            if current_chunk:
                                text_chunks.append(current_chunk.strip())
                            current_chunk = paragraph + " "
            
            # 添加最后一个块
            if current_chunk:
                text_chunks.append(current_chunk.strip())
                
            return text_chunks
        except Exception as e:
            print(f"提取PDF文本时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def vectorize_text(self, text_chunks):
        """将文本块转换为向量"""
        try:
            # 使用sentence-transformers模型将文本转换为向量
            vectors = self.model.encode(text_chunks, show_progress_bar=True)
            return vectors
        except Exception as e:
            print(f"向量化文本时出错: {str(e)}")
            return []
    
    def search_similar_text(self, query, file_key='file1', top_k=3, similarity_threshold=0.2):
        """在指定文件中搜索与查询最相似的文本块"""
        try:
            text_chunks = self.processed_files[file_key]['text']
            vectors = self.processed_files[file_key]['vectors']
            
            if not text_chunks or len(vectors) == 0:
                print(f"{file_key} 没有处理过的数据")
                return []
            
            # 向量化查询
            query_vector = self.model.encode([query])[0]
            
            # 计算相似度
            similarities = np.dot(vectors, query_vector) / (np.linalg.norm(vectors, axis=1) * np.linalg.norm(query_vector))
            
            # 获取前K个最相似的索引
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            # 构建结果
            results = []
            for idx in top_indices:
                similarity = float(similarities[idx])
                # 只返回相似度超过阈值的结果
                if similarity >= similarity_threshold:
                    results.append({
                        'text': text_chunks[idx],
                        'similarity': similarity
                    })
                    print(f"{file_key} - 找到匹配: 相似度={similarity:.4f}")
            
            return results
        except Exception as e:
            print(f"搜索相似文本时出错: {str(e)}")
            return []

if __name__ == "__main__":
    processor = PDFBatchProcessor()
    
    input_dir = "./test_files/input/"  # 替换为实际PDF路径
    output_dir = "./test_files/output"
    
    # 示例处理文件
    file_key = 'file1'
    file_path = os.path.join(input_dir, 'example.pdf')
    processor.process_uploaded_file(file_key, file_path)
    
    # 示例查询
    query = "示例查询内容"
    results = processor.search_similar_text(query, file_key=file_key)
    print(f"查询结果: {results}")