# 视频生成翻译字幕 Agent 策划书

## 1. 项目概述

本项目旨在设计并实现一个自动化视频字幕翻译 Agent。系统从视频或音频中提取源语言字幕，结合标题、简介、搜索结果、上下文、术语表与必要的视频理解能力，自动生成目标语言字幕，并对歧义、断句、专有名词、时间轴和字幕可读性进行持续修正。

项目目标不是简单地“把 Whisper 输出逐句翻译”，而是构建一个具备上下文理解、风险判断、局部工具调用和质量自检能力的字幕生产流水线。

## 2. 背景与问题

现有自动字幕翻译流程通常存在以下问题：

- ASR 转写结果存在误听、漏词、断句不自然等问题。
- 翻译模型逐句处理时容易丢失上下文。
- 专有名词、人名、作品名、技术词汇缺少统一译法。
- 复杂句子被错误拆分，导致字幕语义不完整。
- 目标语言字幕长度、阅读速度和时间轴不匹配。
- 自动翻译结果难以解释错误来源，也难以局部修复。

因此，本项目需要一个多阶段 Agent，而不是单一翻译器。

## 3. 核心目标

### 3.1 功能目标

- 从视频或音频中自动生成源语言字幕。
- 根据标题、简介和转写文本生成全局上下文。
- 自动抽取并维护术语表、专有名词表和翻译策略。
- 按上下文窗口翻译字幕，而不是孤立逐句翻译。
- 自动识别高风险字幕片段，包括歧义、误听、断句异常和术语冲突。
- 对高风险片段触发工具调用，包括上下文检查、搜索、重新 ASR、视频片段理解。
- 自动修复字幕断句、合并、拆分与时间轴。
- 输出最终字幕文件，如 SRT、VTT、ASS。
- 输出质量报告，记录不确定片段、修复操作和风险原因。

### 3.2 非目标

第一阶段不追求完全替代专业字幕组的最终审校能力。

系统应优先做到：

- 自动生成可用字幕。
- 对不确定内容可解释。
- 能够局部修复。
- 保留完整中间状态，方便后续调优。

## 4. 用户场景

### 4.1 知识类视频翻译

用户上传技术演讲、课程、访谈或 podcast。系统自动识别术语、生成词库并翻译成目标语言字幕。

### 4.2 YouTube / Bilibili 视频字幕生成

用户提供视频、标题和简介。系统结合外部搜索理解背景，生成适合发布的字幕。

### 4.3 影视、游戏、教程类视频

系统在文字上下文不足时，截取关键视频帧或片段进行视觉理解，辅助翻译 “this”, “that”, “here”, “the button” 等依赖画面的表达。

### 4.4 纯音频或广播内容

系统禁用视频理解模块，主要依靠音频重识别、上下文窗口、搜索和术语表修复歧义。

## 5. 总体方案

推荐采用“全局上下文 + 局部 ReAct 修复”的架构。

整体流程如下：

```text
视频 / 音频输入
  ↓
音频提取
  ↓
Whisper / ASR 转写
  ↓
源字幕清理与初步重分段
  ↓
标题、简介、全文转写分析
  ↓
关键词抽取、搜索、术语表生成
  ↓
上下文窗口翻译
  ↓
字幕质量检查
  ↓
高风险片段 ReAct 修复
  ↓
术语一致性与时间轴修正
  ↓
输出字幕与质量报告
```

## 6. 模块设计

### 6.1 输入模块

输入内容包括：

- 视频文件，可选。
- 音频文件，可选。
- 标题，可选。
- 简介，可选。
- 目标语言。
- 风格要求，例如直译、意译、口语化、正式字幕、技术字幕。

输出为标准化任务对象：

```json
{
  "video_path": "input.mp4",
  "audio_path": "input.wav",
  "title": "optional title",
  "description": "optional description",
  "source_language": "auto",
  "target_language": "zh-CN",
  "style": "natural subtitle"
}
```

### 6.2 ASR 模块

ASR 模块负责生成源语言字幕与时间戳。

建议能力：

- 支持 Whisper、faster-whisper 或其他 ASR 服务。
- 支持语言固定，避免自动识别错误。
- 支持 initial prompt，将标题、简介、术语提示注入 ASR。
- 支持词级时间戳，用于后续断句修复。
- 支持局部音频重跑，用于高风险片段修复。

输出结构：

```json
{
  "segments": [
    {
      "id": 1,
      "start": 0.0,
      "end": 3.2,
      "text": "Today we're going to talk about Whisper.",
      "confidence": 0.91
    }
  ]
}
```

### 6.3 源字幕预处理模块

该模块负责清理和规范化 ASR 输出。

主要任务：

- 去除重复语气词和明显 ASR 噪声。
- 合并过短、不完整片段。
- 标记疑似断句异常片段。
- 保留原始时间轴和原始文本，不直接覆盖。

建议维护 `source_segments` 和 `segment_operations`，避免修改过程不可追溯。

### 6.4 全局上下文模块

该模块在翻译前运行，用于建立视频主题理解。

输入：

- 标题。
- 简介。
- 源语言字幕全文。
- 可选搜索结果。

输出：

- 视频主题摘要。
- 章节结构。
- 关键词列表。
- 专有名词列表。
- 术语表。
- 翻译风格指南。

示例：

```json
{
  "summary": "The video explains how to build an automatic subtitle translation agent.",
  "domain": "AI / speech recognition / translation",
  "glossary": {
    "Whisper": {
      "translation": "Whisper",
      "strategy": "keep_original"
    },
    "ReAct": {
      "translation": "ReAct",
      "strategy": "keep_original_with_explanation_if_needed"
    }
  }
}
```

### 6.5 搜索模块

搜索模块用于补充外部知识，但不应对每一句字幕都调用。

触发条件：

- 出现未知专有名词。
- 术语表置信度低。
- 标题和字幕主题不一致。
- Agent 判断存在多种可能解释。
- 翻译结果中出现高风险歧义。

搜索结果应被摘要后写入上下文，不直接长篇塞入翻译 prompt。

### 6.6 翻译模块

翻译不应以孤立单句为单位，而应使用上下文窗口。

推荐方式：

- 每次输入当前字幕片段及前后若干句。
- 输出仍然按原片段 ID 对齐。
- 保留术语表和风格约束。
- 标记无法确定的内容，而不是强行自信翻译。

示例输入窗口：

```json
{
  "current_segment_ids": [15, 16, 17],
  "context_before": [12, 13, 14],
  "context_after": [18, 19, 20],
  "glossary": {},
  "style": "natural Chinese subtitle"
}
```

输出：

```json
{
  "translations": [
    {
      "id": 15,
      "text": "我的意思是，这其实不是一个简单的翻译问题。",
      "confidence": 0.88
    }
  ],
  "notes": [
    {
      "id": 15,
      "risk": "medium",
      "reason": "segment may depend on previous sentence"
    }
  ]
}
```

### 6.7 质量检查模块

质量检查模块负责发现需要修复的字幕片段。

检查项：

- 翻译是否遗漏源文信息。
- 是否出现术语不一致。
- 是否存在明显误译。
- 是否存在上下文歧义。
- 是否存在断句异常。
- 字幕长度是否过长。
- 阅读速度是否过快。
- 时间轴是否过短。
- 是否需要合并或拆分字幕。

每个片段生成风险评分：

```json
{
  "segment_id": 42,
  "risk_score": 0.82,
  "risk_level": "high",
  "reasons": [
    "low ASR confidence",
    "proper noun uncertain",
    "sentence incomplete"
  ],
  "recommended_actions": [
    "rerun_asr_with_context",
    "search_keyword",
    "merge_with_next"
  ]
}
```

### 6.8 ReAct 修复模块

ReAct 修复模块只处理高风险片段。

可用工具：

- 上下文检索。
- 搜索。
- 术语表更新。
- 当前片段音频重识别。
- 当前片段 + 前后片段音频重识别。
- 视频关键帧理解。
- 视频片段理解。
- 字幕合并与拆分。

建议执行策略：

```text
低风险：不处理
中风险：上下文窗口重新翻译
高风险：上下文 + 搜索 + 必要时重跑 ASR
极高风险：视频理解 / 多轮 ASR / 标记到 review report
```

### 6.9 断句修复模块

断句修复是系统质量关键。

主要操作：

- merge：合并语义不完整的连续字幕。
- split：拆分目标语言过长字幕。
- shift_time：微调时间轴。
- expand_audio_window：扩大音频窗口并重新 ASR。
- realign：根据词级时间戳重新对齐字幕。

为避免连锁错误，建议不在遍历过程中直接修改字幕数组，而是收集 patch proposals：

```json
{
  "operation": "merge",
  "segments": [15, 16],
  "reason": "segment 15 is semantically incomplete",
  "confidence": 0.86
}
```

所有 proposals 经冲突检测后统一应用。

### 6.10 视频理解模块

视频理解模块作为兜底能力，而非默认流程。

适用场景：

- 源字幕出现 “this”, “that”, “here”, “the button” 等依赖画面的表达。
- 教程、游戏、影视、商品评测类视频需要画面信息。
- 屏幕上出现文字、代码、PPT、UI 或专有名词。
- ASR 结果疑似把画面中的词听错。

建议策略：

- 首先截取关键帧。
- 只有在动作依赖较强时截取前后 3-8 秒视频片段。
- 对纯音频任务禁用该模块。

## 7. 数据结构设计

### 7.1 Segment

```json
{
  "id": 1,
  "start": 0.0,
  "end": 3.2,
  "source_text": "Today we're going to talk about Whisper.",
  "translated_text": "今天我们来聊聊 Whisper。",
  "asr_confidence": 0.91,
  "translation_confidence": 0.88,
  "risk_level": "low",
  "notes": []
}
```

### 7.2 Glossary Item

```json
{
  "term": "Whisper",
  "translation": "Whisper",
  "strategy": "keep_original",
  "confidence": 0.95,
  "source": "title/transcript/search"
}
```

### 7.3 Operation

```json
{
  "type": "merge",
  "target_segments": [15, 16],
  "reason": "semantic incompleteness",
  "created_by": "segmentation_agent",
  "confidence": 0.86,
  "status": "applied"
}
```

### 7.4 Quality Report

```json
{
  "overall_score": 0.84,
  "high_risk_segments": [15, 42, 87],
  "glossary_conflicts": [],
  "asr_rerun_count": 4,
  "search_count": 7,
  "video_understanding_count": 2
}
```

## 8. Agent 策略

### 8.1 不建议逐句全量 ReAct

逐句 ReAct 的问题：

- 成本高。
- 延迟大。
- 容易过度搜索。
- 局部判断可能破坏整体一致性。

推荐方式：

- 全局分析先行。
- 普通片段批量翻译。
- 高风险片段局部 ReAct。
- 最后整体一致性检查。

### 8.2 风险驱动工具调用

工具调用应由风险评分驱动，而不是由固定流程驱动。

示例：

```text
ASR confidence < 0.65 → 重跑 ASR
出现未知专有名词 → 搜索
当前句语义不完整 → 检查前后句并尝试合并
目标字幕过长 → 拆分或重写
依赖画面指代 → 视频关键帧理解
```

### 8.3 缓存策略

为降低成本，建议缓存：

- ASR 结果。
- 搜索结果。
- 术语表。
- 每个窗口的翻译结果。
- 每个高风险片段的修复记录。
- 视频关键帧分析结果。

## 9. Whisper 与 ASR 策略

### 9.1 初次 ASR

建议配置：

- 如果源语言已知，固定语言。
- 使用标题和简介作为 initial prompt。
- 开启词级时间戳。
- 保留置信度或可替代的质量指标。

### 9.2 局部重跑 ASR

触发条件：

- 片段 ASR 置信度低。
- 翻译后语义不通。
- 前后句明显断裂。
- 疑似专有名词误听。
- 字幕时间过短但文字过多。

重跑范围：

```text
第 1 次：当前字幕音频
第 2 次：当前字幕 + 下一句
第 3 次：当前字幕 + 前后各一句
```

最大建议重跑 2-3 次，避免成本失控。

### 9.3 参数方向

如果使用本地 Whisper / faster-whisper，可考虑：

- language：固定源语言。
- initial_prompt：注入标题、简介、术语。
- temperature：低温稳定，高温作为 fallback。
- beam_size / best_of：改善候选质量。
- word_timestamps：辅助断句。
- VAD：改善语音边界。

## 10. 输出设计

### 10.1 字幕文件

支持：

- SRT
- VTT
- ASS

### 10.2 中间产物

建议保留：

- `source_segments.json`
- `translated_segments.json`
- `glossary.json`
- `quality_report.json`
- `operations.json`
- `uncertain_segments.srt`

### 10.3 质量报告

质量报告应说明：

- 哪些片段风险高。
- 为什么风险高。
- 系统做了哪些修复。
- 哪些内容仍然不确定。
- 是否调用了搜索、重跑 ASR 或视频理解。

## 11. MVP 方案

第一版建议控制复杂度，先实现可运行闭环。

### 11.1 MVP 功能

- 输入视频或音频。
- Whisper 生成源字幕。
- 标题、简介、全文生成摘要和术语表。
- 按上下文窗口翻译。
- 简单断句合并。
- 翻译后质量检查。
- 对高风险片段重新翻译。
- 输出 SRT 和质量报告。

### 11.2 暂不实现

- 视频理解。
- 多轮搜索策略。
- 复杂 segment graph。
- 高级时间轴重对齐。
- 多说话人分离。

### 11.3 MVP 技术路线

```text
Python / Node.js 后端
ffmpeg 提取音频
Whisper / faster-whisper 转写
LLM 生成 glossary
LLM 窗口翻译
LLM 质量检查
SRT/VTT 输出
```

## 12. 进阶版本规划

### 12.1 V1：可用自动字幕

- 完整字幕生成。
- 术语表。
- 上下文窗口翻译。
- 基础质量报告。

### 12.2 V2：高质量自动修复

- 风险驱动 ReAct。
- 搜索工具。
- 局部 ASR 重跑。
- 合并/拆分 patch proposal。
- 术语一致性全局修复。

### 12.3 V3：多模态字幕 Agent

- 视频关键帧理解。
- 视频片段理解。
- 屏幕文字 OCR。
- 教程、游戏、影视类内容增强。

### 12.4 V4：半自动审校工作台

- 展示高风险片段。
- 播放对应视频片段。
- 支持人工确认、编辑和回写术语表。
- 支持团队字幕协作。

## 13. 风险与对策

| 风险 | 影响 | 对策 |
| --- | --- | --- |
| ASR 误听 | 翻译基础错误 | 局部重跑 ASR、术语 prompt、置信度检测 |
| 断句错误 | 语义不完整 | 上下文窗口翻译、合并拆分 proposal |
| 专有名词误译 | 质量下降 | 翻译前生成术语表、搜索验证 |
| Agent 过度调用工具 | 成本和延迟过高 | 风险评分驱动工具调用 |
| 搜索结果不可靠 | 引入错误背景 | 多源摘要、标记来源和置信度 |
| 字幕过长 | 阅读体验差 | 字幕长度检查、目标语言重写 |
| 时间轴错位 | 观看体验差 | 词级时间戳、VAD、局部 realign |
| 全自动不可控 | 错误难发现 | 输出 quality_report 和 uncertain_segments |

## 14. 评估指标

### 14.1 ASR 指标

- WER / CER。
- 低置信片段比例。
- 局部重跑修复成功率。

### 14.2 翻译指标

- 人工抽检准确率。
- 术语一致性。
- 信息遗漏率。
- 高风险片段误报率和漏报率。

### 14.3 字幕体验指标

- 每行字符数。
- 每秒阅读字符数。
- 字幕停留时间。
- 合并拆分后语义完整度。

### 14.4 系统指标

- 平均处理时间。
- 搜索调用次数。
- ASR 重跑次数。
- 视频理解调用次数。
- 单视频平均成本。

## 15. 推荐实施顺序

1. 实现基础输入、音频提取和 Whisper 转写。
2. 实现 SRT/VTT 读写和 segment 数据结构。
3. 实现全文摘要和术语表生成。
4. 实现上下文窗口翻译。
5. 实现翻译后质量检查。
6. 实现简单断句合并和拆分。
7. 实现高风险片段重新翻译。
8. 实现局部 ASR 重跑。
9. 接入搜索工具。
10. 接入视频关键帧理解。
11. 建立审校工作台和人工反馈闭环。

## 16. 结论

视频字幕翻译 Agent 具备较高可行性。最关键的设计原则是：不要将系统设计成逐句翻译器，而应设计成具备全局上下文、术语管理、风险识别和局部修复能力的字幕生产流水线。

第一阶段建议聚焦“Whisper 转写 + 术语表 + 上下文窗口翻译 + 质量检查 + 局部重跑 ASR”。该组合能够在工程复杂度可控的前提下，显著提升自动字幕质量，并为后续搜索、视频理解和人工审校工作台打下基础。
