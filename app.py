#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频信息抓取工具 - Streamlit应用
"""

import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO

from utils.config_manager import ConfigManager
from utils.bilibili_scraper import BilibiliScraper

# 设置页面配置
st.set_page_config(
    page_title="B站视频信息抓取工具",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)


def fetch_bilibili_image(image_url: str, width: int = 150, caption: str = "",
                         fallback_emoji: str = "🖼️", timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """
    通用的B站图片获取函数

    Args:
        image_url: 图片URL
        width: 显示宽度
        caption: 图片标题
        fallback_emoji: 失败时显示的emoji
        timeout: 请求超时时间

    Returns:
        Tuple[是否成功, 错误信息]
    """
    if not image_url:
        st.info(f"无{caption}")
        st.markdown(f"### {fallback_emoji}")
        return False, "无图片URL"

    try:
        # 处理图片URL
        processed_url = image_url.strip()

        # 确保使用HTTPS协议
        if processed_url.startswith('http://'):
            processed_url = processed_url.replace('http://', 'https://')
        elif not processed_url.startswith('https://'):
            processed_url = 'https:' + \
                processed_url if processed_url.startswith(
                    '//') else processed_url

        # 添加headers避免防盗链
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com/'
        }

        response = requests.get(
            processed_url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            image_bytes = BytesIO(response.content)
            st.image(image_bytes, width=width, caption=caption)
            return True, None
        else:
            error_msg = f"图片加载失败，状态码: {response.status_code}"
            st.error(error_msg)
            st.markdown(f"### {fallback_emoji}")
            return False, error_msg

    except Exception as e:
        error_msg = f"图片加载失败: {str(e)}"
        st.error(error_msg)
        st.info("🎭 图片加载失败，可能是由于B站的防盗链机制")
        st.markdown(f"### {fallback_emoji}")
        return False, error_msg


def init_session_state():
    """初始化session state"""
    if 'scraper' not in st.session_state:
        st.session_state.scraper = None
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = None
    if 'init_status' not in st.session_state:
        st.session_state.init_status = None
    if 'init_message' not in st.session_state:
        st.session_state.init_message = ""
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'videos' not in st.session_state:
        st.session_state.videos = []
    if 'selected_videos' not in st.session_state:
        st.session_state.selected_videos = []
    if 'manual_config' not in st.session_state:
        st.session_state.manual_config = {
            'SESSDATA': '',
            'BILI_JCT': '',
            'BUVID3': '',
            'DEDEUSERID': ''
        }
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'main'  # 'main' 或 'config'
    if 'cached_config' not in st.session_state:
        st.session_state.cached_config = None
    if 'video_selection_state' not in st.session_state:
        st.session_state.video_selection_state = []


def auto_initialize():
    """自动初始化抓取器"""
    if st.session_state.scraper is not None:
        return  # 已经初始化过

    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        st.session_state.config_manager = config_manager

        # 检查是否有有效配置
        if config_manager.has_valid_config():
            credential = config_manager.get_credential()
            if credential:
                # 验证凭据
                is_valid, message = config_manager.validate_credential(
                    credential)
                if is_valid:
                    # 初始化成功
                    scraper = BilibiliScraper(credential)
                    st.session_state.scraper = scraper
                    st.session_state.init_status = "success"
                    st.session_state.init_message = f"✅ 自动初始化成功 - 用户: {message}"
                else:
                    # 凭据无效
                    st.session_state.init_status = "error"
                    st.session_state.init_message = f"❌ 凭据验证失败: {message}"
            else:
                st.session_state.init_status = "error"
                st.session_state.init_message = "❌ 凭据创建失败"
        else:
            # 没有有效配置
            st.session_state.init_status = "config_needed"
            st.session_state.init_message = "⚠️ 需要配置登录凭据"

    except Exception as e:
        st.session_state.init_status = "error"
        st.session_state.init_message = f"❌ 初始化失败: {str(e)}"


def display_init_status():
    """显示初始化状态"""
    if st.session_state.init_status == "success":
        st.success(st.session_state.init_message)
    elif st.session_state.init_status == "error":
        st.error(st.session_state.init_message)
    elif st.session_state.init_status == "config_needed":
        st.warning(st.session_state.init_message)
    else:
        st.info("🔄 等待初始化...")


def config_page():
    """配置管理页面"""

    # 返回按钮
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🔙 返回主页", type="primary"):
            st.session_state.current_page = 'main'
            st.rerun()

    st.markdown("### 🔧 B站登录凭据配置")

    display_init_status()

    # 配置输入表单
    st.markdown("### 📝 输入凭据信息")

    # 获取凭据说明
    with st.expander("📋 **如何获取登录凭据？**", expanded=False):
        st.markdown("""
        ### 步骤说明：
        1. **登录B站** - 访问 [bilibili.com](https://bilibili.com) 并登录您的账号
        2. **打开开发者工具** - 按 `F12` 键或右键选择"检查"
        3. **找到Application标签** - 在开发者工具中点击 `Application` 或 `存储` 标签
        4. **查看Cookie** - 在左侧展开 `Cookies` → `https://www.bilibili.com`
        5. **复制以下字段的值：**
           - `SESSDATA` - 会话标识符（最重要）
           - `bili_jct` - CSRF保护令牌
           - `buvid3` - 浏览器唯一标识
           - `DedeUserID` - 您的用户ID
        
        ### 注意事项：
        - ⚠️ 这些信息非常重要，请妥善保管
        - 🔒 SESSDATA包含您的登录状态，不要泄露给他人
        - 🕐 登录凭据会过期，过期后需要重新获取
        """)

    # 从缓存中加载配置（如果有）
    if st.session_state.cached_config:
        if st.button("📦 使用缓存的配置", type="secondary"):
            st.session_state.manual_config = st.session_state.cached_config.copy()
            st.success("✅ 已加载缓存的配置")
            st.rerun()

    with st.form("credential_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            sessdata = st.text_area(
                "SESSDATA",
                value=st.session_state.manual_config['SESSDATA'],
                height=100,
                help="B站登录会话ID - 从Cookie中复制SESSDATA的值",
                placeholder="粘贴SESSDATA值..."
            )

            buvid3 = st.text_input(
                "BUVID3",
                value=st.session_state.manual_config['BUVID3'],
                help="浏览器标识符 - 从Cookie中复制buvid3的值",
                placeholder="粘贴BUVID3值..."
            )

        with col2:
            bili_jct = st.text_input(
                "BILI_JCT",
                value=st.session_state.manual_config['BILI_JCT'],
                help="B站CSRF令牌 - 从Cookie中复制bili_jct的值",
                placeholder="粘贴BILI_JCT值..."
            )

            dedeuserid = st.text_input(
                "DEDEUSERID",
                value=st.session_state.manual_config['DEDEUSERID'],
                help="用户ID - 从Cookie中复制DedeUserID的值",
                placeholder="粘贴DEDEUSERID值..."
            )

        st.markdown("---")

        # 操作按钮
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            validate_btn = st.form_submit_button("🔍 验证凭据", type="primary")

        with col2:
            save_btn = st.form_submit_button("💾 保存到文件", type="secondary")

        with col3:
            cache_btn = st.form_submit_button("📦 缓存到本地", type="secondary")

        with col4:
            clear_btn = st.form_submit_button("🗑️ 清空表单", type="secondary")

    # 处理表单提交
    if validate_btn or save_btn or cache_btn or clear_btn:
        if clear_btn:
            # 清空表单
            st.session_state.manual_config = {
                'SESSDATA': '',
                'BILI_JCT': '',
                'BUVID3': '',
                'DEDEUSERID': ''
            }
            st.success("🗑️ 表单已清空")
            st.rerun()
        else:
            # 更新session state
            st.session_state.manual_config = {
                'SESSDATA': sessdata.strip(),
                'BILI_JCT': bili_jct.strip(),
                'BUVID3': buvid3.strip(),
                'DEDEUSERID': dedeuserid.strip()
            }

            # 验证凭据
            if all([sessdata.strip(), bili_jct.strip(), buvid3.strip(), dedeuserid.strip()]):
                credential = st.session_state.config_manager.get_credential(
                    st.session_state.manual_config)
                if credential:
                    is_valid, message = st.session_state.config_manager.validate_credential(
                        credential)

                    if is_valid:
                        st.success(f"✅ 凭据验证成功 - 用户: {message}")

                        # 初始化抓取器
                        st.session_state.scraper = BilibiliScraper(credential)
                        st.session_state.init_status = "success"
                        st.session_state.init_message = f"✅ 手动配置成功 - 用户: {message}"

                        # 如果是保存按钮，保存到配置文件
                        if save_btn:
                            if st.session_state.config_manager.save_credential_to_config(st.session_state.manual_config):
                                st.success("💾 配置已保存到config.ini文件")
                            else:
                                st.error("❌ 配置保存失败")

                        # 如果是缓存按钮，缓存到localStorage
                        if cache_btn:
                            st.session_state.cached_config = st.session_state.manual_config.copy()
                            st.success("📦 配置已缓存到本地存储")

                        # 显示成功后的操作提示
                        st.info("🎉 配置成功！您现在可以返回主页使用功能了。")

                    else:
                        st.error(f"❌ 凭据验证失败: {message}")
                        st.info("💡 请检查凭据是否正确，或者尝试重新获取")
                else:
                    st.error("❌ 凭据创建失败，请检查输入格式")
            else:
                st.warning("⚠️ 请填写所有必需的凭据信息")

    st.markdown("---")

    # 配置文件管理
    st.subheader("📂 配置文件管理")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📤 导出配置**")
        st.markdown("将当前配置文件导出为文本，便于备份或在其他设备使用")

        if st.button("📋 导出配置文件", type="secondary", use_container_width=True):
            if st.session_state.config_manager:
                config_content = st.session_state.config_manager.export_config()
                if config_content:
                    st.text_area("配置文件内容", config_content,
                                 height=300, help="请复制此内容进行备份")
                    st.success("✅ 配置已导出，请复制上方内容保存")
                else:
                    st.error("❌ 导出失败，配置文件可能不存在")
            else:
                st.error("❌ 配置管理器未初始化")

    with col2:
        st.markdown("**📥 导入配置**")
        st.markdown("从之前导出的配置文本中恢复配置")

        imported_config = st.text_area(
            "粘贴配置文件内容",
            height=250,
            help="粘贴之前导出的配置内容",
            placeholder="将导出的配置内容粘贴到这里..."
        )

        if st.button("📁 导入并应用配置", type="secondary", use_container_width=True):
            if imported_config.strip():
                if st.session_state.config_manager:
                    if st.session_state.config_manager.import_config(imported_config):
                        st.success("✅ 配置导入成功，正在重新初始化...")
                        # 重新初始化
                        st.session_state.scraper = None
                        st.session_state.init_status = None
                        st.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 配置导入失败，请检查格式是否正确")
                else:
                    st.error("❌ 配置管理器未初始化")
            else:
                st.warning("⚠️ 请输入配置内容")


def get_user_videos(uid: int, months_back: int = 1):
    """获取用户视频"""
    if st.session_state.scraper is None:
        st.error("❌ 请先配置登录凭据")
        return

    with st.spinner("🔍 正在获取用户信息和视频列表..."):
        # 获取用户信息
        user_info = st.session_state.scraper.get_user_info(uid)
        if not user_info:
            st.error("❌ 获取用户信息失败，请检查UID是否正确")
            return

        st.session_state.user_info = user_info

        # 计算时间范围
        now = datetime.now()
        cutoff_date = now - timedelta(days=months_back * 30)  # 简单按30天/月计算
        cutoff_timestamp = cutoff_date.timestamp()

        # 获取足够多的视频，然后过滤
        all_videos = []
        page_num = 1
        should_continue = True

        while len(all_videos) < 500 and page_num <= 20 and should_continue:  # 最多获取500个视频，最多20页
            videos = st.session_state.scraper.get_user_videos(
                uid, page_num=page_num, page_size=50)
            if not videos:
                break

            # 过滤指定时间范围内的视频
            videos_added_this_page = 0
            for video in videos:
                if video.get('created', 0) >= cutoff_timestamp:
                    all_videos.append(video)
                    videos_added_this_page += 1

            # 如果这一页没有添加任何视频，说明后面的视频都太旧了
            if videos_added_this_page == 0:
                should_continue = False

            page_num += 1

        st.session_state.videos = all_videos[:500]  # 最多保留500个

        if st.session_state.videos:
            st.success(
                f"✅ 成功获取最近{months_back}个月内的 {len(st.session_state.videos)} 个视频")
        else:
            st.warning(f"⚠️ 在最近{months_back}个月内未找到视频")


def display_user_info():
    """显示用户信息"""
    if not st.session_state.user_info:
        return

    user = st.session_state.user_info

    st.subheader("👤 用户信息")

    col1, col2 = st.columns([1, 3])

    with col1:
        # 使用通用图片获取函数显示头像
        face_url = user.get('face', '')
        fetch_bilibili_image(
            image_url=face_url,
            width=150,
            caption="用户头像",
            fallback_emoji="👤",
            timeout=10
        )

    with col2:
        st.write(f"**用户名:** {user.get('name', 'N/A')}")
        st.write(f"**UID:** {user.get('uid', 'N/A')}")
        st.write(f"**等级:** LV{user.get('level', 0)}")
        st.write(f"**签名:** {user.get('sign', 'N/A')}")


def display_video_selector():
    """显示视频选择器"""
    if not st.session_state.videos:
        return

    st.subheader("🎥 视频列表")

    # 初始化选择状态
    if len(st.session_state.video_selection_state) != len(st.session_state.videos):
        st.session_state.video_selection_state = [
            False] * len(st.session_state.videos)

    # 添加状态更新计数器，用于强制刷新data_editor
    if 'data_editor_key' not in st.session_state:
        st.session_state.data_editor_key = 0

    # 批量操作控制区域
    st.markdown("🎛️ 批量操作", help="选择要抓取的视频")

    # 第一行：全选和反选按钮
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("✅ 全选", use_container_width=True, key="select_all"):
            st.session_state.video_selection_state = [
                True] * len(st.session_state.videos)
            st.session_state.data_editor_key += 1
            st.rerun()

    with col2:
        if st.button("🔄 反选", use_container_width=True, key="invert_selection"):
            st.session_state.video_selection_state = [
                not x for x in st.session_state.video_selection_state]
            st.session_state.data_editor_key += 1
            st.rerun()

    with col3:
        if st.button("❌ 清空选择", use_container_width=True, key="clear_selection"):
            st.session_state.video_selection_state = [
                False] * len(st.session_state.videos)
            st.session_state.data_editor_key += 1
            st.rerun()

    # 第二行：关键词选择
    st.markdown("🔍 关键词选择", help="选择要抓取的视频")

    # 标题关键词搜索
    st.markdown("**📝 标题关键词搜索**")
    col1, col2 = st.columns([3, 1])

    with col1:
        title_keywords_input = st.text_input(
            "输入标题关键词",
            placeholder="输入关键词，用空格或逗号分隔，例如：游戏 攻略 教程",
            help="在视频标题中搜索包含这些关键词的视频",
            key="title_keywords_input"
        )

    with col2:
        title_search_mode = st.radio(
            "标题搜索模式",
            ["包含任意", "包含全部"],
            help="包含任意：只要包含其中一个关键词即可\n包含全部：必须包含所有关键词",
            key="title_search_mode"
        )

    # 标题关键词操作处理
    if title_keywords_input.strip():
        # 解析关键词
        title_keywords = []
        if ',' in title_keywords_input:
            title_keywords = [kw.strip() for kw in title_keywords_input.split(',') if kw.strip()]
        else:
            title_keywords = [kw.strip() for kw in title_keywords_input.split() if kw.strip()]

        if title_keywords:
            # 标题关键词操作按钮
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"🔍 选择标题包含关键词的视频", use_container_width=True, key="select_title_keywords"):
                    for i, video in enumerate(st.session_state.videos):
                        title = video.get('title', '').lower()
                        if title_search_mode == "包含任意":
                            if any(kw.lower() in title for kw in title_keywords):
                                st.session_state.video_selection_state[i] = True
                        else:
                            if all(kw.lower() in title for kw in title_keywords):
                                st.session_state.video_selection_state[i] = True
                    st.session_state.data_editor_key += 1
                    st.rerun()

            with col2:
                if st.button(f"🚫 反选标题包含关键词的视频", use_container_width=True, key="invert_title_keywords"):
                    for i, video in enumerate(st.session_state.videos):
                        title = video.get('title', '').lower()
                        if title_search_mode == "包含任意":
                            if any(kw.lower() in title for kw in title_keywords):
                                st.session_state.video_selection_state[i] = not st.session_state.video_selection_state[i]
                        else:
                            if all(kw.lower() in title for kw in title_keywords):
                                st.session_state.video_selection_state[i] = not st.session_state.video_selection_state[i]
                    st.session_state.data_editor_key += 1
                    st.rerun()

            with col3:
                if st.button(f"🎯 仅选择标题关键词视频", use_container_width=True, key="only_title_keywords"):
                    new_selection = [False] * len(st.session_state.videos)
                    for i, video in enumerate(st.session_state.videos):
                        title = video.get('title', '').lower()
                        if title_search_mode == "包含任意":
                            if any(kw.lower() in title for kw in title_keywords):
                                new_selection[i] = True
                        else:
                            if all(kw.lower() in title for kw in title_keywords):
                                new_selection[i] = True
                    st.session_state.video_selection_state = new_selection
                    st.session_state.data_editor_key += 1
                    st.rerun()

            # 显示标题匹配的视频数量
            title_matched_count = 0
            for i, video in enumerate(st.session_state.videos):
                title = video.get('title', '').lower()
                if title_search_mode == "包含任意":
                    if any(kw.lower() in title for kw in title_keywords):
                        title_matched_count += 1
                else:
                    if all(kw.lower() in title for kw in title_keywords):
                        title_matched_count += 1

            st.info(f"🎯 找到 {title_matched_count} 个标题包含关键词 {title_keywords} 的视频（{title_search_mode}）")

    # 简介关键词搜索
    st.markdown("**📄 简介关键词搜索**")
    col1, col2 = st.columns([3, 1])

    with col1:
        desc_keywords_input = st.text_input(
            "输入简介关键词",
            placeholder="输入关键词，用空格或逗号分隔，例如：解说 评测 分析",
            help="在视频简介中搜索包含这些关键词的视频",
            key="desc_keywords_input"
        )

    with col2:
        desc_search_mode = st.radio(
            "简介搜索模式",
            ["包含任意", "包含全部"],
            help="包含任意：只要包含其中一个关键词即可\n包含全部：必须包含所有关键词",
            key="desc_search_mode"
        )

    # 简介关键词操作处理
    if desc_keywords_input.strip():
        # 解析关键词
        desc_keywords = []
        if ',' in desc_keywords_input:
            desc_keywords = [kw.strip() for kw in desc_keywords_input.split(',') if kw.strip()]
        else:
            desc_keywords = [kw.strip() for kw in desc_keywords_input.split() if kw.strip()]

        if desc_keywords:
            # 简介关键词操作按钮
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"🔍 选择简介包含关键词的视频", use_container_width=True, key="select_desc_keywords"):
                    for i, video in enumerate(st.session_state.videos):
                        description = video.get('description', '').lower()
                        if desc_search_mode == "包含任意":
                            if any(kw.lower() in description for kw in desc_keywords):
                                st.session_state.video_selection_state[i] = True
                        else:
                            if all(kw.lower() in description for kw in desc_keywords):
                                st.session_state.video_selection_state[i] = True
                    st.session_state.data_editor_key += 1
                    st.rerun()

            with col2:
                if st.button(f"🚫 反选简介包含关键词的视频", use_container_width=True, key="invert_desc_keywords"):
                    for i, video in enumerate(st.session_state.videos):
                        description = video.get('description', '').lower()
                        if desc_search_mode == "包含任意":
                            if any(kw.lower() in description for kw in desc_keywords):
                                st.session_state.video_selection_state[i] = not st.session_state.video_selection_state[i]
                        else:
                            if all(kw.lower() in description for kw in desc_keywords):
                                st.session_state.video_selection_state[i] = not st.session_state.video_selection_state[i]
                    st.session_state.data_editor_key += 1
                    st.rerun()

            with col3:
                if st.button(f"🎯 仅选择简介关键词视频", use_container_width=True, key="only_desc_keywords"):
                    new_selection = [False] * len(st.session_state.videos)
                    for i, video in enumerate(st.session_state.videos):
                        description = video.get('description', '').lower()
                        if desc_search_mode == "包含任意":
                            if any(kw.lower() in description for kw in desc_keywords):
                                new_selection[i] = True
                        else:
                            if all(kw.lower() in description for kw in desc_keywords):
                                new_selection[i] = True
                    st.session_state.video_selection_state = new_selection
                    st.session_state.data_editor_key += 1
                    st.rerun()

            # 显示简介匹配的视频数量
            desc_matched_count = 0
            for i, video in enumerate(st.session_state.videos):
                description = video.get('description', '').lower()
                if desc_search_mode == "包含任意":
                    if any(kw.lower() in description for kw in desc_keywords):
                        desc_matched_count += 1
                else:
                    if all(kw.lower() in description for kw in desc_keywords):
                        desc_matched_count += 1

            st.info(f"🎯 找到 {desc_matched_count} 个简介包含关键词 {desc_keywords} 的视频（{desc_search_mode}）")

    # 创建DataFrame用于显示
    df = pd.DataFrame(st.session_state.videos)

    # 添加选择列，使用session state中的状态
    df['选择'] = st.session_state.video_selection_state

    # 重新排列列顺序
    columns = ['选择', 'title', 'bvid', 'description', 'created_str']

    # 显示可编辑的数据表格，使用动态key确保状态更新
    edited_df = st.data_editor(
        df[columns],
        column_config={
            "选择": st.column_config.CheckboxColumn(
                "选择",
                help="选择要抓取详细信息的视频",
                default=False,
            ),
            "title": st.column_config.TextColumn(
                "标题",
                help="视频标题",
                max_chars=50,
            ),
            "description": st.column_config.TextColumn(
                "简介",
                help="视频简介",
                max_chars=100,
            ),
            "bvid": st.column_config.TextColumn(
                "BV号",
                help="视频BV号",
            ),
            "created_str": st.column_config.TextColumn(
                "发布时间",
                help="视频发布时间",
            ),
        },
        hide_index=True,
        use_container_width=True,
        height=400,
        key=f"video_data_editor_{st.session_state.data_editor_key}"
    )

    # 检查用户是否手动更改了选择状态
    new_selection_state = edited_df['选择'].tolist()
    if new_selection_state != st.session_state.video_selection_state:
        # 用户手动更改了选择，更新状态
        st.session_state.video_selection_state = new_selection_state

    # 获取选中的视频
    selected_indices = [i for i, selected in enumerate(
        st.session_state.video_selection_state) if selected]
    selected_videos = [st.session_state.videos[i] for i in selected_indices]
    st.session_state.selected_videos = selected_videos

    # 显示选择统计
    st.info(
        f"📊 已选择 {len(selected_videos)} / {len(st.session_state.videos)} 个视频")

    return selected_videos


def get_selected_video_details():
    """获取选中视频的基本信息"""
    if not st.session_state.selected_videos:
        st.warning("⚠️ 请先选择要抓取的视频")
        return None

    detailed_videos = []

    with st.spinner("📋 正在整理选中视频信息..."):
        for video in st.session_state.selected_videos:
            # 直接从现有视频数据中提取基本信息
            video_info = {
                'bvid': video.get('bvid', ''),
                'title': video.get('title', ''),
                'description': video.get('description', ''),
                'pic': video.get('pic', ''),
                'created_str': video.get('created_str', ''),
                'duration': video.get('length', ''),  # 使用length字段作为duration
            }
            detailed_videos.append(video_info)

    st.success(f"✅ 成功整理 {len(detailed_videos)} 个视频的基本信息")
    return detailed_videos


def display_video_details(detailed_videos: List[Dict[str, Any]]):
    """显示视频基本信息"""
    if not detailed_videos:
        return

    st.subheader("📋 视频基本信息")

    for i, video in enumerate(detailed_videos):
        with st.expander(f"📺 {video['title']}", expanded=True):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**BV号:** {video['bvid']}")
                st.write(f"**标题:** {video['title']}")
                if video.get('description'):
                    st.write(
                        f"**简介:** {video['description'][:200]}{'...' if len(video['description']) > 200 else ''}")
                st.write(f"**发布时间:** {video['created_str']}")
                if video.get('duration'):
                    st.write(f"**时长:** {video['duration']}")

            with col2:
                # 使用通用图片获取函数显示视频封面
                pic_url = video.get('pic', '')
                fetch_bilibili_image(
                    image_url=pic_url,
                    width=200,
                    caption="视频封面",
                    fallback_emoji="🎬",
                    timeout=10
                )


def save_video_data(detailed_videos: List[Dict[str, Any]]):
    """保存视频数据"""
    if not detailed_videos:
        st.warning("⚠️ 没有数据可保存")
        return

    st.subheader("📥 下载数据")

    # 准备文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"videos_{st.session_state.user_info['name']}_{timestamp}.json"

    # 准备JSON数据
    json_data = st.session_state.scraper.prepare_json_download(detailed_videos)

    # 显示下载按钮
    st.download_button(
        label="📝 下载 JSON 文件",
        data=json_data,
        file_name=filename,
        mime="application/json",
        type="primary",
        use_container_width=True
    )

    # 显示数据统计
    st.info(f"📊 共 {len(detailed_videos)} 个视频的详细信息将被下载")


def main_page():
    """主页面"""
    st.title("🎬 B站视频信息抓取工具")
    st.markdown("---")

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 控制面板")

        # 显示初始化状态
        st.subheader("🔄 状态")
        display_init_status()

        # 配置管理按钮
        if st.button("⚙️ 配置管理", type="secondary", use_container_width=True):
            st.session_state.current_page = 'config'
            st.rerun()

        st.markdown("---")

        # 如果需要配置，显示提示
        if st.session_state.init_status in ["config_needed", "error"]:
            st.warning("⚠️ 请点击上方'配置管理'按钮进行配置")

        # 视频获取控制
        if st.session_state.init_status == "success":
            st.subheader("📺 视频获取")

            # 输入用户UID
            uid = st.number_input(
                "👤 输入B站用户UID",
                min_value=1,
                value=3546883777629058,  # 默认值
                help="从用户主页URL中获取UID，例如：https://space.bilibili.com/3546883777629058"
            )

            # 时间范围选择
            time_options = {
                "最近1个月": 1,
                "最近3个月": 3,
                "最近6个月": 6,
                "最近12个月": 12
            }

            selected_time = st.selectbox(
                "📅 选择时间范围",
                options=list(time_options.keys()),
                index=0,  # 默认选择"最近1个月"
                help="选择要获取视频的时间范围"
            )

            months_back = time_options[selected_time]

            if st.button("🔍 获取用户视频", type="primary"):
                get_user_videos(uid, months_back)

        st.markdown("---")
        st.markdown("### 📖 使用说明")
        st.markdown("""
        1. 点击"配置管理"进行初始化设置
        2. 输入目标用户的UID
        3. 选择要获取视频的时间范围
        4. 点击"获取用户视频"加载视频列表
        5. 在视频列表中勾选需要的视频
        6. 点击"整理选中视频信息"获取详细信息
        7. 下载JSON文件保存数据
        """)

    # 主内容区域
    if st.session_state.init_status == "success":
        # 显示用户信息
        display_user_info()

        if st.session_state.videos:
            st.markdown("---")

            # 显示视频选择器
            selected_videos = display_video_selector()

            if selected_videos:
                if st.button("📋 整理选中视频信息", type="primary"):
                    detailed_videos = get_selected_video_details()
                    if detailed_videos:
                        st.session_state.detailed_videos = detailed_videos

                # 显示详细信息
                if 'detailed_videos' in st.session_state:
                    st.markdown("---")
                    display_video_details(st.session_state.detailed_videos)

                    st.markdown("---")
                    save_video_data(st.session_state.detailed_videos)
    else:
        # 显示配置引导
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info("🔧 请点击侧边栏的'配置管理'按钮进行登录凭据配置")
            st.markdown("### 🚀 快速开始")
            st.markdown("""
            1. **点击配置管理** - 在侧边栏找到"配置管理"按钮
            2. **获取登录凭据** - 按照页面指引从B站获取Cookie信息
            3. **验证配置** - 输入凭据并验证有效性
            4. **开始使用** - 返回主页开始抓取视频信息
            """)


def main():
    """主函数"""
    # 初始化
    init_session_state()

    # 自动初始化
    auto_initialize()

    # 根据当前页面状态显示不同页面
    if st.session_state.current_page == 'config':
        config_page()
    else:
        main_page()


if __name__ == "__main__":
    main()
