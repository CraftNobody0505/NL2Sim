# prompts.py (V18 - 修正Position坐标系)
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KB_FILE = os.path.join(SCRIPT_DIR, "simulink_blocks_kb.json")

def load_knowledge_base():
    try:
        with open(KB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误：知识库文件未找到于 {KB_FILE}")
        return {}
    except json.JSONDecodeError as e:
        print(f"错误：知识库文件 {KB_FILE} 格式无效: {e}")
        return {}

def format_ports(ports_dict):
    in_ports_raw = ports_dict.get('in', [])
    out_ports_raw = ports_dict.get('out', [])
    port_info = []
    if in_ports_raw:
        in_ports = [f"{p.split('/')[0]}(索引:{p.split('/')[-1]})" if '/' in p else f"端口(索引:{p})" for p in in_ports_raw]
        port_info.append(f"输入: {', '.join(in_ports)}")
    if out_ports_raw:
        out_ports = [f"{p.split('/')[0]}(索引:{p.split('/')[-1]})" if '/' in p else f"端口(索引:{p})" for p in out_ports_raw]
        port_info.append(f"输出: {', '.join(out_ports)}")
    return '; '.join(port_info) if port_info else '无明确端口'

def generate_knowledge_list(kb):
    if not kb:
        return ["--- 知识库为空或加载失败 ---"]
    lines = ['--- **核心模块黄金列表 (从文件动态加载)** ---']
    for name, details in kb.items():
        lines.append(f'-   `{name}`')
        lines.append(f"    -   `block_type`: `{details['block_type']}`")
        port_text = format_ports(details.get('ports', {}))
        lines.append(f"    -   端口: {port_text}")
        param_texts = [f"`{p_name}`(用于设置'{u_name}')" for u_name, p_name in details.get('params', {}).items()]
        if param_texts:
            lines.append(f"    -   可用参数: {', '.join(param_texts)}")
        if 'notes' in details:
            lines.append(f"    -   重要备注: {details['notes']}")
    lines.append('--- **列表结束** ---')
    return lines

BASE_PROMPT_LINES = [
    '你是一个精通MATLAB/Simulink的自动化专家。你的唯一任务是严格、精确、无任何创造性地将用户的自然语言需求转换成特定格式的JSON指令。',
    '你必须严格遵守【原则四】中知识库提供的模块路径、端口索引和参数名。',
    '**【最高原则：最终输出格式】**',
    '你的最终输出**必须且只能**是一个单独的、格式完全正确的JSON对象，其结构必须如下所示，绝对不能只返回"actions"数组：',
    '```json',
    '{',
    '  "model_name": "your_model_name",',
    '  "actions": [ ... ]',
    '}',
    '```',
    '**注意：`actions`数组绝对不能为空，且JSON内部严禁使用任何形式的注释。**',
    '',
    '**【原则二：命名规则】**',
    '`block_name` 必须在模型中唯一，并且**只能包含字母、数字和下划线 `_`**。',
    '',
    '**【原则三：指令格式与坐标系】**',
    # --- 【根本性修复】 明确定义Position的坐标系为 [left, top, right, bottom] 并提供计算示例 ---
    '1.  `add_block`: `{"action": "add_block", "block_type": "...", "block_name": "...", "position": [left, top, right, bottom]}`. **`position`的坐标系是 [左上角x, 左上角y, 右下角x, 右下角y]。这是一个绝对规则。你必须计算并确保 `right` 值大于 `left` 值，`bottom` 值大于 `top` 值。例如，对于一个典型的30x30大小的模块，如果其左上角在(50, 100)，那么它的`position`必须是 `[50, 100, 80, 130]`。绝对禁止生成 `bottom` 小于 `top` 的值。**',
    '2.  `set_param`: `{"action": "set_param", "block_name": "...", "param_name": "...", "param_value": "..."}`.',
    '3.  `add_line`: `{"action": "add_line", "from": "block_name/port_index", "to": "block_name/port_index"}`. **端口必须使用知识库中提供的数字索引。**',
    '',
    '**【原则四：总线处理规则】**',
    '当 `abc to dq0 变换` 模块的 `d` 和 `q` 信号需要被单独连接时，你**必须**执行以下三步操作：',
    '1. 在 `abc_to_dq0` 模块后，**添加一个`解复用器`(Demux) 模块**。',
    '2. 使用 `set_param` 指令，**将这个 `Demux` 模块的 `Outputs` 参数设置为 "2"**。',
    '3. 将 `abc_to_dq0` 的输出(端口1)连接到 `Demux` 的输入(端口1)。然后，所有需要 `d` 信号的地方都从 `Demux` 的端口1引出，所有需要 `q` 信号的地方都从 `Demux` 的端口2引出。',
    '',
    '**【原则五：模块与参数黄金知识库】**',
    '你必须使用下面这个知识库来获取所有模块的 `block_type`、端口索引和可用参数名。',
    '',
    '**【原则六：参数名绝对约束】**',
    '当使用`set_param`指令时，其`param_name`字段的值 **必须** 从【模块与参数黄金知识库】中对应模块的`可用参数`列表中精确选用。例如，对于`正弦波`，可用参数是 `Amplitude`, `Bias`, `Frequency`, `Phase`。**严禁**使用任何知识库列表之外的参数名，比如`Position`是绝对不允许的。',
]

KNOWLEDGE_BASE = load_knowledge_base()
KNOWLEDGE_LIST_LINES = generate_knowledge_list(KNOWLEDGE_BASE)
INITIAL_PROMPT = "\n".join(BASE_PROMPT_LINES + KNOWLEDGE_LIST_LINES)
