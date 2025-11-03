from  utils import *
import re
import time
import os
import argparse

model='gpt-4o-mini'

def RE_signature(input_path,data):
    if "combine" in input_path:
        pass_output=[]
        fail_output=[]
        for _,item in enumerate(data):
            pass_re=True
            variables=get_variables(item,"re_combine_signature" ,None)
            if variables["<CODE>"] == "None":
                item['re_signature']=0
                fail_output.append(item)
                continue
            for signature in variables["<NON_SIGNATURE>"]:
                try:
                    if re.search(signature.split('(')[0],variables["<CODE>"]):
                        item['re_signature']=0
                        fail_output.append(item)
                        pass_re=False
                        break
                except:
                    item['re_signature']=0
                    fail_output.append(item)
                    pass_re=False
                    break
            if pass_re:
                item['re_signature']=1
                pass_output.append(item)
        return pass_output,fail_output
    else:
        pass_output=[]
        fail_output=[]
        for _,item in enumerate(data):
            variables=get_variables(item,"re_signature" ,None)
            if variables["<CODE>"] == "None":
                item['re_signature']=0
                fail_output.append(item)
                continue
            try:
                if re.search(variables["<NON_SIGNATURE>"],variables["<CODE>"]):
                    item['re_signature']=0
                    fail_output.append(item)
                else:
                    item['re_signature']=1
                    pass_output.append(item)
            except:
                # print(variables["<NON_SIGNATURE>"])
                # print(variables["<CODE>"])
                # print(item)
                item['re_signature']=0
                fail_output.append(item)
        return pass_output,fail_output

def Generate_script(begin, data):
    prompt_generate_answer_path = "./prompt/generate_answer.txt"
    
    output = []
    for index, item in enumerate(data):
        if index < begin:
            continue
        
        while True:  # 使用循环来重试
            try:
                variables = get_variables(item, "generate_script", None)
                system_txt, user_txt = extract_prompt(prompt_generate_answer_path, variables)
                str = getfromOpenAI(system_txt, user_txt, model)
                print(str)
                item['fixed_script'] = str
                output.append(item)
                break  # 如果成功，跳出循环
            except Exception as e:  # 捕获异常
                print(f"Error occurred: {e}. Retrying in 15 minutes...")
                time.sleep(900)  # 暂停 15 分钟 (900 秒)
                continue  # 继续重试
    return output

def Clean_code_fixed(begin,input_path):
    prompt_generate_answer_path = "./prompt/clean_fixcode.txt"
    data = getDictFromJsonl(input_path)
    clean_data = []
    for index, item in enumerate(data):
        if index < begin:
            continue
        
        while True:  # 使用循环来重试
            try:
                variables = get_variables(item, "clean_fixcode", None)
                system_txt, user_txt = extract_prompt(prompt_generate_answer_path, variables)
                str = getfromOpenAI(system_txt, user_txt, model)
                print(str)
                answer=safe_json_loads(str)
                item['origin_code_fixed'] = item["code_fixed"]
                item["code_fixed"] = answer["clean_function"]
                clean_data.append(item)
                break  # 如果成功，跳出循环
            except Exception as e:  # 捕获异常
                print(f"Error occurred: {e}. Retrying in 15 minutes...")
                time.sleep(900)  # 暂停 15 分钟 (900 秒)
                continue  # 继续重试
    return clean_data

def Run_script(begin,data):
    fail_output = []
    pass_output = []
    for index, item in enumerate(data):
        if index<begin:
            continue
        test_str(item['fixed_script'],f'./tmp/tmp.py')
        venv_path = env_path(item['import'],item['compare_version'])
        print("调用虚拟路径：",venv_path)
        m_str=py_run(venv_path,f'./tmp/tmp.py')
        item['fixed_message']=m_str
        if "error" in m_str:
            item['success_run']=0
            fail_output.append(item)
        else:
            item['success_run']=1
            pass_output.append(item)
    return pass_output,fail_output

def RE_Contrast_answer(begin,data):
    pass_num = 0
    output = []
    for index, item in enumerate(data):
        if index<begin:
            continue
        variables=get_variables(item,"contrast_answer" ,None)
        if variables['<RIGHT_ANSWER>']==variables['<RUN_ANSWER>']:
            item['re_run_answer']=1
            pass_num=pass_num+1
        else:
            item['re_run_answer']=0
        output.append(item)
    print(pass_num)
    return output

def AI_Contrast_answer(begin,input_path,output_path):
    prompt_contrast_answer_path="./prompt/judge_answer.txt"
    data = getDictFromJsonl(input_path)

    for index, item in enumerate(data):
        if index<begin:
            continue
        variables=get_variables(item,"contrast_answer" ,None)
        system_txt,user_txt=extract_prompt(prompt_contrast_answer_path,variables)
        str = getfromOpenAI(system_txt,user_txt,model)
        print(str)
        answer=safe_json_loads(str)
        item.update(answer)
        append_to_jsonl(output_path,[item])

# 将运行通过和不通过的合并
def Merge_RUN_NOTRUN(fail_data,pass_data):
    output=[]
    for _, item in enumerate(fail_data):
        output.append(item)
    for _,item in enumerate(pass_data):
        output.append(item)
    return output

# 将函数调用的和没有调用的合并
def Merge_RE_NotRE(fail_data,pass_data):
    output=[]
    for _, item in enumerate(fail_data):
        output.append(item)
    for _,item in enumerate(pass_data):
        output.append(item)

    return output

def parse_args():
    parser = argparse.ArgumentParser(description='模型评估参数解析器')
    
    # 添加必需的字符串参数
    parser.add_argument('--model_name', type=str, required=True,default='gpt-4o-mini',
                        help='使用的模型名称')
    parser.add_argument('--type', type=str, required=True,default='easy',
                        help='要检测的难度 (e.g., "easy", "hard")')
    parser.add_argument('--begin', type=int, required=False,default=0)
    
    
    return parser.parse_args()
def main(begin):
    args = parse_args()
    eval_model = args.model_name
    nandu = args.type
    begin = args.begin
    file_name=f"easy_eval.jsonl"if nandu == "easy" else "hard_eval.jsonl"
    file_holder=eval_model
    
    
    raw_data=os.path.join(f"./output/",file_holder,file_name)
    clean_data = Clean_code_fixed(begin,raw_data)
    pass_re_data,fail_re_data = RE_signature(file_name,clean_data)
    code_script = Generate_script(begin,pass_re_data)
    pass_run_data,fail_run_data = Run_script(begin,code_script)

    contrast_answer_data = RE_Contrast_answer(begin,pass_run_data)

    finally_merge_data = Merge_RUN_NOTRUN(fail_run_data,contrast_answer_data)
    finally_merge_data = Merge_RE_NotRE(fail_re_data,finally_merge_data)

    code_id_path = ""
    if "single" in file_name:
        code_id_path = "./eval_data/single_code_id.jsonl"
    elif "combine" in file_name:
        code_id_path = "./eval_data/combine_code_id.jsonl"


    pass_k = 1
    finally_merge_k_path = os.path.join(f"./output/",file_holder,f"pass_{pass_k}_{file_name}")
    finally_package_k_path = os.path.join(f"./output/",file_holder,f"package_{pass_k}_{file_name}")
    Random_code_id(code_id_path,finally_merge_data,pass_k,finally_merge_k_path,finally_package_k_path)

    pass_k = 5
    finally_merge_k_path = os.path.join(f"./output/",file_holder,f"pass_{pass_k}_{file_name}")
    finally_package_k_path = os.path.join(f"./output/",file_holder,f"package_{pass_k}_{file_name}")
    Random_code_id(code_id_path,finally_merge_data,pass_k,finally_merge_k_path,finally_package_k_path)

    # re_signature = 0 表示调用失败
    # success_run  = 0 表示编译运行失败
    # re_run_answer = 0 表示运行答案前后不一致
    acculate_key("re_signature",finally_merge_k_path)
    acculate_key("success_run",finally_merge_k_path)
    acculate_key("re_run_answer",finally_merge_k_path)
    acculate_result(finally_merge_k_path)


if __name__ == '__main__':
    begin=0
    main(begin)