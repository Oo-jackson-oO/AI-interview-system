import os
import base64
from PIL import Image

class SkillManager:
    def __init__(self):
        self.books_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "modules", "book")
        self.ensure_book_folder()
        
    def ensure_book_folder(self):
        """确保书籍文件夹存在"""
        if not os.path.exists(self.books_folder):
            os.makedirs(self.books_folder)
    
    def save_uploaded_book(self, cover_file, pdf_file):
        """保存上传的书籍文件"""
        cover_path = os.path.join(self.books_folder, cover_file.name)
        pdf_path = os.path.join(self.books_folder, pdf_file.name)

        with open(cover_path, "wb") as f:
            f.write(cover_file.read())

        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())

        return {
            "title": pdf_file.name.split(".")[0], 
            "cover": cover_path, 
            "pdf": pdf_path
        }
    
    def get_preset_books(self):
        """获取预设书籍列表"""
        return [
            {"title": "军事理论", "cover": "book/军事理论.png", "pdf": "book/084733-01.pdf"},
            {"title": "数据管理分析", "cover": "book/数据管理.png", "pdf": "book/084733-01.pdf"},
            {"title": "操作系统原理", "cover": "book/f0549ae0dbadb44431d7931c4f6db31.png", "pdf": "book/084733-01.pdf"},
            {"title": "计算机网络", "cover": "book/e0928b4989ad49c1ab22a656927f2df.png", "pdf": "book/084733-01.pdf"},
            {"title": "deepseek", "cover": "book/deepseek.png", "pdf": "book/084733-01.pdf"},
        ]
    
    def get_available_books(self):
        """获取所有可用的书籍，包含页数信息"""
        books = []
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
        
        # 扫描book文件夹中的其他PDF文件
        if os.path.exists(self.books_folder):
            for filename in os.listdir(self.books_folder):
                if filename.lower().endswith('.pdf'):
                    pdf_path = os.path.join(self.books_folder, filename)
                    # 检查是否已经在预设列表中
                    if not any(book["pdf"] == pdf_path for book in preset_books):
                        # 查找对应的封面图片
                        cover_path = None
                        name_without_ext = os.path.splitext(filename)[0]
                        for ext in ['.png', '.jpg', '.jpeg']:
                            potential_cover = os.path.join(self.books_folder, name_without_ext + ext)
                            if os.path.exists(potential_cover):
                                cover_path = potential_cover
                                break
                        
                        book_info = {
                            "title": name_without_ext,
                            "cover": cover_path,
                            "pdf_path": pdf_path,
                            "pages": self.get_pdf_page_count(pdf_path)
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