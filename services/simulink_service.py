# simulink_service.py (V-Definitive-Fix - 采用两步法并强制转换Position类型)
import matlab.engine
from flask import Flask, request, jsonify
import logging
import re
import traceback
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s -[%(levelname)s]- %(message)s')
service_log = logging.getLogger('SimulinkService')
app = Flask(__name__)
eng = None


def start_matlab_engine():
    global eng
    if eng is None:
        try:
            service_log.info("正在启动或连接 MATLAB 引擎... 这可能需要一些时间。")
            eng = matlab.engine.start_matlab()
            service_log.info("✅ MATLAB 引擎连接成功！")
        except Exception as e:
            service_log.error(f"❌ 启动 MATLAB 引擎时发生严重错误: {e}", exc_info=True)
            eng = None
    return eng


def sanitize_name(name):
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if name and name.isdigit():
        name = 'b' + name
    return name or "unnamed_block"


@app.route('/model/build_and_validate', methods=['POST'])
def build_and_validate():
    service_log.info("--- ✅✅✅ 您正在运行的是【V-Definitive-Fix - 两步法+强制类型转换】的 simulink_service.py ✅✅✅ ---")

    if not eng:
        return jsonify({"status": "error", "message": "MATLAB 引擎未连接"}), 503

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "请求体必须是JSON对象，而不是列表或其它类型"}), 400

    model_name = data.get('model_name')
    actions = data.get('actions')

    if not model_name or not isinstance(actions, list):
        return jsonify({"status": "error", "message": "请求JSON中缺少 'model_name' 或 'actions' 列表"}), 400

    try:
        if eng.bdIsLoaded(model_name):
            eng.close_system(model_name, 0, nargout=0)
    except Exception:
        pass  # Ignore error if closing fails

    current_action = None
    name_map = {}

    try:
        service_log.info(f"--- 开始构建模型: {model_name} ---")
        eng.new_system(model_name, nargout=0)
        eng.open_system(model_name, nargout=0)

        # 第一遍：只创建模块，并填充name_map
        for act in actions:
            if act.get('action') == 'add_block':
                current_action = act
                original_name = act.get('block_name')
                block_type = act.get('block_type')
                position_val = act.get('position')

                if not all([original_name, block_type, position_val]):
                    raise ValueError(f"add_block动作缺少必要字段(block_name, block_type, position)。收到: {act}")

                if isinstance(position_val, str):
                    try:
                        position_val = json.loads(position_val)
                    except json.JSONDecodeError:
                        raise ValueError(
                            f"模块 '{original_name}' 的 position 参数是一个格式不正确的字符串: '{position_val}'")

                if not isinstance(position_val, list) or len(position_val) != 4:
                    raise ValueError(
                        f"模块 '{original_name}' 的 position 参数必须是一个包含4个元素的列表。收到: {position_val}")

                sanitized = sanitize_name(original_name)
                if sanitized in name_map.values():
                    i = 1
                    new_sanitized = f"{sanitized}_{i}"
                    while new_sanitized in name_map.values():
                        i += 1
                        new_sanitized = f"{sanitized}_{i}"
                    sanitized = new_sanitized

                name_map[original_name] = sanitized
                destination = f"{model_name}/{sanitized}"

                service_log.info(f"步骤1/2: 创建模块: AI名='{original_name}', 清洗后='{sanitized}'")
                # 【最终修复 - 第1步】使用最纯粹的 add_block，不附加任何额外参数
                eng.add_block(block_type, destination, nargout=0)

                service_log.info(f"步骤2/2: 设置位置: Block='{sanitized}', Position='{position_val}'")
                # 【最终修复 - 第2步】使用 set_param 设置位置，并强制将Python列表转换为MATLAB double向量
                matlab_position = matlab.double(position_val)
                eng.set_param(destination, 'Position', matlab_position, nargout=0)

        # 第二遍：设置其他参数和连线
        for act in actions:
            action_type = act.get('action')
            if action_type in ['set_param', 'add_line']:
                current_action = act

            if action_type == 'set_param':
                original_name = act.get('block_name')
                param_name = act.get('param_name')
                param_value = act.get('param_value')

                if not all([original_name, param_name, param_value is not None]):
                    raise ValueError(f"set_param动作缺少关键字段(block_name, param_name, param_value)。收到: {act}")
                if original_name not in name_map:
                    raise ValueError(f"尝试设置一个未创建的模块参数: '{original_name}'")

                sanitized_name = name_map[original_name]
                service_log.info(f"设置参数: Block='{sanitized_name}', Param='{param_name}', Value='{param_value}'")
                eng.set_param(f"{model_name}/{sanitized_name}", param_name, str(param_value), nargout=0)

            elif action_type == 'add_line':
                from_str_raw = act.get('from')
                to_str_raw = act.get('to')

                if not all([from_str_raw, to_str_raw]):
                    raise ValueError(f"add_line动作缺少'from'或'to'。收到: {act}")

                from_block_orig, from_port = from_str_raw.split('/')
                to_block_orig, to_port = to_str_raw.split('/')

                if from_block_orig not in name_map: raise ValueError(
                    f"连线源模块AI名称未在映射表中找到: '{from_block_orig}'")
                if to_block_orig not in name_map: raise ValueError(
                    f"连线目标模块AI名称未在映射表中找到: '{to_block_orig}'")

                from_block_sanitized = name_map[from_block_orig]
                to_block_sanitized = name_map[to_block_orig]
                from_str = f"{from_block_sanitized}/{from_port}"
                to_str = f"{to_block_sanitized}/{to_port}"

                service_log.info(f"连接线路: From='{from_str}', To='{to_str}'")
                eng.add_line(model_name, from_str, to_str, 'autorouting', 'on', nargout=0)

        service_log.info("--- 模型基础构建完成，正在保存... ---")
        eng.save_system(model_name, nargout=0)
        return jsonify({"status": "success", "message": f"模型 '{model_name}' 已成功构建并保存。"})

    except Exception as e:
        error_type = "UnknownError"
        if current_action:
            action_type = current_action.get('action', 'N/A')
            if action_type == 'add_block':
                error_type = "BlockCreationError"
            elif action_type == 'set_param':
                error_type = "ParameterError"
            elif action_type == 'add_line':
                error_type = "ConnectionError"

        error_message = traceback.format_exc()
        service_log.error(f"❌ 在处理动作 {json.dumps(current_action, ensure_ascii=False)} 时出错: {error_message}")
        error_response = {
            "status": "error",
            "error_type": error_type,
            "failed_action": current_action,
            "matlab_error_log": str(e)
        }
        return jsonify(error_response), 500


if __name__ == '__main__':
    start_matlab_engine()
    if eng:
        app.run(host='0.0.0.0', port=5000)
    else:
        service_log.critical("无法启动Flask服务器，因MATLAB引擎未能初始化。")
