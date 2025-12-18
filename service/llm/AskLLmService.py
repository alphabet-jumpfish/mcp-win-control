from transformers import AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer
from threading import Thread
from typing import Iterator
import torch


class AskLLM:

    def __init__(self, model_path):
        ## 分词等内容
        self.model_path = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            device_map="auto",
            torch_dtype=torch.bfloat16
        )

    def chat(self, text):
        messages = text
        print("=" + "打印请求参数" + "=" * 20)
        print(f"{text}")
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=512
        )
        output = self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        print("=" + "打印回复参数" + "=" * 20)
        print(output)
        return output

    def chat_stream(
            self,
            text: str,
            max_new_tokens: int = 512,
            temperature: float = 0.7,
            top_k: int = 50,
            top_p: float = 0.9
    ) -> Iterator[str]:
        """
        流式输出聊天方法
        
        Args:
            text: 输入文本
            max_new_tokens: 最大生成token数
            temperature: 温度参数，控制随机性
            top_k: top-k采样
            top_p: top-p采样
            
        Yields:
            生成的文本片段（逐个token或词）
        """
        print("=" + "打印请求参数（流式）" + "=" * 20)
        print(f"{text}")

        # 准备输入
        messages = text
        formatted_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([formatted_text], return_tensors="pt").to(self.model.device)

        # 创建流式输出器
        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,  # 跳过提示部分，只输出生成的内容
            skip_special_tokens=True
        )

        # 生成参数
        generation_kwargs = {
            **model_inputs,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
            "streamer": streamer,
            "do_sample": True if temperature > 0 else False
        }

        # 在单独线程中运行生成
        generation_thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        generation_thread.start()

        # 流式输出生成的文本
        generated_text = ""
        for new_text in streamer:
            generated_text += new_text
            yield new_text

        generation_thread.join()
        print("=" + "[ASK_LLM]打印回复参数（流式）" + "=" * 20)
        print(generated_text)
