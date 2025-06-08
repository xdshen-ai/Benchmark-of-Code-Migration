from utils import *
from agents.Replier import Replier
from agents.Judger import Judger
import random
import time
import pandas as pd
import argparse
'''注意这里同时生成ai_reason和code_fixed的字典可能只适合比较大的模型，有可能一些小模型直接生成文本
所以到时候会增加两个prompt，但是judger固定使用4o-mini，prompt不变'''

evaluate_comibine_llm_prompt='prompt/newevaluation/evaluate_combine_llm.txt'
evaluate_single_llm_prompt='prompt/newevaluation/evaluate_single_llm.txt'
evaluate_combine_slm_prompt='prompt/newevaluation/evaluate_combine_slm.txt'
evaluate_single_slm_prompt='prompt/newevaluation/evaluate_single_slm.txt'
evaluate_java_prompt='prompt/newevaluation/evaluation_java.txt'
judge_prompt_single="prompt/judge_agent.txt"
judge_prompt_combine="prompt/judge_agent_combine.txt"
judge_java_prompt="prompt/judge_agent_java.txt"
judge_model='gpt-4o-mini'

eval_models={"gpt-4o-mini":{"eval_model":'gpt-4o-mini',"model_dir":'gpt-4o-mini'},
             "gpt-4o":{"eval_model":'gpt-4o',"model_dir":'gpt-4o'},
             "gpt-3.5-turbo":{"eval_model":'gpt-3.5-turbo',"model_dir":'gpt-3.5-turbo'},
             "llama_8B":{"eval_model":'meta-llama/Meta-Llama-3.1-8B-Instruct',"model_dir":'llama_8B'},
             "llama_70B":{"eval_model":'meta-llama/Llama-3.3-70B-Instruct',"model_dir":'llama_70B'},
             "qwen_coder":{"eval_model":"Qwen/Qwen2.5-Coder-7B-Instruct","model_dir":"qwen_coder"},
             "deepseek-chat":{"eval_model":"deepseek-chat","model_dir":"deepseek-chat"},
             "code_llama":{"eval_model":"Xorbits/CodeLlama-34B-Instruct-GGUF","model_dir":"code_llama"},
}

def parse_args():
    parser = argparse.ArgumentParser(description='模型评估参数解析器')
    
    # 添加必需的字符串参数
    parser.add_argument('--model_name', type=str, required=True,default='gpt-4o-mini',
                        help='使用的模型名称')
    parser.add_argument('--lang', type=str, required=True,
                        help='要检测的语言 (e.g., "python", "java")')
    parser.add_argument('--type', type=str, required=True,default='easy',
                        help='要检测的难度 (e.g., "easy", "hard")')
    parser.add_argument('--judge', type=bool, required=False,default=False,
                        help='要检测的难度 (e.g., "easy", "hard")')
    parser.add_argument('--begin', type=int, required=False,default=0)
    
    
    return parser.parse_args()

args = parse_args()
eval_model = args.model_name
lang = args.lang
nandu = args.type
begin = args.begin
judge=args.judge

def check_filed(input_path):
    data=getDictFromJsonl(input_path)
    data=getDictFromJsonl(input_path)
    for index,item in enumerate(data):
        if 'code_fixed' not in item.keys() or 'ai_api_wrong' not in item.keys() or 'ai_api_change' not in item.keys():
            print(index)

def read_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    return data

def evaluate(input_path,output_path,eval_mode):
    data=getDictFromJsonl(input_path)
    record=[]
    #data=random.sample(data,10)

    prompt_path=''
    if eval_mode['model_type']=='llm':
        if eval_mode['api']=='hard':
            prompt_path=evaluate_comibine_llm_prompt
        else:
            prompt_path=evaluate_single_llm_prompt
    elif eval_mode['model_type']=='slm':
        if eval_mode['api']=='hard':
            prompt_path=evaluate_combine_slm_prompt
        else:
            prompt_path=evaluate_single_slm_prompt
    
    print(prompt_path)
    for index,item in enumerate(data):
        
        begin=0
        if index<begin:
            continue
        replier=Replier(model=eval_mode['eval_model'],prompt_instruct_path=prompt_path,variables=get_variables(item,'replier'))
        if index==begin:
            success=0
        else :
           success=0
        for i in range(success,5):
            while True:
                try:
                    print(index,i)
                    reply=replier.reply()
                    print(reply)
                    break
                except Exception as e:  # 捕获异常
                    print(f"Error occurred: {e}. Retrying in 10 minute...")
                    time.sleep(600)  # 暂停 1 分钟 (60 秒)
                    continue  # 继续重试
                
                
            # print(index,i)
            # reply=replier.reply()
            # print(reply)

            #reply中有ai_reason和code_fixed
            reply.update(item)
            append_to_jsonl(output_path,[reply])
            
        #record.append(reply)

    #append_to_jsonl(output_path,record)

def evaluate_java(input_path,output_path,eval_model):
    data=getDictFromJsonl(input_path)
    record=[]
    #data=random.sample(data,10)
    prompt_path=evaluate_java_prompt
    for index,item in enumerate(data):
        # if index<190:
        #     continue
        while True:
            try:  
                print(index)
                replier=Replier(model=eval_model,prompt_instruct_path=prompt_path,variables=get_variables(item,'replier','java'))
                reply=replier.reply_java()
                print(reply)
                #reply中有ai_reason和code_fixed
                reply.update(item)
                break
            except Exception as e:  # 捕获异常
                    print(f"Error occurred: {e}. Retrying in 10 minute...")
                    time.sleep(600)  # 暂停 1 分钟 (60 秒)
                    continue  # 继续重试
            
        append_to_jsonl(output_path,[reply])


def locate_judge_python(eval_file_path,locate_res_path,is_combine):
    data=getDictFromJsonl(eval_file_path)

    df=pd.DataFrame(data)
    filtered_df = df.drop_duplicates(subset=["code_id"])
    # 将结果转换回列表
    data = filtered_df.to_dict(orient="records")
        
    res_list=[]
    flex_pra=None
    prompt_path=judge_prompt_single
    if is_combine:
        flex_pra='combine'
        prompt_path=judge_prompt_combine

    #data=random.sample(data,5)
    for idx,item in enumerate(data):
        print(idx)
        judger=Judger(model=judge_model,prompt_instruct_path=prompt_path,variables=get_variables(item,'judger',flexible_para=flex_pra))
        judge=judger.judge()
        print(judge)       
        item.update(judge)
        res_list.append(item)
        
    append_to_jsonl(locate_res_path,res_list)

def locate_judge_java(eval_file_path,locate_res_path):
    data=getDictFromJsonl(eval_file_path)
    res_list=[]

    #data=random.sample(data,30)
    for idx,item in enumerate(data):
        print(idx)
        judger=Judger(model=judge_model,prompt_instruct_path=judge_java_prompt,variables=get_variables(item,'judger',flexible_para='java'))
        judge=judger.judge()
        print(judge)       
        item.update(judge)
        #append_to_jsonl([item])
        res_list.append(item)
        
    append_to_jsonl(locate_res_path,res_list)


def python_main():
    input_single_path="eval_data/easy_code.jsonl"
    input_combine_path="eval_data/hard_code.jsonl"
    if nandu=='easy':
        input_path=input_single_path
    else:
        input_path=input_combine_path
    output_dir="output/"
    
    #change the parameters here is OK
    eval_mode={'eval_model':eval_models[eval_model]['eval_model'],'model_type':'slm','api':nandu}
    eval_file_name=eval_mode['api']+'_eval.jsonl'
    output_dir+=eval_models[eval_model]['model_dir']+'/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path=os.path.join(output_dir,eval_file_name)
    evaluate(input_path,output_path,eval_mode)
    

    locate_res_path=output_dir+eval_mode['api']+'_judge.jsonl'
    locate_judge_python(output_path,locate_res_path,False)
    # print(calculate_accuracy(locate_res_path))
    
def python_judge():
    eval_mode={'eval_model':eval_models[eval_model]['eval_model'],'model_type':'slm','api':nandu}
    output_dir="output/"
    output_dir+=eval_models[eval_model]['model_dir']+'/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    eval_file_name=eval_mode['api']+'_eval.jsonl'
    output_path=os.path.join(output_dir,eval_file_name)
    locate_res_path=output_dir+eval_mode['api']+'_judge.jsonl'
    if nandu=='easy':
        locate_judge_python(output_path,locate_res_path,False)
    else:
        locate_judge_python(output_path,locate_res_path,True)
    
    

def java_main():
    input_path="eval_data/java_code.jsonl"
    
    output_dir="output/"
    output_dir=output_dir+eval_models[eval_model]['model_dir']+'/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_path=output_dir+'java_eval.jsonl'
    
    evaluate_java(input_path,output_path,eval_models[eval_model]['eval_model'])
    locate_res_path=output_dir+'/java_judge.jsonl'
    #locate_judge_java(output_path,locate_res_path)
    
def java_judge():
    input_path="eval_data/java_code.jsonl"
    output_dir="output/"
    output_dir=output_dir+eval_models[eval_model]['model_dir']+'/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_path=output_dir+'java_eval.jsonl'
    locate_res_path=output_dir+'/java_judge.jsonl'
    locate_judge_java(output_path,locate_res_path)

if __name__ == '__main__':
    if judge==False:
        if lang=='python':
            python_main()
        elif lang=='java':
            java_main()

    else:
        if lang=='python':
            python_judge()
        elif lang=='java':
            java_judge()

