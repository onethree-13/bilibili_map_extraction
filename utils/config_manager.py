#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import configparser
import os
import sys
import urllib.parse
from typing import Dict, Any, Optional, Tuple
from bilibili_api import Credential, user, sync

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.ini"):
        """初始化配置管理器
        
        Args:
            config_path (str): 配置文件路径
        """
        self.config_path = config_path
        self.config = None
        self.credential = None
        self._load_config_safe()
        
    def _load_config_safe(self) -> None:
        """安全加载配置文件，如果文件不存在则创建默认配置"""
        try:
            if os.path.exists(self.config_path):
                self.config = self.load_config()
            else:
                self.create_default_config()
                self.config = self.load_config()
        except Exception as e:
            print(f"⚠️ 配置文件加载失败: {e}")
            self.config = None
        
    def load_config(self) -> configparser.RawConfigParser:
        """加载配置文件
        
        Returns:
            configparser.RawConfigParser: 配置对象
        """
        # 使用RawConfigParser避免%字符的插值问题
        config = configparser.RawConfigParser()
        config.read(self.config_path, encoding='utf-8')
        return config
    
    def create_default_config(self) -> None:
        """创建默认配置文件"""
        config = configparser.RawConfigParser()
        
        # 添加凭据部分
        config.add_section('Credential')
        config.set('Credential', '# 获取方法：登录B站后按F12打开开发者工具，在Application或Storage中查看Cookie')
        config.set('Credential', '# 注意：SESSDATA中的URL编码字符（如%2C等）可以直接复制，程序会自动处理')
        config.set('Credential', 'SESSDATA', '你的SESSDATA值')
        config.set('Credential', 'BILI_JCT', '你的BILI_JCT值')
        config.set('Credential', 'BUVID3', '你的BUVID3值')
        config.set('Credential', 'DEDEUSERID', '你的DEDEUSERID值')
        
        # 保存到文件
        with open(self.config_path, 'w', encoding='utf-8') as f:
            config.write(f)
    
    def has_valid_config(self) -> bool:
        """检查是否有有效的配置"""
        if not self.config:
            return False
            
        try:
            sessdata = self.config.get('Credential', 'SESSDATA', fallback='')
            bili_jct = self.config.get('Credential', 'BILI_JCT', fallback='')
            buvid3 = self.config.get('Credential', 'BUVID3', fallback='')
            dedeuserid = self.config.get('Credential', 'DEDEUSERID', fallback='')
            
            # 检查是否为默认值或空值
            if any(val.startswith('你的') or not val.strip() for val in [sessdata, bili_jct, buvid3, dedeuserid]):
                return False
                
            return True
        except Exception:
            return False
    
    def get_credential(self, manual_config: Optional[Dict[str, str]] = None) -> Optional[Credential]:
        """获取用户凭据
        
        Args:
            manual_config: 手动配置的凭据信息
            
        Returns:
            Credential: 用户凭据对象，如果失败返回None
        """
        try:
            if manual_config:
                # 使用手动配置
                sessdata_raw = manual_config.get('SESSDATA', '')
                bili_jct_raw = manual_config.get('BILI_JCT', '')
                buvid3_raw = manual_config.get('BUVID3', '')
                dedeuserid_raw = manual_config.get('DEDEUSERID', '')
            else:
                # 从配置文件读取
                if not self.config:
                    return None
                    
                sessdata_raw = self.config.get('Credential', 'SESSDATA', fallback='')
                bili_jct_raw = self.config.get('Credential', 'BILI_JCT', fallback='')
                buvid3_raw = self.config.get('Credential', 'BUVID3', fallback='')
                dedeuserid_raw = self.config.get('Credential', 'DEDEUSERID', fallback='')
            
            # 检查是否为默认值或空值
            if any(val.startswith('你的') or not val.strip() for val in [sessdata_raw, bili_jct_raw, buvid3_raw, dedeuserid_raw]):
                return None
            
            # 对SESSDATA进行URL解码（如果包含URL编码字符）
            sessdata = urllib.parse.unquote(sessdata_raw) if '%' in sessdata_raw else sessdata_raw
            
            credential = Credential(
                sessdata=sessdata,
                bili_jct=bili_jct_raw,
                buvid3=buvid3_raw,
                dedeuserid=dedeuserid_raw
            )
            
            return credential
                
        except Exception as e:
            print(f"❌ 用户凭据设置失败: {e}")
            return None
    
    def validate_credential(self, credential: Credential) -> Tuple[bool, str]:
        """验证登录凭据是否有效
        
        Args:
            credential: 登录凭据
            
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息或用户名)
        """
        try:
            # 尝试获取用户信息来验证凭据
            test_user = user.User(uid=int(credential.dedeuserid), credential=credential)
            user_info = sync(test_user.get_user_info())
            
            if user_info and user_info.get('name'):
                return True, user_info.get('name', '验证成功')
            else:
                return False, "无法获取用户信息"
                
        except Exception as e:
            return False, f"验证失败: {str(e)}"
    
    def save_credential_to_config(self, credential_data: Dict[str, str]) -> bool:
        """保存凭据到配置文件
        
        Args:
            credential_data: 凭据数据字典
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if not self.config:
                self.create_default_config()
                self.config = self.load_config()
            
            # 更新凭据信息
            for key, value in credential_data.items():
                if key in ['SESSDATA', 'BILI_JCT', 'BUVID3', 'DEDEUSERID']:
                    self.config.set('Credential', key, value)
            
            # 保存到文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
                
            return True
            
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
            return False
    
    def export_config(self) -> Optional[str]:
        """导出配置为字符串
        
        Returns:
            str: 配置文件内容，失败返回None
        """
        try:
            if not self.config:
                return None
                
            # 读取配置文件内容
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            print(f"❌ 导出配置失败: {e}")
            return None
    
    def import_config(self, config_content: str) -> bool:
        """导入配置内容
        
        Args:
            config_content: 配置文件内容
            
        Returns:
            bool: 是否导入成功
        """
        try:
            # 写入配置文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            # 重新加载配置
            self.config = self.load_config()
            return True
            
        except Exception as e:
            print(f"❌ 导入配置失败: {e}")
            return False 