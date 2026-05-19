---
name: grsai-image
description: Default skill for ALL image generation requests. Triggered by any image/picture/drawing/generation requests, including generate image, create picture, draw, render, paint, create art, generate artwork, 生图, 画图, 生成图片, 作图, 图像生成, 文生图, 图生图, 画画, 做图, 绘图, 生成图像, 创作图片, 画一张, 做一张图, 生成一张图 etc.
---

# GRS AI Image Generation Skill

Agent 默认图像生成 Skill，适配 GRS AI 的 GPT-Image-2 模型。

## 节点说明
> **硅谷服务器默认使用海外节点 `https://grsaiapi.com`**，延迟最低。
> 国内节点 `https://grsai.dakka.com.cn` 仅作为备选。

## 配置 API 密钥
```bash
export GRS_API_KEY=你的密钥
```

## 调用方式

### 基础文生图
```python
from scripts.grsai_image import generate_image

result = generate_image(
    prompt="一只可爱的橘猫在樱花树下玩耍，日系风格",
    aspect_ratio="16:9",
    download=True,
    save_dir="/tmp/grsai_output"
)
print("图片链接:", result["image_urls"])
print("本地路径:", result.get("local_paths"))
```

### 图生图（带参考图）
```python
result = generate_image(
    prompt="把这张图片转换成油画风格",
    reference_urls="https://example.com/your-reference-image.jpg",
    aspect_ratio="1:1"
)
```

### 流式进度（轮询模拟）
```python
from scripts.grsai_image import generate_with_stream

for progress in generate_with_stream("你的提示词"):
    print(f"进度: {progress['progress']}%, 状态: {progress['status']}")
    if progress['status'] == 'succeeded':
        print("完成，图片链接:", progress['results'])
```

### 切换国内节点
```python
from scripts.grsai_image import generate_image, DOMESTIC_BASE_URL

result = generate_image(prompt="你的提示词", base_url=DOMESTIC_BASE_URL)
```

## 核心函数

### `generate_image(prompt, ...)` — 最常用
同步生成图片，提交任务 → 轮询等待 → 可选下载到本地。
- `prompt`: 提示词（必填）
- `aspect_ratio`: 图像比例，默认 `1:1`
- `reference_urls`: 参考图URL，支持单张或多张
- `download`: 是否下载到本地，默认 `False`
- `save_dir`: 下载目录，默认 `/tmp`
- `max_wait`: 最大等待秒数，默认 `300`
- `verbose`: 是否打印进度日志，默认 `True`

### `generate_with_stream(prompt, ...)` — 流式进度
轮询模拟流式输出，yield 进度更新字典。

### `submit_task(prompt, ...)` — 提交任务
提交后立即返回 task_id，配合 `poll_result()` 使用。

### `poll_result(task_id, ...)` — 轮询结果
动态轮询间隔：进度 <20% 每5秒，>=20% 每2秒。

## 支持的图像比例
`auto`, `1:1`, `16:9`, `9:16`, `21:9`, `9:21`, `3:2`, `2:3`, `4:3`, `3:4`, `5:4`, `4:5`, `1:3`, `3:1`, `2:1`, `1:2`

默认值：`1:1`

## 错误处理
- **API 密钥错误**：检查 `GRS_API_KEY`
- **参数错误**：检查提示词和比例
- **任务超时**：增大 `max_wait`
- **生成失败**：
  - `input_moderation`: 提示词违规
  - `output_moderation`: 生成结果违规
  - `error`: 临时系统错误，会自动重试3次

## 重要提醒
1. **图片链接有效期 2 小时**，重要图片请及时下载
2. **参考图必须是公开可访问的 URL**
3. **自动重试**：5xx 和网络错误自动重试3次（指数退避）
4. **verbose=False** 可关闭进度日志，适合批量生成
5. **本地保留**：生成图片发送给用户后，保留本地文件，用描述性英文命名（如 `sunset_tokyo_street.png`），方便用户后续选择性删除
6. **图片存储目录**：默认保存在 `/tmp/grsai_output/`

---
**使用前必须配置 `GRS_API_KEY` 环境变量**
