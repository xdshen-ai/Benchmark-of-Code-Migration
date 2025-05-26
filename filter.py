from  utils import *
import re
import time
import os

model='gpt-4o-mini'

def RE_signature(input_path,pass_output_path,fail_output_path):
    if "combine" in input_path:
        data = getDictFromJsonl(input_path)
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
        rewrite_jsonl(pass_output_path,pass_output)
        rewrite_jsonl(fail_output_path,fail_output)
    else:
        data = getDictFromJsonl(input_path)
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
        rewrite_jsonl(pass_output_path,pass_output)
        rewrite_jsonl(fail_output_path,fail_output)

def Generate_script(begin, input_path, output_path):
    prompt_generate_answer_path = "./prompt/generate_answer.txt"
    data = getDictFromJsonl(input_path)
    
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
                append_to_jsonl(output_path, [item])
                break  # 如果成功，跳出循环
            except Exception as e:  # 捕获异常
                print(f"Error occurred: {e}. Retrying in 15 minutes...")
                time.sleep(900)  # 暂停 15 分钟 (900 秒)
                continue  # 继续重试

def Clean_code_fixed(begin,input_path,output_path):
    prompt_generate_answer_path = "./prompt/clean_fixcode.txt"
    data = getDictFromJsonl(input_path)
    
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
                append_to_jsonl(output_path, [item])
                break  # 如果成功，跳出循环
            except Exception as e:  # 捕获异常
                print(f"Error occurred: {e}. Retrying in 15 minutes...")
                time.sleep(900)  # 暂停 15 分钟 (900 秒)
                continue  # 继续重试

def Run_script(begin,input_path,pass_output_path,fail_output_path):
    data = getDictFromJsonl(input_path)

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
            append_to_jsonl(fail_output_path,[item])
        else:
            item['success_run']=1
            append_to_jsonl(pass_output_path,[item])

def RE_Contrast_answer(begin,input_path,output_path):
    data = getDictFromJsonl(input_path)
    pass_num = 0
    for index, item in enumerate(data):
        if index<begin:
            continue
        variables=get_variables(item,"contrast_answer" ,None)
        if variables['<RIGHT_ANSWER>']==variables['<RUN_ANSWER>']:
            item['re_run_answer']=1
            pass_num=pass_num+1
        else:
            item['re_run_answer']=0
        append_to_jsonl(output_path,[item])
    print(pass_num)

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
def Merge_RUN_NOTRUN(fail_run_path,pass_run_path,output_path):
    fail_data = getDictFromJsonl(fail_run_path)
    pass_data = getDictFromJsonl(pass_run_path)
    output=[]

    for _, item in enumerate(fail_data):
        output.append(item)
    for _,item in enumerate(pass_data):
        output.append(item)
    rewrite_jsonl(output_path,output)

# 将函数调用的和没有调用的合并
def Merge_RE_NotRE(fail_re_path,pass_re_path,output_path):
    fail_data = getDictFromJsonl(fail_re_path)
    pass_data = getDictFromJsonl(pass_re_path)
    output=[]

    for _, item in enumerate(fail_data):
        output.append(item)
    for _,item in enumerate(pass_data):
        output.append(item)

    rewrite_jsonl(output_path,output)


def main(begin):
    file_name=f"single_eval.jsonl"
    # llama_8B
    file_holder=f"code_llama"
    
    
    raw_data=os.path.join(f"./newdata/raw/",file_holder,file_name)
    clean_data=os.path.join(f"./newdata/clean_fixcode/",file_holder,file_name)
    pass_re_path=os.path.join(f"./newdata/middle/pass_re/",file_holder,file_name)
    fail_re_path=os.path.join(f"./newdata/middle/fail_re/",file_holder,file_name)

    code_script=os.path.join(f"./newdata/middle/fixed_code_script/",file_holder,file_name)

    pass_run_path=os.path.join(f"./newdata/middle/pass_run/",file_holder,file_name)
    fail_run_path=os.path.join(f"./newdata/middle/fail_run/",file_holder,file_name)

    contrast_answer_path=os.path.join(f"./newdata/filter/",file_holder,file_name)

    finally_merge_path = os.path.join(f"./newdata/finally_result/",file_holder,file_name)

    # Clean_code_fixed(begin,raw_data,clean_data)
    # RE_signature(clean_data,pass_re_path,fail_re_path)
    # Generate_script(begin,pass_re_path,code_script)
    # Run_script(begin,code_script,pass_run_path,fail_run_path)

    # RE_Contrast_answer(begin,pass_run_path,contrast_answer_path)

    # Merge_RUN_NOTRUN(fail_run_path,contrast_answer_path,finally_merge_path)
    # Merge_RE_NotRE(fail_re_path,finally_merge_path,finally_merge_path)

    code_id_path = ""
    if "single" in file_name:
        code_id_path = "./newdata/single_code_id.jsonl"
    elif "combine" in file_name:
        code_id_path = "./newdata/combine_code_id.jsonl"

    pass_k = 5
    finally_merge_k_path = os.path.join(f"./newdata/finally_result/",file_holder,f"pass_{pass_k}_{file_name}")
    finally_package_k_path = os.path.join(f"./newdata/finally_result/",file_holder,f"package_{pass_k}_{file_name}")
    # 内部有一些细节要改！！
    Random_code_id(code_id_path,finally_merge_path,pass_k,finally_merge_k_path,finally_package_k_path)
    # Random_code_id2(code_id_path,finally_merge_path,pass_k,finally_merge_k_path,finally_package_k_path)
    # Random_code_id3(code_id_path,finally_merge_path,pass_k,35,65,finally_merge_k_path,finally_package_k_path)
    # Random_code_id4(code_id_path,finally_merge_path,pass_k,7,8,finally_merge_k_path,finally_package_k_path)

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