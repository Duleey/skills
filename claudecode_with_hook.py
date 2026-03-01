import subprocess
import sys
import datetime
import tempfile
import os

# --------------------------
# 定义 Hook 函数
# --------------------------
def pre_hook(prompt: str) -> str:
    """前置Hook：预处理输入"""
    print(f"[前置Hook] {datetime.datetime.now()} - 处理输入")
    # 自定义逻辑：添加代码规范要求
    enhanced_prompt = (
        "请严格按照PEP8规范生成Python代码，"
        "所有函数必须包含中文文档字符串。需求：" + prompt
    )
    return enhanced_prompt

def post_hook(output: str) -> str:
    """后置Hook：处理输出结果"""
    print(f"[后置Hook] {datetime.datetime.now()} - 处理输出")
    # 自定义逻辑1：提取代码块
    code_block = ""
    if "```python" in output:
        code_block = output.split("```python")[1].split("```")[0].strip()
    
    # 自定义逻辑2：语法校验
    if code_block:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(code_block.encode())
            temp_file = f.name
        
        # 用Python校验语法
        result = subprocess.run(
            ["python3", "-m", "py_compile", temp_file],
            capture_output=True,
            text=True
        )
        os.unlink(temp_file)
        
        if result.returncode != 0:
            print(f"[后置Hook] 语法错误：{result.stderr}")
        else:
            print("[后置Hook] 代码语法校验通过")
    
    return output

# --------------------------
# 主流程：调用CLI + 触发Hook
# --------------------------
def call_claudecode_with_hook(prompt: str):
    # 1. 触发前置Hook
    processed_prompt = pre_hook(prompt)
    
    # 2. 调用claudecode CLI
    print("[主流程] 执行claudecode CLI...")
    try:
        result = subprocess.run(
            ["claude", "-p", processed_prompt],
            capture_output=True,
            text=True,
            check=True
        )
        cli_output = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[错误] claudecode执行失败：{e.stderr}")
        return ""
    
    # 3. 触发后置Hook
    final_output = post_hook(cli_output)
    return final_output

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python claudecode_with_hook.py <生成代码的需求>")
        sys.exit(1)
    
    original_prompt = " ".join(sys.argv[1:])
    output = call_claudecode_with_hook(original_prompt)
    
    print("\n========================================")
    print("最终输出：")
    print(output)