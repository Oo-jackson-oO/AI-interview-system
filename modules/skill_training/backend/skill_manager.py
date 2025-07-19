import os
import base64
from PIL import Image

class SkillManager:
    def __init__(self):
        # 使用modules/modules/book路径
        self.books_folder = os.path.join(os.getcwd(), "modules", "modules", "book")
        self.cover_folder = os.path.join(self.books_folder, "cover")
        self.pdf_folder = os.path.join(self.books_folder, "pdf")
        self.ensure_book_folders()
        
    def ensure_book_folders(self):
        """确保书籍相关文件夹存在"""
        folders = [self.books_folder, self.cover_folder, self.pdf_folder]
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)
    
    def get_next_book_number(self):
        """获取下一本书的编号"""
        try:
            # 统计cover文件夹中的图片数量
            if os.path.exists(self.cover_folder):
                cover_files = [f for f in os.listdir(self.cover_folder) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                return len(cover_files) + 1
            else:
                return 1
        except Exception:
            return 1
    
    def save_uploaded_book(self, title, cover_file, pdf_file):
        """保存上传的书籍文件，使用书名重命名"""
        try:
            # 清理书名，移除特殊字符
            safe_title = self.sanitize_filename(title)
            
            # 获取文件扩展名
            cover_ext = os.path.splitext(cover_file.filename)[1].lower()
            pdf_ext = os.path.splitext(pdf_file.filename)[1].lower()
            
            # 生成新的文件名
            cover_filename = f"{safe_title}{cover_ext}"
            pdf_filename = f"{safe_title}{pdf_ext}"
            
            # 保存文件路径
            cover_path = os.path.join(self.cover_folder, cover_filename)
            pdf_path = os.path.join(self.pdf_folder, pdf_filename)
            
            # 保存封面文件
            cover_file.save(cover_path)
            
            # 保存PDF文件
            pdf_file.save(pdf_path)
            
            return {
                "title": title,
                "cover": cover_path,
                "pdf": pdf_path,
                "filename": safe_title
            }
            
        except Exception as e:
            raise Exception(f"保存文件失败: {str(e)}")
    
    def sanitize_filename(self, filename):
        """清理文件名，移除特殊字符"""
        import re
        # 移除或替换特殊字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除多余的空格和连字符
        safe_name = re.sub(r'\s+', '_', safe_name.strip())
        # 移除开头和结尾的特殊字符
        safe_name = re.sub(r'^[._]+|[._]+$', '', safe_name)
        return safe_name
    
    def get_preset_books(self):
        """获取预设书籍列表"""
        return [
            {"title": "军事理论", "cover": os.path.join(self.cover_folder, "军事理论.png"), "pdf": os.path.join(self.pdf_folder, "084733-01.pdf")},
            {"title": "数据管理分析", "cover": os.path.join(self.cover_folder, "数据管理.png"), "pdf": os.path.join(self.pdf_folder, "084733-01.pdf")},
            {"title": "操作系统原理", "cover": os.path.join(self.cover_folder, "f0549ae0dbadb44431d7931c4f6db31.png"), "pdf": os.path.join(self.pdf_folder, "084733-01.pdf")},
            {"title": "计算机网络", "cover": os.path.join(self.cover_folder, "e0928b4989ad49c1ab22a656927f2df.png"), "pdf": os.path.join(self.pdf_folder, "084733-01.pdf")},
            {"title": "deepseek", "cover": os.path.join(self.cover_folder, "deepseek.png"), "pdf": os.path.join(self.pdf_folder, "084733-01.pdf")},
        ]
    
    def get_available_books(self):
        """获取所有可用的书籍，包含页数信息"""
        books = []
        
        # 首先添加cover文件夹中的书籍（新上传的书籍）
        if os.path.exists(self.cover_folder):
            for filename in os.listdir(self.cover_folder):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    cover_path = os.path.join(self.cover_folder, filename)
                    
                    # 根据封面文件名生成PDF文件名
                    name_without_ext = os.path.splitext(filename)[0]
                    pdf_filename = name_without_ext + '.pdf'
                    pdf_path = os.path.join(self.pdf_folder, pdf_filename)
                    
                    # 检查对应的PDF是否存在
                    if os.path.exists(pdf_path):
                        # 使用文件名作为标题，但移除下划线
                        display_title = name_without_ext.replace('_', ' ')
                        book_info = {
                            "title": display_title,
                            "cover": cover_path,
                            "pdf_path": pdf_filename,  # 只保存文件名，不保存完整路径
                            "pages": self.get_pdf_page_count(pdf_path)
                        }
                        books.append(book_info)
        
        # 然后添加预设书籍（如果文件存在）
        preset_books = self.get_preset_books()
        for book in preset_books:
            # 检查文件是否存在
            cover_exists = os.path.exists(book["cover"])
            pdf_exists = os.path.exists(book["pdf"])
            
            if pdf_exists:  # 只要PDF存在就显示
                book_info = {
                    "title": book["title"],
                    "cover": book["cover"] if cover_exists else None,
                    "pdf_path": book["pdf"],
                    "pages": self.get_pdf_page_count(book["pdf"])
                }
                books.append(book_info)
        
        return books
    
    def get_pdf_page_count(self, pdf_path):
        """获取PDF页数"""
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception:
            return "未知"
    
    def get_all_books(self, uploaded_books=None):
        """获取所有书籍（预设+上传）"""
        books = self.get_preset_books()
        if uploaded_books:
            books.extend(uploaded_books)
        return books
    
    def get_pdf_link(self, pdf_path):
        """生成PDF下载链接"""
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_data = f.read()
            pdf_base64 = base64.b64encode(pdf_data).decode()
            return f"data:application/pdf;base64,{pdf_base64}"
        return None
    
    def load_image(self, image_path):
        """加载图片"""
        try:
            if os.path.exists(image_path):
                return Image.open(image_path)
            else:
                # 返回默认图片或None
                return None
        except Exception as e:
            print(f"加载图片失败: {e}")
            return None 