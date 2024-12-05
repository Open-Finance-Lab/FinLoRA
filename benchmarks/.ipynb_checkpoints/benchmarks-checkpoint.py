from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel, get_peft_model, LoraConfig, TaskType  # 0.4.0
import torch
import argparse


from fpb import test_fpb, test_fpb_mlt
from fiqa import test_fiqa, test_fiqa_mlt 
from tfns import test_tfns
from nwgi import test_nwgi
from headline import test_headline
from ner import test_ner
# from convfinqa import test_convfinqa
from fineval import test_fineval
from finred import test_re


import sys
sys.path.append('../')
from utils import *


def main(args):
    # if args.from_remote:
    #     model_name = parse_model_name(args.base_model, args.from_remote)
    # else:
    #     model_name = '../' + parse_model_name(args.base_model)

    model_name = args.base_model
        
    bnb_config = BitsAndBytesConfig(
        # load_in_4bit=args.quant_bits == 4,  # Load in 4-bit if quant_bits is 4
        load_in_8bit=args.quant_bits == 8,  # Load in 8-bit if quant_bits is 8
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, 
        # quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,

    )

    model.model_parallel = True

    tokenizer = AutoTokenizer.from_pretrained(model_name,     
        torch_dtype=torch.float16,
        trust_remote_code=True,
        device_map="auto"
    )
    
    # tokenizer.pad_token_id = tokenizer.eos_token_id

    tokenizer.padding_side = "left"
    if args.base_model == 'qwen':
        tokenizer.eos_token_id = tokenizer.convert_tokens_to_ids('<|endoftext|>')
        tokenizer.pad_token_id = tokenizer.convert_tokens_to_ids('<|extra_0|>')

    tokenizer.pad_token = tokenizer.eos_token
    # if not tokenizer.pad_token or tokenizer.pad_token_id == tokenizer.eos_token_id:
    #     tokenizer.add_special_tokens({'pad_token': '[PAD]'})
    #     model.resize_token_embeddings(len(tokenizer))

    print(f'pad: {tokenizer.pad_token_id}, eos: {tokenizer.eos_token_id}')
    # model.generation_config.pad_token_id = tokenizer.pad_token_id

    if args.peft_model != "":
        model = PeftModel.from_pretrained(model, args.peft_model)
    else:
        model.half()
        
    model = model.eval()
    model.generation_config.pad_token_id = tokenizer.pad_token_id

    with torch.no_grad():
        for data in args.dataset.split(','):
            if data == 'fpb':
                test_fpb(args, model, tokenizer)
            elif data == 'fpb_mlt':
                test_fpb_mlt(args, model, tokenizer)
            elif data == 'fiqa':
                test_fiqa(args, model, tokenizer)
            elif data == 'fiqa_mlt':
                test_fiqa_mlt(args, model, tokenizer)
            elif data == 'tfns':
                test_tfns(args, model, tokenizer)
            elif data == 'nwgi':
                test_nwgi(args, model, tokenizer)
            elif data == 'headline':
                test_headline(args, model, tokenizer)
            elif data == 'ner':
                test_ner(args, model, tokenizer)
            elif data == 'fineval':
                test_fineval(args, model, tokenizer)
            elif data == 're':
                test_re(args, model, tokenizer)
            else:
                raise ValueError('undefined dataset.')
    
    print('Evaluation Ends.')
        


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=str)
    parser.add_argument("--base_model", required=True, type=str)
    parser.add_argument("--peft_model", required=False, default="", type=str)
    parser.add_argument("--max_length", default=512, type=int)
    parser.add_argument("--batch_size", default=8, type=int, help="The train batch size per device")
    parser.add_argument("--instruct_template", default='default')
    parser.add_argument("--from_remote", default=False, type=bool)  
    parser.add_argument("--quant_bits", default=8, type=int)

    args = parser.parse_args()
    
    print(args.base_model)
    print(args.peft_model)
    
    main(args)
