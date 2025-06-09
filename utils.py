import json
from openai import OpenAI
import subprocess
import re
import os
import requests
import random


api_key=os.environ.get("OPENAI_KEY")
base_url=os.environ.get("OPENAI_BASE_URL")
client1 = OpenAI(api_key=api_key,base_url = base_url)
client2 = OpenAI(api_key="",base_url = "https://yunwu.ai/v1/")
client3 = OpenAI(api_key="",base_url = "https://api.gpt.ge/v1")
client_deep_seek1=OpenAI(api_key="",base_url="https://api.deepseek.com/v1")
client_deep_seek=OpenAI(api_key="",base_url="https://kg-api.cloud/v1")
# client_moda = OpenAI(
#         api_key="156c8782-f3af-4cc2-9c3c-c7674ea49ce5",  # 请替换成您的 ModelScope SDK Token
#         base_url="https://api-inference.modelscope.cn/v1/"
#     )
client_moda = OpenAI(
        api_key="",  # 请替换成您的 ModelScope SDK Token
        base_url="https://ms-fc-bapp-func-wgnhvzimnv.cn-hangzhou.fcapp.run/v1"
    )



client_moda=OpenAI(api_key="",base_url="https://ms-fc-bapp-func-wgnhvzimnv.cn-hangzhou.fcapp.run/v1")
def getfromOpenAI(system, user,model,temperature=0.7):
    
    
    completion = client1.chat.completions.create(messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], model=model,temperature=temperature)
 
    return completion.choices[0].message.content

def replace_variables(text, variables):
    for variable, value in variables.items():
        text = text.replace(variable, str(value))
    return text

def getNextId(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return len(data)

def reSetId(file_path):
    data=getDictFromJsonl(file_path)
    for index,item in enumerate(data):
        item['id']=index
        
    with open(file_path, 'w') as file:
        for item in data:
            file.write(json.dumps(item, ensure_ascii=False) + '\n')
        

def extract_prompt(file_path, variables):
    with open(file_path, 'r') as file:
        content = file.read()

    #分别是prompt中system和user的起始标记
    system_start_marker = "==== SYSTEM ===="
    user_start_marker = "==== USER ===="

    system_start = content.find(system_start_marker) + len(system_start_marker)
    system_end = content.find(user_start_marker)
    system_text = content[system_start:system_end].strip()

    user_start = content.find(user_start_marker) + len(user_start_marker)
    user_text = content[user_start:].strip()

    system_text = replace_variables(system_text, variables)
    user_text = replace_variables(user_text, variables)

    return system_text, user_text


def get_variables(data, agent_type, flexible_para=None):
    #后面评价combine的时候，需要传入combine的参数，然后会修改字段名称
    if agent_type=="replier":
        if flexible_para=='java':
            return {
                "<VERSION>":"JDK11",
                "<CODE>":data['java_code'],
            }
        return {
            "<VERSION>":data['compare_version'],
            "<PACKAGE>":data['package'],
            "<CODE>":data['solution_function'],
        }
    
    elif agent_type=="judger":
        if flexible_para=="java":
            return{
                "<CODE>":data["java_code"],
                "<AI_API_WRONG>":data["ai_api_wrong"],
                "<AI_API_CHANGE>":data["ai_api_change"],
                "<API_WRONG>":data["signature"],
                "<API_CHANGE>":data["update"]
            }
        if 'version_type'not in data:
            if flexible_para=="combine":
                return{
                "<CODE>":data["solution_function"],
                "<AI_API_WRONG>":data["ai_api_wrong"],
                "<AI_API_CHANGE>":data["ai_api_change"],
                "<API_WRONG>":data["signature_list"],
                "<API_CHANGE>":data["update_list"]
            }
            return {
                "<CODE>":data["solution_function"],
                "<AI_API_WRONG>":data["ai_api_wrong"],
                "<AI_API_CHANGE>":data["ai_api_change"],
                "<API_WRONG>":data["signature"],
                "<API_CHANGE>":data["update"]
        }

        else:
            
            if flexible_para=="combine":
                return{
                    "<CODE>":data["solution_function"],
                    "<AI_API_WRONG>":data["ai_api_wrong"],
                    "<AI_API_CHANGE>":data["ai_api_change"],
                    "<API_WRONG>":data["signature_list"],
                    "<API_CHANGE>":data["update_list"]
            }
            return {
                "<CODE>":data["solution_function"],
                "<AI_API_WRONG>":data["ai_api_wrong"],
                "<AI_API_CHANGE>":data["ai_api_change"],
                "<API_WRONG>":data["signature"],
                "<API_CHANGE>":data["update"]
            }
    elif agent_type=="re_signature":
        return {
            "<NON_SIGNATURE>":data["signature"].split('(')[0],
            "<CODE>":data["code_fixed"],
        }
    elif agent_type == "re_combine_signature":
        return {
            "<NON_SIGNATURE>":data["signature_list"],
            "<CODE>":data["code_fixed"],
        }
    elif agent_type=="generate_script":
        return{
            "<PROBLEM>":data['problem'],
            "<DATA>":data['case'],
            "<IMPORT_METHOD>":data["import"],
            "<TARGET_IMPLEMENTATION>":data['code_fixed'],
        }
    elif agent_type=="contrast_answer":
        return{
            "<RUN_ANSWER>":data["fixed_message"],
            "<RIGHT_ANSWER>":data["message"],
        }
    elif agent_type=="clean_fixcode":
        return{
            "<RESPONSE>":data["code_fixed"],
        }
        
        
def getDictFromJsonl(file_path):
    with open(file_path, 'r',encoding='utf-8') as f:
        data = [json.loads(line) for line in f]

    return data

def parse_answerFromSlm(json_str):
    # if "####" not in json_str:
    #     return None
    # parts = json_str.split('####')
    # ai_api_wrong = parts[0].strip()
    # ai_api_change=parts[1].strip()
    # code_fixed = parts[2].strip()
    # match1=re.search(r'ai_api_wrong:(.*)',ai_api_wrong)
    # match2=re.search(r'ai_api_change:(.*)',ai_api_change)
    # match3=re.search(r'code_fixed(.*)',code_fixed)
    # code_fixed=extract_python_code(code_fixed)
    # if code_fixed=='' or code_fixed==None:
    #     return None
    
    # if match1 and match2 and match3:
    #     return {
    #         "ai_api_wrong":match1.group(1).strip(),
    #         "ai_api_change":match2.group(1).strip(),
    #         "code_fixed":code_fixed,
    #     }
    # return None
    #暂时写法，后面再改
    if json_str=="":
        return None
    return {"ai_api_wrong":"None","ai_api_change":"None","code_fixed":json_str}
    pattern1 = r"ai_api_wrong:\s*(.*?)\s*ai_api_change:\s*(.*?)\s*code_fixed:\s*```python\n(.*?)```"
    pattern2 = r"ai_api_wrong\s*:\s*(.*?)\nai_api_change\s*:\s*(.*?)\ncode_fixed\s*:\s*(.*)"
    match1 = re.search(pattern1, json_str, re.DOTALL)
    match2=re.search(pattern2, json_str, re.DOTALL)
    if match1:
        ai_api_wrong = match1.group(1).strip()
        ai_api_change = match1.group(2).strip()
        code_fixed = match1.group(3).strip()
        if ai_api_wrong and ai_api_change and code_fixed:
            return {
                "ai_api_wrong":re.sub("####","",ai_api_wrong),
                "ai_api_change":re.sub("####","",ai_api_change),
                "code_fixed":code_fixed,
            }
        return None
    
    elif match2:
        ai_api_wrong = match2.group(1).strip()
        ai_api_change = match2.group(2).strip()
        code_fixed = match2.group(3).strip()
        if ai_api_wrong and ai_api_change and code_fixed:
            return {
                "ai_api_wrong":re.sub("####","",ai_api_wrong),
                "ai_api_change":re.sub("####","",ai_api_change),
                "code_fixed":code_fixed,
            }
        return None
    
    return None
    
def parserjava(str):
    pattern = r"ai_api_wrong:(.*?)\nai_api_change:(.*)"
    match = re.search(pattern, str, re.DOTALL)
    if match:
        ai_api_wrong = match.group(1).strip()
        ai_api_change = match.group(2).strip()
        if ai_api_wrong!='' and ai_api_change!='':
            return {
                "ai_api_wrong":ai_api_wrong,
                "ai_api_change":ai_api_change,
            }
        return None
    else:
        return None
    
def extract_python_code(s):

    # 使用正则表达式匹配Python代码块
    pattern = r'```python(.*?)```'
    match = re.search(pattern, s, re.DOTALL)
    
    if match:
        # 如果找到匹配，返回匹配的代码块
        return match.group(1).strip()
    else:
        # 如果未找到匹配，返回原始字符串（或可以选择返回空字符串）
        return s
    

def safe_json_loads(json_str,is_slm=False):
    try:
        if is_slm:
            return parse_answerFromSlm(json_str)
        patter=r"</think>"
        result = re.split(patter, json_str, maxsplit=1)
        if len(result)==2:
            return json.loads(result[1])

        # 尝试解析JSON字符串
        patter=r"```json\s*(.*?)\s*```"
        matches = re.findall(patter, json_str, re.DOTALL)
        if matches:
            json_str=matches[0]

        return json.loads(json_str)
    except json.JSONDecodeError:
        # 如果解析失败，打印错误信息并返回None
        print("JSON解析失败，将尝试重新获取数据。")
        return None
    
def append_to_jsonl(file_path, data):
    with open(file_path, 'a', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def rewrite_jsonl(file_path, data):
    with open(file_path,'w',encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

# 用于合并两个jsonl
def contact_jsonl(file_path1,file_path2,fin_output_path):
    data1 = getDictFromJsonl(file_path1)
    data2 = getDictFromJsonl(file_path2)

    for index,_ in enumerate(data1):
        data1[index]['case']=data2[index]

    append_to_jsonl(fin_output_path,data1)

def calculate_accuracy(file_path):
    data = getDictFromJsonl(file_path)
    correct_count = sum(1 for item in data if item['judge_answer']=="1")
    total_count = len(data)
    accuracy = correct_count / total_count
    return accuracy

# 判断环境路径
def env_path(bag,version):
    if re.search("numpy",bag):
        if re.search("1.",version):
            return '/home/yang/miniconda3/envs/env_3_5'#
        else:
            return '/home/yang/miniconda3/envs/env_3_10'#
    elif re.search("pandas",bag):
        if re.search("1.0.0",version):
            return '/home/yang/miniconda3/envs/env_3_8'#
        else:
            return '/home/yang/miniconda3/envs/env_3_10'#
    elif re.search("tensorflow",bag):
        if re.search("2.",version):
            return '/home/yang/miniconda3/envs/env_3_7_2'#
        else:
            return '/home/yang/miniconda3/envs/env_2_7_2'#
    elif re.search("torch",bag):
        if re.search("1.0",version):
            return '/home/yang/miniconda3/envs/env_3_7'
        else:
            return '/home/yang/miniconda3/envs/env_3_10'
    elif re.search("re",bag):
        if re.search("3.10",version):
            return '/home/yang/miniconda3/envs/env_3_10'
        else:
            return '/home/yang/miniconda3/envs/env_2_7'
    elif re.search("os",bag):
        if re.search("3.13",version):
            return "/home/yang/miniconda3/envs/env_3_13"
        else:
            return "/home/yang/miniconda3/envs/env_2_7"
    elif re.search("math",bag):
        if re.search("3.9",version):
            return "/home/yang/miniconda3/envs/env_3_9"
        elif re.search("3.10",version):
            return "/home/yang/miniconda3/envs/env_3_10"
        else:
            return "/home/yang/miniconda3/envs/env_2_7"
    elif re.search("python",bag):
        if re.search("2.7",version):
            return "/home/yang/miniconda3/envs/env_2_7"
        else:
            return "/home/yang/miniconda3/envs/env_3_9"
    elif re.search("random",bag):
        if re.search("2.7",version):
            return "/home/yang/miniconda3/envs/env_2_7"
        else:
            return "/home/yang/miniconda3/envs/env_3_9"
    elif re.search("csv",bag):
        if re.search("3.8",version):
            return "/home/yang/miniconda3/envs/env_3_8"
        else:
            return "/home/yang/miniconda3/envs/env_2_7"
    elif re.search("itertools",bag):
        if re.search("3.0",version):
            return "/home/yang/miniconda3/envs/env_2_7"
        elif re.search("3.10",version):
            return "/home/yang/miniconda3/envs/env_3_10"
        elif re.search("3.8",version):
            return "/home/yang/miniconda3/envs/env_3_8"
        elif re.search("3.12",version):
            return "/home/yang/miniconda3/envs/env_3_12"
        
    # elif re.search("python",bag):
    #     if re.search("")


# 将字符串转化为python代码
def test_str(str,script_path):
    # print("跑了")
    str=re.sub(r"```|python", "", str)
    with open(script_path, "w") as file:
        file.write(str)

def py_run(venv_path, script_path):
    python_executable = os.path.join(venv_path, "bin", "python")

    try:
        # 使用 subprocess 调用 Conda 环境的 Python 来运行脚本
        result = subprocess.run([python_executable, script_path], check=True, capture_output=True, text=True)
        print("成了")
        # 如果没有错误，返回标准输出
        return result.stdout
    except Exception as e:
        print("败了")
        print(f"An unexpected error occurred: {e}")
        return f"An unexpected code_error occurred: {e}"
    
def Request_Model(model,system_prompt,user_prompt):
    url = "https://api.siliconflow.cn/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": system_prompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            }
        ],
        "stream": False,
        "max_tokens": 1024,
        "stop": ["null"],
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "frequency_penalty": 0.5,
        "n": 1,
        "response_format": {"type": "text"}
    }
    headers = {
        "Authorization": "Bearer sk-dwbbdmbiglchvuolnnobfcxynlftnxurheihrlmqbvtpnerl",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)
    data = json.loads(response.text)
    print(data)
    # 提取内容
    content = data['choices'][0]['message']['content']
    print(content)
    return content

# 挑选不同模型有区别的例子
def Select_example(strong_path,weak_path,output_path):
    strong_data = getDictFromJsonl(strong_path)
    weak_data = getDictFromJsonl(weak_path)

    output=[]

    for index,_ in enumerate(strong_data):
        if "re_run_answer" in strong_data[index] and strong_data[index]['re_run_answer'] == 1:
            for index2, _ in enumerate(weak_data):
                if weak_data[index2]["solution_function"] == strong_data[index]["solution_function"]:
                    if not ("re_run_answer" in weak_data[index2] and weak_data[index2]["re_run_answer"]==1):
                        output.append({"solution_function":strong_data[index]["solution_function"]})
    rewrite_jsonl(output_path,output)

def filter_fixed_code(input_path,output_path):
    data = getDictFromJsonl(input_path)
    output=[]

    for index,_ in enumerate(data):
        if "code_fixed" in data[index]:
            output.append(data[index])
    rewrite_jsonl(output_path,output)

def filter_code_ids(input_path, output_path):
    # 获取数据
    data = getDictFromJsonl(input_path)
    code_ids = set()  # 用于存储唯一的 code_id
    output = []  # 存储最终的输出数据

    # 遍历数据，提取每个元素的 "code_id"
    for item in data:
        if "code_id" in item:
            code_ids.add(item["code_id"])  # 只存储唯一的 code_id

    # 将唯一的 code_id 写入输出文件
    for code_id in code_ids:
        output.append({"code_id": code_id})  # 每个 code_id 包装成字典

    # 将结果写入输出文件
    rewrite_jsonl(output_path, output)

# 配合pass@num运行，只要有一个前后转化一致就返回True
def code_id_pass(data,min_num=1):
    num = 0
    for item in data:        
        if "re_run_answer" in item and item["re_run_answer"] == 1:
            num = num + 1
    if num >= min_num:
        return True        
    return False

def compare_versions(version1, version2):
    try:
        # 将版本号字符串拆分成数字列表
        v1 = list(map(int, version1.split('.')))
        v2 = list(map(int, version2.split('.')))
        
        # 补齐较短的版本号，使其长度一致
        max_length = max(len(v1), len(v2))
        v1.extend([0] * (max_length - len(v1)))
        v2.extend([0] * (max_length - len(v2)))
        
        # 逐个比较版本号的每个部分
        for i in range(max_length):
            if v1[i] < v2[i]:
                return -1
            elif v1[i] > v2[i]:
                return 1
    except:
        if version1 < version2:
            return -1
        else :
            return 1

def acculate_pass_code(code_id_path, input_path,package_output_path):
    # 获取所有 code_id 和 data 数据
    code_ids = getDictFromJsonl(code_id_path)  # 假设这个是一个包含 code_id 的列表
    data = getDictFromJsonl(input_path)

    # 初始化输出列表
    output = []
    new2old_pass_code_id_num = 0
    old2new_pass_code_id_num = 0

    # 将 data 按照 code_id 分组
    data_by_code_id = {}

    data_by_package = {}
    for item in data:
        code_id = item.get("code_id")
        if code_id:
            if code_id not in data_by_code_id:
                data_by_code_id[code_id] = []
            data_by_code_id[code_id].append(item)

    # 对每个 code_id 进行处理
    for code_id in code_ids:
        if code_id["code_id"] in data_by_code_id:
            items = data_by_code_id[code_id["code_id"]]
            
            if items[0]['package'] not in data_by_package:
                data_by_package[items[0]['package']] = 0
            
            if code_id_pass(items):
                if compare_versions(items[0]['origin_version'],items[0]['compare_version']) == -1:
                    old2new_pass_code_id_num = old2new_pass_code_id_num +1
                else:
                    new2old_pass_code_id_num =new2old_pass_code_id_num +1
                data_by_package[items[0]['package']] = data_by_package[items[0]['package']] + 1

    rewrite_jsonl(package_output_path,[data_by_package])
    print(f"{input_path}中new2old运行通过的有{new2old_pass_code_id_num}条")
    print(f"{input_path}中old2new运行通过的有{old2new_pass_code_id_num}条")


# 随机选择一个code_id生成转化的多份代码的num份
def Random_code_id(code_id_path, data, num, item_output_path,package_output_path):
    # 获取所有 code_id 和 data 数据
    code_ids = getDictFromJsonl(code_id_path)  # 假设这个是一个包含 code_id 的列表

    # 初始化输出列表
    output = []
    new2old_pass_code_id_num = 0
    old2new_pass_code_id_num = 0

    # 将 data 按照 code_id 分组
    data_by_code_id = {}

    data_by_package = {}
    for item in data:
        code_id = item.get("code_id")
        if code_id:
            if code_id not in data_by_code_id:
                data_by_code_id[code_id] = []
            data_by_code_id[code_id].append(item)

    # 对每个 code_id 进行处理
    for code_id in code_ids:
        if code_id["code_id"] in data_by_code_id:
            items = data_by_code_id[code_id["code_id"]]
            # 随机选择 num 个不重复的记录
            selected_items = random.sample(items, min(num, len(items)))  # 防止超过可选项的数量
            if selected_items[0]['package'] not in data_by_package:
                data_by_package[selected_items[0]['package']] = 0
            
            if code_id_pass(selected_items):
                if compare_versions(selected_items[0]['origin_version'],selected_items[0]['compare_version']) == -1:
                    old2new_pass_code_id_num = old2new_pass_code_id_num +1
                else:
                    new2old_pass_code_id_num =new2old_pass_code_id_num +1
                data_by_package[selected_items[0]['package']] = data_by_package[selected_items[0]['package']] + 1
            for item in selected_items:
                output.append(item)

    # 将结果写入 output_path
    rewrite_jsonl(item_output_path, output)
    rewrite_jsonl(package_output_path,[data_by_package])
    print(f"{item_output_path}中new2old运行通过的有{new2old_pass_code_id_num}条")
    print(f"{item_output_path}中old2new运行通过的有{old2new_pass_code_id_num}条")

# re_signature = 0 表示调用失败
# success_run  = 0 表示编译运行失败
# re_run_answer = 0 表示运行答案前后不一致
def acculate_key(key_name,input_path):
    data = getDictFromJsonl(input_path)
    num = 0

    for _, item in enumerate(data):
        if key_name in item and item[key_name]==0:
            num = num +1
    print(f"统计{key_name}为0的数量：",num)

def acculate_result(input_path):
    data = getDictFromJsonl(input_path)
    old2new_num = 0
    new2old_num = 0

    for _, item in enumerate(data):
        if "re_run_answer" in item and item['re_run_answer']==1:
            if compare_versions(item['origin_version'],item['compare_version']) == -1:
                old2new_num = old2new_num +1
            else:
                new2old_num = new2old_num +1
    print(f"通过的数量：{old2new_num+new2old_num}")
    # print(f"统计通过的old2new的数量：",old2new_num)
    # print(f"统计通过的new2old的数量：",new2old_num)
    

if __name__ == '__main__':
    # # 可供选择的model:
    # """
    # Pro/meta-llama/Meta-Llama-3.1-8B-Instruct
    # meta-llama/Meta-Llama-3.1-8B-Instruct   (免费)
    # meta-llama/Meta-Llama-3.1-70B-Instruct
    # Qwen/Qwen2.5-72B-Instruct
    # Qwen/Qwen2.5-Coder-7B-Instruct  （免费）
    # mirror013/starcoder2-15b （免费）
    # LLM-Research/CodeLlama-70b-Instruct-hf（免费）
    # """
    model = "starcoder"
    system_prompt="你是一个有用的小帮手。"
    user_prompt = "你好。"
    answer=getfromOpenAI(system_prompt,user_prompt,model)
    print(answer)

    # 21、33选中作为例子
    # Select_example("Evaluation/data/finally_result/gpt-4o-mini/combine_eval.jsonl","Evaluation/data/finally_result/llama_8B/combine_eval.jsonl","Evaluation/article_example/combine_example.jsonl")

    # filter_fixed_code("./newdata/raw/gpt-4o-mini/single_eval.jsonl","./newdata/raw/gpt-4o-mini/single_eval.jsonl")
    # filter_code_ids("./newdata/raw/gpt-4o-mini/combine_eval.jsonl","./newdata/combine_code_id.jsonl")
    # num = 1
    # Random_code_id("./newdata/single_code_id.jsonl","./newoutput/gpt-4o-mini/single_eval.jsonl",num,f"./newdata/raw/gpt-4o-mini/single_eval_pass@{num}.jsonl")
    

    