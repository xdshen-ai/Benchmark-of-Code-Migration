from utils import *

class Replier:
    def __init__(self, model,prompt_instruct_path,variables):
        self.is_slm=False
        self.model=model
        pattern = r'slm'
        pattern_java=r'java'
        if re.search(pattern, prompt_instruct_path):
            self.is_slm=True
            
        self.system_instruct,self.user_instruct=extract_prompt(prompt_instruct_path,variables)
        
    def reply_java(self):
        dict_=None
        while dict_==None:
            str= getfromOpenAI(system=self.system_instruct,user=self.user_instruct,model=self.model,temperature=1.0)
            dict_=parserjava(str)

        return dict_

    def reply(self):
        answer=None
        while answer==None:
            answer=getfromOpenAI(system=self.system_instruct,user=self.user_instruct,model=self.model,temperature=0.8)
            print(answer)
            answer=safe_json_loads(answer,self.is_slm)
            

            
        return answer
        
        