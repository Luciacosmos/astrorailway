#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本脚本演示如何在原有星盘生成脚本的基础上添加一个网页应用接口，
并将生成的 SVG 星图直接嵌入网页中显示。
This script demonstrates how to add a web interface on top of the original chart
generation script and directly embed the generated SVG chart into the webpage.
"""

from flask import Flask, request, render_template_string, flash, url_for
import logging
import sys
import os
from pathlib import Path

# 导入 kerykeion 模块
try:
    from kerykeion import AstrologicalSubject, KerykeionChartSVG
except ImportError:
    print("请先安装 kerykeion 模块: pip install kerykeion")
    sys.exit(1)

# 全局日志配置，支持 UTF-8 并输出到控制台和文件
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# 默认 GeoNames 用户名（请根据需要替换）
geonames_username = 'astrolucia'

# 星图输出目录（使用相对路径，方便 Docker 环境下操作）
DOC_DIR = Path("chart")
try:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"输出目录已创建或已存在: {DOC_DIR.resolve()}")
except Exception as e:
    logging.error(f"创建输出目录时发生错误：{e}")
    sys.exit(1)

# 获取当前脚本目录
CURRENT_DIR = Path(os.getcwd()).absolute()

# 检查配置文件，如果不存在则创建默认配置文件
config_path = CURRENT_DIR / "kr.config.json"
if not config_path.exists():
    try:
        with config_path.open('w', encoding='utf-8') as f:
            f.write('{}')
        logging.warning(f"配置文件 kr.config.json 未找到，已生成默认配置文件：{config_path.resolve()}")
    except Exception as e:
        logging.error(f"生成默认配置文件时发生错误：{e}")
        sys.exit(1)

def generate_chart(name, year, month, day, hour, minute, city, nation):
    """
    根据输入信息生成星盘并保存为 SVG 文件。
    Generate a chart based on user input and save as an SVG file.
    """
    try:
        # 创建占星对象
        subject = AstrologicalSubject(
            name=name,
            year=int(year),
            month=int(month),
            day=int(day),
            hour=int(hour),
            minute=int(minute),
            city=city,
            nation=nation,
            geonames_username=geonames_username
        )
        logging.info(f"占星对象创建成功: {subject}")

        # 创建星盘 SVG 对象
        chart = KerykeionChartSVG(
            subject,
            new_output_directory=DOC_DIR,
            new_settings_file=config_path
        )
        logging.info("星盘 SVG 对象创建成功 / Chart SVG object created successfully")

        # 生成 SVG 文件
        output_file = DOC_DIR / f"{name}_NatalChart.svg"
        chart.makeSVG()
        logging.info(f"SVG 文件已成功生成，路径为: {output_file.resolve()}")

        return output_file
    except Exception as e:
        logging.error(f"生成星盘时发生错误：{e}")
        raise

# 创建 Flask 应用
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 请替换为安全的密钥

# 使用内嵌的 HTML 模板生成表单页面，同时嵌入 SVG 内容（如果存在）
template = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>星图生成工具 / Chart Generator</title>
  <style>
    .svg-container {
      width: 100%;
      text-align: center;
      margin-top: 20px;
    }
    svg {
      width: 80%;
      height: auto;
      border: 1px solid #ccc;
    }
  </style>
</head>
<body>
  <h1>星图生成工具 / Chart Generator</h1>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul style="color: red;">
      {% for message in messages %}
        <li>{{ message }}</li>
      {% endfor %}
      </ul>
    {% endif %}
  {% endwith %}
  <form method="post">
    <label>名字 (Name):</label><br>
    <input type="text" name="name"><br>
    <label>出生年 (Year):</label><br>
    <input type="text" name="year"><br>
    <label>出生月 (Month):</label><br>
    <input type="text" name="month"><br>
    <label>出生日 (Day):</label><br>
    <input type="text" name="day"><br>
    <label>出生时 (Hour):</label><br>
    <input type="text" name="hour"><br>
    <label>出生分 (Minute):</label><br>
    <input type="text" name="minute"><br>
    <label>出生城市 (City):</label><br>
    <input type="text" name="city"><br>
    <label>出生国家 (Nation):</label><br>
    <input type="text" name="nation"><br><br>
    <input type="submit" value="生成星图 (Generate Chart)">
  </form>
  
  {% if svg_content %}
  <div class="svg-container">
    <h2>生成的星图 / Generated Chart:</h2>
    {{ svg_content|safe }}
  </div>
  {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    svg_content = None
    if request.method == 'POST':
        # 获取表单数据
        name = request.form.get('name', '').strip()
        year = request.form.get('year', '').strip()
        month = request.form.get('month', '').strip()
        day = request.form.get('day', '').strip()
        hour = request.form.get('hour', '').strip()
        minute = request.form.get('minute', '').strip()
        city = request.form.get('city', '').strip()
        nation = request.form.get('nation', '').strip()
        
        if not all([name, year, month, day, hour, minute, city, nation]):
            flash("请完整填写所有字段 / Please fill out all fields.")
        else:
            try:
                output_file = generate_chart(name, year, month, day, hour, minute, city, nation)
                # 读取生成的 SVG 文件内容
                with output_file.open('r', encoding='utf-8') as f:
                    svg_content = f.read()
                flash("星图已生成! / Chart generated!")
            except Exception as e:
                flash(f"生成星图时发生错误: {e}")
    return render_template_string(template, svg_content=svg_content)

if __name__ == '__main__':
    # Railway 环境变量 PORT 会自动设置，如无则默认使用 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
