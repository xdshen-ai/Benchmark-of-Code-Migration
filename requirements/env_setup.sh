#!/bin/sh

# 定义环境配置（每行格式：环境名 Python版本 依赖文件）
environments="
code 3.8.2 code.txt
env_2_7 2.7.18 requirements_2_7.txt
env_2_7_2 2.7.18 requirements_2_7_2.txt
env_3_10 3.10.0 requirements_3_10.txt
env_3_12 3.12.1 requirements_3_12.txt
env_3_13 3.13.0 requirements_3_13.txt
env_3_5 3.5.4 requirements_3_5.txt
env_3_7 3.7.3 requirements_3_7.txt
env_3_7_2 3.7.5 requirements_3_7_2.txt
env_3_8 3.8.0 requirements_3_8.txt
env_3_9 3.9.0 requirements_3_9.txt
"

# 检查是否安装了 conda
if ! command -v conda >/dev/null 2>&1; then
    echo "错误: 未找到 Conda。请先安装 Anaconda 或 Miniconda。"
    exit 1
fi

# 循环创建环境（逐行解析配置）
echo "$environments" | while read -r env_name python_version requirements_file; do
    # 跳过空行
    [ -z "$env_name" ] && continue

    echo "========================================"
    echo "创建环境: $env_name (Python $python_version)"
    echo "========================================"
    
    # 创建环境
    conda create -y -n "$env_name" python="$python_version"
    
    # 激活环境并安装依赖（使用 source 确保 conda 环境生效）
    if source activate "$env_name"; then
        echo "正在安装 $requirements_file 中的依赖..."
        conda install -y --file "$requirements_file"
        conda deactivate
        echo "环境 $env_name 创建完成!"
    else
        echo "错误: 无法激活环境 $env_name"
        exit 1
    fi
done

echo "所有环境创建完成!"