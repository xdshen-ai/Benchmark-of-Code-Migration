## The paper is accepted to ACL-2025 Findings! Click here to see the [paper](https://arxiv.org/abs/2506.00894).



### Quick Start

Set the openai_key and base_url

```
export OPENAI_KEY="your_actual_openai_key"
export OPENAI_BASE_URL="your_actual_base_url"
```

You can adjust the parameters in run.sh to change the LLMs, language and difficulty of the assessment that you want to evaluate.

```
sh eval.sh
```

Then judging the output from the LLMs，to set the parameter --judge "true"

```
sh eval.sh
```

Install the sandbox environment for Sub-task 3.
```
sh requirements/env_setup.sh
```

Conduct the evaluation of Sub-task 3 only after the evaluations of Sub-task 1 and Sub-task 2 are completed (there is a strict upstream-downstream relationship). You can modify the "model_name" and "type" fields to change the model and adjust the task difficulty respectively.
```
sh eval.sh
```
