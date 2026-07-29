# Multi-agent Tarot Reader 

## 项目概述
一个实现塔罗+占星解读的多智能体项目。提出问题并提供牌面后，系统会结合知识图谱、会话记忆，及当日星座运势等生成解读。

## 项目特点
- 构建知识图谱，提升AI占卜师联想能力
- 加入星座运势分析等subagent
- 存储短期记忆，支持多轮对话
- 包含网页端对话系统

## 项目依赖
- Agent工作流构建：LangChain, LangGraph
- 记忆检索：Rank BM25
- Web服务：http.server
- 当前仅支持OpenAI API或兼容OpenAI接口的LLM

## 启动方法
### 创建虚拟环境
```powershell
conda create -n agentic-tarot python=3.10 -y
conda activate agentic-tarot
```
### 安装依赖包
``` powershell
pip install -r requirements.txt
```
### 创建 .env文件:
```text
multi-agent-reader/.env
```
填写以下配置：
```dotenv
OPENAI_API_KEY = <YOUR_OPENAI_API_KEY>
READER_MODEL_NAME = <gpt-4o-mini>
```
### 启动网页服务
```powershell
python -B -m app.web_server
```
