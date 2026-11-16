# 投票单智能识别与计票辅助系统

这是一个基于 FastAPI、原生前端和视觉大模型的投票单识别系统。系统可以批量上传纸质投票单或民主测评表图片，自动识别候选人、选项、勾选结果和异常标记，并提供人工复核、重新统计、重复票提醒、统计分析和 Excel/CSV 导出。

## 功能总览

- 创建投票活动：支持活动名称、候选人名单、选项列表、无效标记规则。
- 活动模板复用：创建活动后自动保存模板，下次可选择历史模板一键填充。
- 批量上传图片：支持 PNG、JPG、JPEG、BMP、TIF、TIFF。
- 视觉模型识别：识别标题、候选人、评价选项、选项格内标记和行级结果。
- 严格标记判定：只有标准对勾、V 形勾、短 tick 算有效；画圈、打叉、黑块、黑点、涂抹、线条等算无效标记。
- 异常票复核：支持查看原图、修改候选人、修改选项、修改异常原因、填写复核备注。
- 自动重新统计：人工校正保存后，系统自动刷新活动总数、候选人明细和异常统计。
- 重复票检测：支持完全相同文件检测，也支持重新拍摄后亮度略变的疑似重复检测。
- 活动结果看板：展示总票数、有效勾选、异常票、作废/无效票、疑似重复票、复核完成率。
- 投票单筛选：支持全部、仅异常、仅作废/无效、仅正常、疑似重复票。
- 统计分析：展示候选人排行、中文异常类型统计、候选人票数明细。
- 数据导出：支持 CSV 和 Excel 导出，用于答辩、留档和后续复查。
- 手机上传入口：每个活动有移动端链接，局域网内可用手机拍照上传。

## 技术结构

```text
IOT_project/
├─ ballot_recognition/      # 视觉模型调用、prompt、识别结果归一化、批量识别
├─ webapp/                  # FastAPI 后端、状态存储、任务管理、接口 schema
├─ webapp_frontend/         # 前端 HTML、CSS、状态、API、渲染逻辑
├─ tests/                   # 单元测试
├─ webapp_data/             # 本地运行数据，包含活动、上传图片和识别结果
├─ run_web_app.py           # 本地启动入口
└─ requirements.txt         # Python 依赖
```

## 本地启动

```powershell
cd D:\LectureFile\IOT_project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_web_app.py
```

浏览器打开：

```text
http://127.0.0.1:8000
```

## 大模型环境变量

### 智谱 GLM

```powershell
$env:VISION_MODEL_PROVIDER="zhipu"
$env:$env:VISION_MODEL_PROVIDER="zhipu"
$env:VISION_MODEL_API_KEY=
$env:VISION_MODEL_NAME="glm-4.6v"
$env:VISION_MODEL_API_URL="https://open.bigmodel.cn/api/paas/v4/chat/completions"
```

### OpenAI-compatible

```powershell
$env:VISION_MODEL_PROVIDER="openai_compatible"
$env:VISION_MODEL_API_KEY="你的 API Key"
$env:VISION_MODEL_NAME="你的视觉模型名称"
$env:VISION_MODEL_API_URL="https://api.openai.com/v1/chat/completions"
```

可选环境变量：

```text
VISION_MODEL_TIMEOUT_SECONDS=90
VISION_MODEL_RESPONSE_FORMAT=true
APP_DATA_DIR=webapp_data
PUBLIC_BASE_URL=http://服务器地址:端口
HOST=0.0.0.0
PORT=8000
```

## 使用流程

1. 打开系统首页。
2. 在“上传识别”页面创建活动。
3. 填写活动名称、候选人名单、选项列表、无效标记规则。
4. 如果已有历史配置，可在“使用历史模板”下拉框选择模板自动填充。
5. 上传一张或多张投票单图片。
6. 等待识别任务完成。
7. 在“活动看板”查看总览数据。
8. 在“投票单明细”筛选异常票、作废/无效票、重复票。
9. 在“异常复核”中查看原图并人工校正。
10. 保存复核结果后，系统自动重新统计。
11. 活动结束后导出 CSV 或 Excel。

## 识别规则

系统采用严格计票规则：

- 有效标记：标准对勾、V 形勾、短 tick。
- 无效标记：圆圈、O、X、十字、实心黑块、黑点、涂抹、线条、重度阴影。
- 无效标记不计票，异常原因为 `invalid_mark`。
- 多个有效勾选不计票，异常原因为 `multiple_marks`。
- 多选项表格中漏选不计票，异常原因为 `missing_mark`。
- 标记跨格、压线严重或无法明确归属时，异常原因为 `unclear_mark`。
- 候选人姓名不可读时，异常原因为 `unreadable_candidate_name`。
- 单选项表格中，如果只有“同意/通过/合格”一类选项，未勾选可视为有效否定结果，不自动判异常。

## 重复票检测

系统会在同一活动内检测重复票：

- `confirmed_exact`：图片文件内容完全一致。
- `suspected_same_ballot`：图片感知哈希接近，并且识别结果指纹一致，用于发现同一张纸重新拍摄的情况。

重复票不会自动删除，也不会自动作废。系统只提示疑似重复组，管理员需要进入复核页查看原图后再决定如何处理。

近似重复检测依赖 OpenCV，服务器需要安装：

```powershell
pip install opencv-python
```

## 统计分析

统计分析页包含：

- 候选人排行。
- 候选人票数明细表。
- 中文异常类型统计。

候选人票数明细会优先显示活动模板里的中文选项，例如“优秀 / 合格 / 不合格”。如果模型结果中同时存在 `excellent / qualified / unqualified` 等英文 code，前端会隐藏这些重复英文列，只保留中文统计列。

## 导出内容

CSV 和 Excel 导出包含：

- 活动名称和票数概览。
- 各选项汇总。
- 每个候选人的得票明细。
- 每张投票单的行级识别结果。
- 异常票列表。
- 人工复核状态和复核备注。

## 数据保存位置

默认数据目录：

```text
webapp_data/
```

主要文件：

```text
webapp_data/state.json
webapp_data/activities/<activity_id>/uploads/<upload_id>/原始图片
webapp_data/activities/<activity_id>/uploads/<upload_id>/result.json
```

建议服务器上使用持久化目录：

```powershell
$env:APP_DATA_DIR="D:\data\iot_project"
```

## 本次代码上传到服务器的文件清单

上传代码时至少需要包含：

```text
README.md
requirements.txt
run_web_app.py
ballot_recognition/
webapp/
webapp_frontend/
```

如果服务器也要运行测试，额外上传：

```text
tests/
```

如果要迁移本地已有活动数据，额外上传：

```text
webapp_data/
```

注意：`webapp_data/` 是运行数据，不是代码。正式服务器已有数据时，更新代码不要覆盖服务器上的 `webapp_data/`，除非你明确要迁移本地数据。

## 服务器更新流程

以下流程适合“服务器已经部署过，现在要上传本地修改后的代码”。

### 1. 在本地确认测试通过

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_webapp_features tests.test_vision_model -v
node --check .\webapp_frontend\app.js
node --check .\webapp_frontend\render.js
```

### 2. 在服务器备份数据

进入服务器项目目录后，先备份数据目录：

```powershell
Copy-Item -Recurse webapp_data webapp_data_backup
```

Linux 服务器可用：

```bash
cp -r webapp_data webapp_data_backup
```

### 3. 停止旧服务

如果是手动运行的服务，停止当前 Python 进程或关闭终端。

如果用 systemd、宝塔、PM2、Docker、Render 等平台部署，请在对应平台里停止或重启服务。

### 4. 上传代码

推荐覆盖上传这些代码目录和文件：

```text
README.md
requirements.txt
run_web_app.py
ballot_recognition/
webapp/
webapp_frontend/
```

不要覆盖服务器上的：

```text
webapp_data/
.venv/
```

### 5. 安装或更新依赖

服务器项目目录下执行：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux 服务器：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

本次新增的关键依赖是：

```text
opencv-python
```

它用于重新拍摄图片的疑似重复票检测。

### 6. 检查环境变量

确认服务器仍然配置了：

```text
VISION_MODEL_PROVIDER
VISION_MODEL_API_KEY
VISION_MODEL_NAME
VISION_MODEL_API_URL
VISION_MODEL_THINKING
APP_DATA_DIR
PUBLIC_BASE_URL
HOST
PORT
```

其中 `APP_DATA_DIR` 应指向服务器持久化数据目录。

### 7. 启动服务

```powershell
python run_web_app.py
```

或按你的服务器平台方式重启服务。

### 8. 验证服务

浏览器访问：

```text
http://服务器地址:端口
```

健康检查：

```text
http://服务器地址:端口/api/healthz
```

确认：

- 页面能打开。
- 活动历史还在。
- 创建活动页面能选择历史模板。
- 上传图片能识别。
- 统计页异常类型显示中文。
- 作废/无效票筛选和异常票筛选不同。
- 疑似重复票筛选可用。

## 常见问题

### 识别速度慢

智谱模型可关闭 thinking：

```powershell
$env:VISION_MODEL_THINKING="false"
```

### 关闭 thinking 后识别不准

当前 prompt 已要求模型输出 `marks / mark_type / is_valid_check`，后端也会用标记类型做硬规则兜底。圈、叉、黑块会强制进入 `invalid_mark`，不计票。

### 统计表出现英文列

创建活动时填写中文选项列表。前端会优先显示模板中的中文选项，并隐藏重复英文 code。

### 服务器上没有疑似重复票检测

检查是否安装 OpenCV：

```powershell
pip install opencv-python
```

### API Key 报错

确认 `VISION_MODEL_API_KEY` 只包含真实 key，不要包含中文说明、空格或注释。
