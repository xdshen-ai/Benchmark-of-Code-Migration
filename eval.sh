# 评估子任务1和子任务2
python run.py --lang "java"  --model_name "gpt-4o-mini" --type "easy" --judge false

# 评估子任务3，目前只支持python语言
python filter.py  --model_name "gpt-4o-mini" --type "easy" 