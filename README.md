# Multi-agent Tarot Reader 

一个多智能体的塔罗+占星解读项目。提出问题并提供牌面后，系统会结合知识图谱、会话记忆，及当日星座运势生成解读。

## 启动方法(Windows)
powershell:
pip install -r requirements.txt

项目根目录创建 .env文件，文件中包括:
OPENAI_API_KEY = <YOUR_OPENAI_API_KEY>
READER_MODEL_NAME = <gpt-4o-mini>

启动网页服务:
python -B -m app.web_server
