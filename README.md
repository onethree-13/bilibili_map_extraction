# B站视频信息抓取工具

基于 [bilibili-api](https://nemo2011.github.io/bilibili-api/#/) 开发的B站视频信息抓取工具，现已升级为Streamlit Web应用！

## 🆕 新功能特点

- ✅ **Streamlit Web界面** - 友好的图形化用户界面
- ✅ **根据UID获取用户视频** - 输入B站用户UID获取所有发布视频
- ✅ **可视化视频选择** - 通过勾选框选择需要抓取的视频
- ✅ **详细视频信息抓取** - 获取视频标题、简介、BV号等详细信息
- ✅ **数据导出功能** - 支持CSV和JSON格式导出
- ✅ **模块化架构** - 代码结构更清晰，易于维护

## 🏗️ 项目结构

```
bilibili_map_extraction/
├── app.py                    # Streamlit主应用
├── config.ini               # 配置文件
├── requirements.txt          # 项目依赖
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── config_manager.py    # 配置管理
│   └── bilibili_scraper.py  # B站数据抓取
├── data/                    # 数据输出目录
└── README.md               # 项目说明
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置登录凭据

编辑 `config.ini` 文件，填入您的B站登录凭据：

```ini
[Credential]
# 获取方法：登录B站后按F12打开开发者工具，在Application或Storage中查看Cookie
SESSDATA = 你的SESSDATA值
BILI_JCT = 你的BILI_JCT值
BUVID3 = 你的BUVID3值
DEDEUSERID = 你的DEDEUSERID值

[Settings]
OUTPUT_PATH = ./data/
```

#### 如何获取登录凭据？

1. 登录 [bilibili.com](https://bilibili.com)
2. 按 `F12` 打开开发者工具
3. 在 `Application` 或 `Storage` 标签中找到 `Cookie`
4. 复制以下字段的值：
   - `SESSDATA`
   - `bili_jct` (对应配置中的BILI_JCT)
   - `buvid3` (对应配置中的BUVID3)
   - `DedeUserID` (对应配置中的DEDEUSERID)

### 3. 启动应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址：`http://localhost:8501`

## 📖 使用指南

### 🔧 初始化设置

1. 在侧边栏点击 **"初始化抓取器"** 按钮
2. 系统会验证您的登录凭据

### 👤 获取用户视频

1. 在侧边栏输入目标用户的 **UID**
   - 从用户主页URL获取：`https://space.bilibili.com/3546883777629058` 中的 `3546883777629058`
2. 选择获取视频数量（10-50）
3. 点击 **"获取用户视频"** 按钮

### 📺 选择和抓取视频

1. 在视频列表中勾选需要抓取详细信息的视频
2. 点击 **"获取选中视频详情"** 按钮
3. 查看详细的视频信息

### 💾 保存数据

- 点击 **"保存为CSV"** 导出表格格式数据
- 点击 **"保存为JSON"** 导出JSON格式数据
- 文件会保存到 `data/` 目录

## 📊 数据字段说明

抓取的视频信息包含以下字段：

| 字段 | 说明 |
|------|------|
| bvid | 视频BV号 |
| title | 视频标题 |
| description | 视频简介 |
| dynamic | 动态信息 |
| pubdate_str | 发布时间 |
| duration | 视频时长 |
| view | 播放量 |
| danmaku | 弹幕数 |
| like | 点赞数 |
| coin | 投币数 |
| favorite | 收藏数 |
| share | 分享数 |

## 🛠️ 高级功能

### 评论抓取（保留功能）

```python
from utils import BilibiliScraper, ConfigManager

# 初始化
config_manager = ConfigManager()
scraper = BilibiliScraper(config_manager.get_credential())

# 抓取评论
comments = scraper.get_video_comments("BV1uv411q7Mv", max_pages=5)
scraper.save_to_csv(comments, "comments.csv")
```

### 用户信息获取

```python
# 获取用户基本信息
user_info = scraper.get_user_info(3546883777629058)

# 获取用户视频列表
videos = scraper.get_user_videos(3546883777629058, page_size=30)
```

## 🔧 配置说明

### 字符转义处理

项目已解决配置文件中URL编码字符的问题：

- 使用 `RawConfigParser` 避免 `%` 字符解析错误
- 自动处理URL编码的SESSDATA
- 支持直接复制Cookie值

### 网络配置

如遇网络问题，可以：

1. 增加请求超时时间
2. 使用代理服务器
3. 分批次抓取数据

## 🐛 常见问题

### Q: 初始化抓取器失败？
A: 请检查config.ini中的登录凭据是否正确和完整。

### Q: 获取用户信息失败？
A: 请确认用户UID是否正确，以及该用户是否公开。

### Q: 无法获取视频详情？
A: 可能是网络问题或B站API限制，建议稍后重试。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目仅供学习和研究使用，请遵守相关法律法规和B站用户协议。

## 🔗 相关链接

- [bilibili-api 官方文档](https://nemo2011.github.io/bilibili-api/#/)
- [Streamlit 官方文档](https://docs.streamlit.io/)

---

**注意：本工具仅用于合法的数据收集和分析，请勿用于违法用途。**