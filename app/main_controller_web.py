# main_controller_web.py (V5.1 - 修复API错误处理)
import os
import json
import logging
import re
import requests
import uuid
from flask import Flask, request, jsonify, render_template
from flask_apscheduler import APScheduler
import google.generativeai as genai
from prompts import INITIAL_PROMPT

# --- 配置 ---
SIMULINK_SERVICE_URL = "http://127.0.0.1:5000/model/build_and_validate"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "failures.log")
tasks = {}

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s -[%(levelname)s]- %(message)s')
controller_log = logging.getLogger('MainController')
failure_log = logging.getLogger('Failures')
failure_log.addHandler(logging.FileHandler(LOG_FILE))

try:
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-pro')
    controller_log.info("✅ Gemini API 配置成功。")
except KeyError:
    controller_log.critical("❌ 错误：环境变量 'GOOGLE_API_KEY' 未设置。请先设置您的API密钥。")
    exit()


def update_task_status(task_id, status, message, result=None):
    if task_id in tasks:
        tasks[task_id]['status'] = status
        tasks[task_id]['message'] = message
        if result:
            tasks[task_id]['result'] = result
        controller_log.info(f"任务 {task_id} 状态更新: {status} - {message}")


def call_gemini_api(prompt, task_id):
    controller_log.info(f"任务 {task_id}: 正在调用 Gemini API...")
    # --- 【关键修正】在这里初始化变量 ---
    ai_response_str = "[AI响应未生成，API调用可能已失败]"
    try:
        generation_config = genai.types.GenerationConfig(temperature=0.0)
        # --- API调用就在下面这行 ---
        response = model.generate_content(prompt, generation_config=generation_config)
        ai_response_str = response.text

        match = re.search(r'```json\s*([\s\S]*?)\s*```', ai_response_str, re.DOTALL)
        if match:
            clean_str = match.group(1).strip()
        elif ai_response_str.strip().startswith('{'):
            clean_str = ai_response_str.strip()
        else:
            raise ValueError(f"AI响应不是有效的JSON格式")

        json.loads(clean_str)
        return clean_str

    except Exception as e:
        # 现在即使API调用失败，ai_response_str也有一个默认值，不会再引发自身的错误
        failure_log.error(f"任务 {task_id}: AI响应解析失败。原始响应: {ai_response_str}")
        raise ValueError(f"调用Google API失败: {e}")


def execute_plan_background_job(task_id, user_demand):
    with app.app_context():
        try:
            update_task_status(task_id, 'processing', '正在生成Simulink指令...')
            prompt = f"{INITIAL_PROMPT}\n\n现在，请为以下用户需求生成JSON指令：\n'{user_demand}'"

            ai_json_str = call_gemini_api(prompt, task_id)
            instruction_json_payload = json.loads(ai_json_str)

            update_task_status(task_id, 'processing', 'AI指令已生成，正在发送给Simulink服务...')
            response = requests.post(SIMULINK_SERVICE_URL, json=instruction_json_payload, timeout=600)

            if response.status_code != 200:
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = {"matlab_error_log": response.text}

                failure_context = {"request_body": instruction_json_payload, "response_body": response_data}
                failure_log.error(json.dumps(failure_context, indent=2, ensure_ascii=False))
                raise Exception(
                    f"Simulink服务返回错误 (状态码 {response.status_code}): {response_data.get('matlab_error_log', '无详细日志')}")

            success_data = response.json()
            update_task_status(task_id, 'completed', '✅ 构建成功！', result=success_data)

        except Exception as e:
            error_message = f"❌ 构建失败: {str(e)}"
            controller_log.error(f"任务 {task_id} {error_message}")
            update_task_status(task_id, 'failed', error_message)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_build', methods=['POST'])
def start_build():
    data = request.get_json()
    if not data or 'demand' not in data:
        return jsonify({"status": "error", "message": "请求体中缺少'demand'字段"}), 400
    task_id = str(uuid.uuid4())
    user_demand = data['demand']
    tasks[task_id] = {'status': 'pending', 'message': '任务已提交，正在等待执行...'}
    scheduler.add_job(id=task_id, func=execute_plan_background_job, args=[task_id, user_demand], trigger='date')
    controller_log.info(f"--- 新任务已提交 --- ID: {task_id}, 需求: {user_demand}")
    return jsonify({"status": "pending", "task_id": task_id})


@app.route('/get_status/<task_id>', methods=['GET'])
def get_status(task_id):
    task = tasks.get(task_id, None)
    if not task:
        return jsonify({"status": "error", "message": "未找到该任务ID"}), 404
    return jsonify(task)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)