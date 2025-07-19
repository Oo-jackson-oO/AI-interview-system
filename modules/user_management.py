import json
import os
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional

class UserManager:
    def __init__(self, data_file: str = 'user_data.json'):
        self.data_file = data_file
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_users(self):
        """保存用户数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str, email: str = "") -> Dict:
        """注册新用户"""
        if username in self.users:
            return {"success": False, "message": "用户名已存在"}
        
        if len(password) < 6:
            return {"success": False, "message": "密码长度至少6位"}
        
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "username": username,
            "password_hash": self._hash_password(password),
            "email": email,
            "name": "",  # 姓名
            "major": "",  # 学科
            "university": "",  # 大学
            "created_at": datetime.now().isoformat(),
            "resumes": [],  # 用户简历列表
            "last_login": None
        }
        
        self.users[username] = user_data
        self._save_users()
        
        return {"success": True, "message": "注册成功", "user_id": user_id}
    
    def login_user(self, username: str, password: str) -> Dict:
        """用户登录"""
        if username not in self.users:
            return {"success": False, "message": "用户名不存在"}
        
        user = self.users[username]
        if user["password_hash"] != self._hash_password(password):
            return {"success": False, "message": "密码错误"}
        
        # 更新最后登录时间
        user["last_login"] = datetime.now().isoformat()
        self._save_users()
        
        return {
            "success": True, 
            "message": "登录成功",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        }
    
    def get_user(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        return self.users.get(username)
    
    def add_resume(self, username: str, resume_data: Dict) -> Dict:
        """添加简历到用户数据"""
        if username not in self.users:
            return {"success": False, "message": "用户不存在"}
        
        resume_id = str(uuid.uuid4())
        resume_data["id"] = resume_id
        resume_data["created_at"] = datetime.now().isoformat()
        
        # 如果resume_data中没有file_path，则添加默认路径
        if "file_path" not in resume_data:
            safe_username = "".join(c for c in username if c.isalnum() or c in ('-', '_')).rstrip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_username}_resume_{timestamp}.txt"
            resume_data["file_path"] = f"resumes/{filename}"
        
        self.users[username]["resumes"].append(resume_data)
        self._save_users()
        
        return {"success": True, "message": "简历保存成功", "resume_id": resume_id}
    
    def get_user_resumes(self, username: str) -> List[Dict]:
        """获取用户的所有简历"""
        if username not in self.users:
            return []
        return self.users[username].get("resumes", [])
    
    def get_resume(self, username: str, resume_id: str) -> Optional[Dict]:
        """获取特定简历"""
        resumes = self.get_user_resumes(username)
        for resume in resumes:
            if resume["id"] == resume_id:
                return resume
        return None
    
    def delete_resume(self, username: str, resume_id: str) -> Dict:
        """删除简历"""
        if username not in self.users:
            return {"success": False, "message": "用户不存在"}
        
        resumes = self.users[username]["resumes"]
        for i, resume in enumerate(resumes):
            if resume["id"] == resume_id:
                # 删除文件
                file_path = resume.get("file_path")
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"删除文件失败: {str(e)}")
                
                del resumes[i]
                self._save_users()
                return {"success": True, "message": "简历删除成功"}
        
        return {"success": False, "message": "简历不存在"}
    
    def update_user_profile(self, username: str, profile_data: Dict) -> Dict:
        """更新用户个人信息"""
        if username not in self.users:
            return {"success": False, "message": "用户不存在"}
        
        user = self.users[username]
        
        # 更新个人信息字段
        if "name" in profile_data:
            user["name"] = profile_data["name"]
        if "major" in profile_data:
            user["major"] = profile_data["major"]
        if "university" in profile_data:
            user["university"] = profile_data["university"]
        if "email" in profile_data:
            user["email"] = profile_data["email"]
        
        self._save_users()
        
        return {"success": True, "message": "个人信息更新成功"}
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """获取用户个人信息"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "name": user.get("name", ""),
            "major": user.get("major", ""),
            "university": user.get("university", ""),
            "created_at": user["created_at"],
            "last_login": user.get("last_login")
        } 