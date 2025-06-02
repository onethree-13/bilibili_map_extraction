#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站数据抓取模块
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from bilibili_api import comment, video, user, sync
from bilibili_api.comment import CommentResourceType, OrderType
from bilibili_api import Credential
from tqdm import tqdm

class BilibiliScraper:
    """B站数据抓取器"""
    
    def __init__(self, credential: Credential):
        """初始化抓取器
        
        Args:
            credential (Credential): 用户凭据
        """
        self.credential = credential
        
    def get_user_videos(self, uid: int, page_num: int = 1, page_size: int = 30) -> List[Dict[str, Any]]:
        """获取用户发布的视频列表
        
        Args:
            uid (int): 用户ID
            page_num (int): 页码，从1开始
            page_size (int): 每页视频数量，最大50
            
        Returns:
            List[Dict[str, Any]]: 视频信息列表
        """
        try:
            user_obj = user.User(uid=uid, credential=self.credential)
            
            # 获取用户视频
            videos_data = sync(user_obj.get_videos(pn=page_num, ps=page_size))
            
            videos = []
            for video_info in videos_data.get('list', {}).get('vlist', []):
                videos.append({
                    'bvid': video_info.get('bvid', ''),
                    'aid': video_info.get('aid', 0),
                    'title': video_info.get('title', ''),
                    'description': video_info.get('description', ''),
                    'pic': video_info.get('pic', ''),
                    'created': video_info.get('created', 0),
                    'created_str': datetime.fromtimestamp(video_info.get('created', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                    'length': video_info.get('length', ''),
                    'play': video_info.get('play', 0),
                    'video_review': video_info.get('video_review', 0),
                    'favorites': video_info.get('favorites', 0),
                })
                
            return videos
            
        except Exception as e:
            print(f"❌ 获取用户视频失败: {e}")
            return []
    
    def get_user_info(self, uid: int) -> Dict[str, Any]:
        """获取用户基本信息
        
        Args:
            uid (int): 用户ID
            
        Returns:
            Dict[str, Any]: 用户信息
        """
        try:
            user_obj = user.User(uid=uid, credential=self.credential)
            user_info = sync(user_obj.get_user_info())
            
            return {
                'uid': uid,
                'name': user_info.get('name', ''),
                'face': user_info.get('face', ''),
                'sign': user_info.get('sign', ''),
                'level': user_info.get('level', 0),
                'sex': user_info.get('sex', ''),
            }
            
        except Exception as e:
            print(f"❌ 获取用户信息失败: {e}")
            return {}
    
    def get_video_detail(self, bvid: str) -> Dict[str, Any]:
        """获取视频详细信息
        
        Args:
            bvid (str): 视频BV号
            
        Returns:
            Dict[str, Any]: 视频详细信息
        """
        try:
            video_obj = video.Video(bvid=bvid, credential=self.credential)
            video_info = sync(video_obj.get_info())
            
            return {
                'bvid': bvid,
                'aid': video_info.get('aid', 0),
                'title': video_info.get('title', ''),
                'desc': video_info.get('desc', ''),
                'pic': video_info.get('pic', ''),
                'pubdate': video_info.get('pubdate', 0),
                'pubdate_str': datetime.fromtimestamp(video_info.get('pubdate', 0)).strftime('%Y-%m-%d %H:%M:%S'),
                'duration': video_info.get('duration', 0),
                'owner': video_info.get('owner', {}),
                'stat': video_info.get('stat', {}),
                'dynamic': video_info.get('dynamic', ''),
                'pages': video_info.get('pages', []),
            }
            
        except Exception as e:
            print(f"❌ 获取视频详情失败: {e}")
            return {}
    
    def get_video_comments(self, bvid: str, max_pages: int = 50) -> List[Dict[str, Any]]:
        """获取视频评论（保留原有功能）
        
        Args:
            bvid (str): 视频BV号
            max_pages (int): 最大页数
            
        Returns:
            List[Dict[str, Any]]: 评论数据列表
        """
        try:
            video_obj = video.Video(bvid=bvid, credential=self.credential)
            video_info = sync(video_obj.get_info())
            
            all_comments = []
            page_index = 1
            oid = video_info['aid']
            
            print(f"🚀 开始抓取评论，最大页数: {max_pages}")
            
            with tqdm(desc="抓取评论", unit="页") as pbar:
                while page_index <= max_pages:
                    try:
                        # 获取当前页评论
                        comments_data = sync(
                            comment.get_comments(
                                oid=oid,
                                type_=CommentResourceType.VIDEO,
                                page_index=page_index,
                                order=OrderType.TIME,
                                credential=self.credential,
                            )
                        )
                        
                        # 检查是否还有评论
                        replies = comments_data.get('replies', [])
                        if not replies:
                            print(f"\n📄 第{page_index}页无评论，停止抓取")
                            break
                        
                        # 处理评论数据
                        for reply in replies:
                            comment_info = self._parse_comment(reply)
                            if comment_info:  # 只添加成功解析的评论
                                all_comments.append(comment_info)
                        
                        pbar.set_postfix({
                            '页数': page_index,
                            '评论数': len(all_comments)
                        })
                        pbar.update(1)
                        
                        page_index += 1
                        
                        # 避免请求过于频繁
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"\n❌ 第{page_index}页抓取失败: {e}")
                        break
            
            print(f"✅ 评论抓取完成，共获取 {len(all_comments)} 条评论")
            return all_comments
            
        except Exception as e:
            print(f"❌ 视频评论抓取失败: {e}")
            return []
    
    def _parse_comment(self, reply: Dict[str, Any]) -> Dict[str, Any]:
        """解析单条评论
        
        Args:
            reply (Dict[str, Any]): 原始评论数据
            
        Returns:
            Dict[str, Any]: 解析后的评论数据
        """
        try:
            member = reply.get('member', {})
            content = reply.get('content', {})
            
            return {
                'rpid': reply.get('rpid', ''),  # 评论ID
                'username': member.get('uname', ''),  # 用户名
                'uid': member.get('mid', ''),  # 用户ID
                'level': member.get('level_info', {}).get('current_level', 0),  # 用户等级
                'sex': member.get('sex', ''),  # 性别
                'content': content.get('message', ''),  # 评论内容
                'like_count': reply.get('like', 0),  # 点赞数
                'reply_count': reply.get('rcount', 0),  # 回复数
                'ctime': reply.get('ctime', 0),  # 评论时间戳
                'time_str': datetime.fromtimestamp(reply.get('ctime', 0)).strftime('%Y-%m-%d %H:%M:%S'),  # 格式化时间
                'location': reply.get('reply_control', {}).get('location', ''),  # IP地址
                'device': member.get('official_verify', {}).get('desc', ''),  # 设备信息
            }
        except Exception as e:
            print(f"⚠️ 评论解析失败: {e}")
            return {}
    
    def prepare_json_download(self, data: List[Dict[str, Any]]) -> str:
        """准备JSON数据供浏览器下载
        
        Args:
            data (List[Dict[str, Any]]): 数据
            
        Returns:
            str: JSON字符串
        """
        if not data:
            return "{}"
        
        try:
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ JSON数据准备失败: {e}")
            return "{}" 