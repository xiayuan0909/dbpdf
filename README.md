# 文件上传预览系统

这是一个基于Django的文件上传和预览系统，支持PDF和Word文档的上传、预览和下载。

## 功能特点

- 支持PDF和Word文档上传
- PDF文件在线预览，支持缩放功能
- Word文档下载查看
- 简洁的用户界面
- 实时上传状态提示

## 技术栈

- Django 后端框架
- PDF.js 用于PDF预览
- Bootstrap 5 用于UI设计
- AJAX 用于异步文件上传

## 安装说明

1. 克隆项目：
```bash
git clone [项目地址]
cd [项目目录]
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 运行数据库迁移：
```bash
python manage.py migrate
```

5. 启动开发服务器：
```bash
python manage.py runserver
```

6. 访问 http://127.0.0.1:8000 查看应用

## 使用说明

1. 在左侧和中间面板分别上传PDF或Word文档
2. PDF文件可以直接在线预览，使用缩放按钮调整大小
3. Word文档需要下载后查看
4. 右侧面板为聊天功能（示意）

## 注意事项

- 确保有足够的磁盘空间用于文件存储
- 建议在生产环境中配置HTTPS
- 可以根据需要调整文件大小限制 