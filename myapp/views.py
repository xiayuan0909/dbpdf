from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import os
import sys

# 添加PDF处理器到系统路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pdfprocessor'))
from pdf_processor import PDFBatchProcessor
from .message_handler import MessageHandler

ALLOWED_EXTENSIONS = {'.pdf'}
pdf_processor = PDFBatchProcessor()
message_handler = MessageHandler()

def index(request: HttpRequest):
    if request.method == 'POST':
        # 检查是否是AJAX请求
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response_data = {}
            error_message = None

            for field in ['file1', 'file2']:
                uploaded = request.FILES.get(field)
                if uploaded:
                    # 检查文件扩展名
                    file_ext = os.path.splitext(uploaded.name)[1].lower()
                    if file_ext not in ALLOWED_EXTENSIONS:
                        error_message = f"不支持的文件类型: {file_ext}。只支持PDF文档。"
                        break

                    try:
                        fs = FileSystemStorage()
                        filename = fs.save(uploaded.name, uploaded)
                        file_path = fs.path(filename)  # 获取文件的完整系统路径
                        file_url = fs.url(filename)
                        
                        # 构建完整的URL
                        full_url = request.build_absolute_uri(file_url)
                        # 确保URL是HTTP（开发服务器只支持HTTP）
                        full_url = full_url.replace('https://', 'http://')
                        
                        # 构建PDF.js使用的URL
                        pdfjs_url = request.build_absolute_uri(file_url)
                        pdfjs_url = pdfjs_url.replace('https://', 'http://')

                        # 立即处理并保存结果
                        processing_result = pdf_processor.process_uploaded_file(field, file_path)
                            
                        response_data[f"{field}_url"] = pdfjs_url
                        response_data[f"{field}_full_url"] = full_url
                        response_data[f"{field}_processed"] = processing_result
                    except Exception as e:
                        error_message = f"文件上传失败: {str(e)}"
                        break

            if error_message:
                return JsonResponse({'error': error_message}, status=400)
            return JsonResponse(response_data)
        else:
            # 处理普通表单提交
            context = {}
            for field in ['file1', 'file2']:
                uploaded = request.FILES.get(field)
                if uploaded:
                    file_ext = os.path.splitext(uploaded.name)[1].lower()
                    if file_ext not in ALLOWED_EXTENSIONS:
                        context['error_message'] = f"不支持的文件类型: {file_ext}。只支持PDF文档。"
                        continue

                    try:
                        fs = FileSystemStorage()
                        filename = fs.save(uploaded.name, uploaded)
                        file_path = fs.path(filename)  # 获取文件的完整系统路径
                        file_url = fs.url(filename)
                        
                        # 构建完整的URL
                        full_url = request.build_absolute_uri(file_url)
                        # 确保URL是HTTP（开发服务器只支持HTTP）
                        full_url = full_url.replace('https://', 'http://')
                        
                        # 构建PDF.js使用的URL
                        pdfjs_url = request.build_absolute_uri(file_url)
                        pdfjs_url = pdfjs_url.replace('https://', 'http://')
                        
                        # 立即处理PDF文件
                        processing_result = pdf_processor.process_uploaded_file(field, file_path)

                        context[f"{field}_url"] = pdfjs_url
                        context[f"{field}_full_url"] = full_url
                        context[f"{field}_processed"] = processing_result
                    except Exception as e:
                        context['error_message'] = f"文件上传失败: {str(e)}"

            return render(request, 'index.html', context)
    else:
        return render(request, 'index.html')

@csrf_exempt
@require_POST
def handle_message(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        
        if not message:
            return JsonResponse({'error': '消息不能为空'}, status=400)
        
        # 使用MessageHandler处理消息
        response = message_handler.handle_message(message)
        
        return JsonResponse({'response': response})
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON格式'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)