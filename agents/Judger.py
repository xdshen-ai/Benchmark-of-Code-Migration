from utils import *
class Judger:
    def __init__(self, model,prompt_instruct_path,variables):
        self.model=model

        self.system_instruct,self.user_instruct=extract_prompt(prompt_instruct_path,variables)
        #print("judger's user instruct:",self.user_instruct)

    def judge(self):
        answer=None
        while answer==None:
            answer=getfromOpenAI(system=self.system_instruct,user=self.user_instruct,model=self.model)
            answer=safe_json_loads(answer)
        #print("judger's reason:",answer['reason'])
        return answer
         
        



        

        
