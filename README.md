# AI 图像生成 / AI Image Generator (GRS)

![分类](https://img.shields.io/badge/分类-创意工具-green)

## 简介 / Overview

Default skill for ALL image generation requests. Triggered by any image/picture/drawing/generation requests, including generate image, create picture, draw, render, paint, create art, generate artwork, 生图, 画图, 生成图片, 作图, 图像生成, 文生图, 图生图, 画画, 做图, 绘图, 生成图像, 创作图片, 画一张, 做一张图, 生成一张图 etc.

## 详细说明 / Details

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
   ...

## 功能特性 / Features

- GRS AI Image Generation Skill
- 节点说明
- 配置 API 密钥
- 调用方式
- 核心函数
- 支持的图像比例
- 错误处理
- 重要提醒

## 使用示例 / Usage Examples

```bash
export GRS_API_KEY=你的密钥
```

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

```python
result = generate_image(
    prompt="把这张图片转换成油画风格",
    reference_urls="https://example.com/your-reference-image.jpg",
    aspect_ratio="1:1"
)
```

## 文件结构 / File Structure

```
SKILL.md
references/api-doc.txt
scripts/grsai_image.py
```

## 作者 / Author

Hermes Agent Community

## 许可证 / License

MIT License

---

更多技能请访问：[github.com/g3353534517-hue?tab=repositories](https://github.com/g3353534517-hue?tab=repositories)
