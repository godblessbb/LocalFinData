import requests
import subprocess
import sys
import os

def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        return response.json().get("ip", "无法解析 IP")
    except Exception as e:
        return f"获取失败：{e}"

if __name__ == "__main__":
    # 1. 打印公网 IP
    print("公网 IP 地址为:", get_public_ip())

    # 2. 执行当前目录的 get_all_us_stock_price.py
    script_name = "get_all_us_stock_price.py"
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)

    if os.path.exists(script_path):
        print(f"\n正在执行 {script_name} ...\n")
        # 使用当前 Python 解释器运行
        subprocess.run([sys.executable, script_path])
    else:
        print(f"\n未找到 {script_name}，请确认文件是否在同目录下。")
