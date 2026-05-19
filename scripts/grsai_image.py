#!/usr/bin/env python3
"""
GRS AI Image Generation Helper (GPT-Image-2)
默认生图 Skill - 硅谷服务器优化版

优化记录：
- 默认使用轮询模式（webHook="-1"），避免流式响应卡死
- 动态轮询间隔：前期慢（5s），后期快（2s），减少无效请求
- 自动重试：API 5xx / 网络错误自动重试3次
- 下载超时放宽到60s，支持大文件
- generate_with_stream 改用轮询模拟，避免 SSE 连接挂起
- 可配置日志级别
"""

import os
import time
import json
import logging
import requests
from typing import Optional, List, Dict, Any, Union, Iterator

logger = logging.getLogger("grsai-image")

# 硅谷服务器推荐使用海外节点
DEFAULT_BASE_URL = "https://grsaiapi.com"
DOMESTIC_BASE_URL = "https://grsai.dakka.com.cn"

# 轮询模式常量：webHook="-1" 让接口立即返回 task_id
POLL_MODE_HOOK = "-1"

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # 秒，指数退避基数

# 完整支持的图像比例列表（共16种）
SUPPORTED_ASPECT_RATIOS = [
    "auto", "1:1", "16:9", "9:16", "21:9", "9:21",
    "3:2", "2:3", "4:3", "3:4", "5:4", "4:5",
    "1:3", "3:1", "2:1", "1:2"
]


def get_api_key(api_key: Optional[str] = None) -> str:
    if api_key:
        return api_key
    key = os.getenv("GRS_API_KEY")
    if not key:
        raise ValueError("请先设置环境变量 GRS_API_KEY，或传入 api_key 参数")
    return key


def get_headers(api_key: str) -> dict:
    return {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}


def _request_with_retry(method, url, max_retries=MAX_RETRIES, **kwargs) -> requests.Response:
    """带自动重试的 HTTP 请求，处理 5xx 和网络错误"""
    kwargs.setdefault("timeout", 30)
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = method(url, **kwargs)
            # 5xx 服务端错误，重试
            if resp.status_code >= 500:
                logger.warning(f"[GRS] 服务端错误 {resp.status_code}，第 {attempt}/{max_retries} 次重试...")
                last_exc = requests.HTTPError(f"Server {resp.status_code}: {resp.text[:200]}")
                if attempt < max_retries:
                    time.sleep(RETRY_BACKOFF ** attempt)
                continue
            # 4xx 客户端错误，不重试
            return resp
        except (requests.Timeout, requests.ConnectionError) as e:
            logger.warning(f"[GRS] 网络错误 ({type(e).__name__})，第 {attempt}/{max_retries} 次重试...")
            last_exc = e
            if attempt < max_retries:
                time.sleep(RETRY_BACKOFF ** attempt)
    # 所有重试都失败
    if last_exc:
        raise last_exc
    raise RuntimeError("不应到达此处")


def submit_task(
    prompt: str,
    aspect_ratio: str = "1:1",
    reference_urls: Optional[Union[str, List[str]]] = None,
    web_hook: Optional[str] = None,
    shut_progress: bool = True,
    base_url: str = DEFAULT_BASE_URL,
    api_key: Optional[str] = None,
    timeout: int = 30,
) -> dict:
    """
    提交图片生成任务。
    默认使用轮询模式（webHook="-1"），接口会立即返回 task_id，
    然后用 poll_result() 轮询获取结果。这避免了流式响应挂起的问题。

    Args:
        prompt: 图像描述提示词（必填）
        aspect_ratio: 图像比例，默认 "1:1"
        reference_urls: 参考图URL，支持单张(str)或多张(List[str])
        web_hook: 自定义回调URL。不传则默认 "-1"（轮询模式）
        shut_progress: 是否关闭进度推送，默认 True
        base_url: API 节点地址
        api_key: API 密钥，不传则从环境变量读取
        timeout: 提交请求的超时时间（秒），注意：这不是任务执行时间

    Returns:
        接口返回的 JSON，包含 data.id（任务ID）
    """
    api_key = get_api_key(api_key)
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "aspectRatio": aspect_ratio,
        "shutProgress": shut_progress,
        # 默认轮询模式：立即返回 task_id，避免流式连接挂起
        "webHook": web_hook or POLL_MODE_HOOK,
    }
    if reference_urls:
        payload["urls"] = [reference_urls] if isinstance(reference_urls, str) else reference_urls

    resp = _request_with_retry(
        requests.post,
        f"{base_url}/v1/draw/completions",
        headers=get_headers(api_key),
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def poll_result(
    task_id: str,
    base_url: str = DEFAULT_BASE_URL,
    api_key: Optional[str] = None,
    max_wait: int = 300,
    verbose: bool = True,
) -> dict:
    """
    轮询获取任务结果。
    动态调整轮询间隔：进度 <20% 时每5秒查一次（减少无效请求），
    进度 >=20% 时每2秒查一次（更快感知完成）。

    Args:
        task_id: 任务ID
        base_url: API 节点地址
        api_key: API 密钥
        max_wait: 最大等待时间（秒），默认300秒
        verbose: 是否打印进度日志，默认 True

    Returns:
        任务结果 dict，包含 status, progress, results 等

    Raises:
        TimeoutError: 超过 max_wait 仍未完成
        Exception: 任务失败（failure_reason / error）
    """
    api_key = get_api_key(api_key)
    start = time.time()
    last_progress = -1

    while True:
        resp = _request_with_retry(
            requests.post,
            f"{base_url}/v1/draw/result",
            headers=get_headers(api_key),
            json={"id": task_id},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        result = data.get("data", {})
        status = result.get("status")
        progress = result.get("progress", 0)

        if verbose and progress != last_progress:
            logger.info(f"[GRS] {task_id}: {progress}% - {status}")
            last_progress = progress

        if status == "succeeded":
            return result
        if status == "failed":
            reason = result.get("failure_reason") or result.get("error") or "未知错误"
            raise Exception(f"任务失败: {reason}")

        elapsed = time.time() - start
        if elapsed > max_wait:
            raise TimeoutError(f"任务处理超时（{max_wait}s），任务 {task_id} 当前进度 {progress}%")

        # 动态轮询间隔：前期慢轮询，后期快轮询
        interval = 5 if progress < 20 else 2
        time.sleep(interval)


def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    reference_urls: Optional[Union[str, List[str]]] = None,
    download: bool = False,
    save_dir: str = "/tmp",
    base_url: str = DEFAULT_BASE_URL,
    api_key: Optional[str] = None,
    max_wait: int = 300,
    verbose: bool = True,
) -> dict:
    """
    同步生成图片：提交任务 → 轮询等待 → （可选）下载到本地。

    Args:
        prompt: 图像描述提示词（必填）
        aspect_ratio: 图像比例，默认 "1:1"
        reference_urls: 参考图URL，支持单张或多张
        download: 是否自动下载图片到本地，默认 False
        save_dir: 下载保存目录，默认 "/tmp"
        base_url: API 节点地址
        api_key: API 密钥
        max_wait: 最大等待时间（秒），默认300秒
        verbose: 是否打印进度日志，默认 True

    Returns:
        {
            "task_id": str,
            "image_urls": [str, ...],
            "status": "succeeded",
            "local_paths": [str, ...]  # 仅当 download=True 时存在
        }
    """
    submit = submit_task(prompt, aspect_ratio, reference_urls, base_url=base_url, api_key=api_key)
    task_id = submit["data"]["id"]
    if verbose:
        logger.info(f"[GRS] 已提交任务: {task_id}")

    result = poll_result(task_id, base_url=base_url, api_key=api_key, max_wait=max_wait, verbose=verbose)
    urls = [r["url"] for r in result.get("results", [])]
    final = {"task_id": task_id, "image_urls": urls, "status": result.get("status")}

    if download and urls:
        os.makedirs(save_dir, exist_ok=True)
        local = []
        for i, u in enumerate(urls):
            r = _request_with_retry(requests.get, u, max_retries=2, timeout=60)
            r.raise_for_status()
            ext = u.split(".")[-1].split("?")[0] or "png"
            path = f"{save_dir}/grsai_{task_id[:8]}_{i}.{ext}"
            with open(path, "wb") as f:
                f.write(r.content)
            local.append(path)
            if verbose:
                logger.info(f"[GRS] 已保存: {path} ({len(r.content) // 1024}KB)")
        final["local_paths"] = local

    return final


def generate_with_stream(
    prompt: str,
    aspect_ratio: str = "1:1",
    reference_urls: Optional[Union[str, List[str]]] = None,
    base_url: str = DEFAULT_BASE_URL,
    api_key: Optional[str] = None,
    max_wait: int = 300,
) -> Iterator[Dict[str, Any]]:
    """
    流式生成模式（轮询模拟），实时返回任务进度。
    
    注意：原 API 的 SSE 流式模式在服务器端会挂起连接导致超时，
    因此改为轮询模拟流式输出，效果等价但更稳定。

    Yields:
        每个进度更新的字典，包含 id, progress, status 等信息。
        当 status 为 "succeeded" 或 "failed" 时，迭代结束。

    Example:
        for progress in generate_with_stream("一只可爱的猫咪"):
            print(f"进度: {progress['progress']}%, 状态: {progress['status']}")
            if progress['status'] == 'succeeded':
                print("图片链接:", progress['results'])
    """
    api_key = get_api_key(api_key)
    submit = submit_task(prompt, aspect_ratio, reference_urls, base_url=base_url, api_key=api_key)
    task_id = submit["data"]["id"]

    start = time.time()
    last_progress = -1

    while True:
        resp = _request_with_retry(
            requests.post,
            f"{base_url}/v1/draw/result",
            headers=get_headers(api_key),
            json={"id": task_id},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        result = data.get("data", {})
        progress_val = result.get("progress", 0)
        status = result.get("status")

        # 只在进度变化时 yield，避免重复
        if progress_val != last_progress or status in ("succeeded", "failed"):
            result["id"] = task_id
            yield result
            last_progress = progress_val

        if status in ("succeeded", "failed"):
            break

        if time.time() - start > max_wait:
            yield {"id": task_id, "progress": last_progress, "status": "timeout", "error": f"超过 {max_wait}s 未完成"}
            break

        # 动态间隔
        time.sleep(5 if last_progress < 20 else 2)
