# Lumina

教会礼拜 PPT 自动生成工具。离线优先的跨平台桌面应用（Electron + React + TypeScript 前端，Python FastAPI + python-pptx 后端），通过「固定流程模板 + 圣经/赞美诗内容库 + 自动排版生成」快速产出一份排版规范、风格统一的礼拜 PowerPoint 文件。

详细需求见 [REQUIREMENTS.md](REQUIREMENTS.md)。

## 仓库结构

```
lumina/
  backend/    # Python FastAPI 后端 + python-pptx 生成引擎
  frontend/   # Electron + React + TS 桌面前端
  REQUIREMENTS.md
```

## 一阶段范围

已实现的核心闭环：从默认流程模板新建工程 → 填写启应/证道经文（圣经引用自动生成）→ 导出 `.pptx`。

## 开发

### 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 导入圣经（和合本）数据，生成 app/data/bible.sqlite
python -m app.data.import_bible

# 启动开发服务
python -m app.main            # 或 uvicorn app.main:app --reload
```

后端默认监听 `127.0.0.1` 上的空闲端口（仅本地回环）。开发时可通过环境变量 `LUMINA_PORT` 固定端口，`LUMINA_HOST` 固定主机。

### 前端

```bash
cd frontend
npm install
npm run dev            # 启动 Vite + Electron 开发环境
```

## 圣经数据

和合本（CUV，1919）为公有领域文本。`backend/app/data/import_bible.py` 负责从公开数据源获取并导入 SQLite（`bible.sqlite` 不入库，由脚本本地生成）。详见脚本内说明。

## 后续阶段

- 阶段二：赞美诗库 / 礼文库 / 视觉主题 / 流程模板管理 / 样式面板 / 近似预览 / 音频（按单击顺序播放）。
- 阶段三：视频、高保真预览、自动保存与崩溃恢复、双平台打包发布。
