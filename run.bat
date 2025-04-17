@echo off

REM 创建虚拟环境
python -m venv venv

REM 激活虚拟环境
call venv\Scripts\activate

REM 安装依赖
pip install -r requirements.txt

REM 运行项目
python ui_app.py

start https://cloud.siliconflow.cn/i/QOxdzxkd

pause