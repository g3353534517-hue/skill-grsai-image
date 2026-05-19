# GRS AI Image Generator / GRS AI 图像生成器

![分类](https://img.shields.io/badge/分类-创意工具-green)

## 项目简介

默认图像生成技能，适配 GRS AI 的 GPT-Image-2 模型。所有图像/图片/绘画/生成请求均触发此技能，包括中英文提示词（生图、画图、生成图片、作图、文生图、图生图等）。硅谷服务器默认使用海外节点，延迟最低。

## 功能特性

- GRS AI Image Generation Skill
- 节点说明
- 配置 API 密钥
- 调用方式
- 基础文生图
- 图生图（带参考图）
- 流式进度（轮询模拟）
- 切换国内节点
- 核心函数
- `generate_image(prompt, ...)` — 最常用
- `generate_with_stream(prompt, ...)` — 流式进度
- `submit_task(prompt, ...)` — 提交任务
- `poll_result(task_id, ...)` — 轮询结果
- 支持的图像比例
- 错误处理

## 使用示例

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

## 文件结构

```
SKILL.md
references/api-doc.txt
scripts/grsai_image.py
```

## 许可证

MIT License

---

更多项目请访问：[github.com/g3353534517-hue?tab=repositories](https://github.com/g3353534517-hue?tab=repositories)
