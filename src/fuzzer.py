#!/usr/bin/env python3

import os
import random
import configparser
import subprocess

config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config.ini")
config.read(config_path)
exif= config["tool"]["exif"]
exif_ASan= config["tool"]["exif_ASan"]

arithmetic_range = [int(i) for i in config["generation"]["arithmetic_range"].split(",")]
mutation_ratio = float(config["generation"]["mutation_ratio"])

round = int(config["evaluation"]["round"])
thread_count = int(config["evaluation"]["thread_count"])
seed = config["evaluation"]["seed"]
testcase_dir= config["evaluation"]["testcase_dir"]
result_dir= config["evaluation"]["result_dir"]

# read bytes from seed (valid exif)
def get_seed(seed_path):
    f = open(seed_path, "rb").read()
    return bytearray(f)

# 获取算数变异的 r
def get_range(alg,byte):
    
    min_r = arithmetic_range[0]
    
    if(alg == '+'):
        temp_max_r = 255-byte
    else:
        temp_max_r = byte
    
    max_r = min(temp_max_r,arithmetic_range[1])
    return min_r if min_r == max_r else random.choice(range(min_r,max_r))

def mutator(data,mutated_path):
    # 文件开头和结尾分别存在两个字节 的 SOI 和 EOI 标记，保持不动
    num_of_flips = int((len(data) - 4) * mutation_ratio)

    indexes = range(4, (len(data) - 4))

    chosen_indexes = []

    # iterate selecting indexes until we've hit our num_of_flips number
    counter = 0
    while counter < num_of_flips:
        chosen_indexes.append(random.choice(indexes))
        counter += 1
        
    # print("Number of indexes chosen: " + str(len(chosen_indexes)))
    # print("Indexes chosen: " + str(chosen_indexes))

    for x in chosen_indexes:
        byte = data[x]
        
        # 随机选择加减
        alg = ['+', '-']
        picked_alg = random.choice(alg)
        r = get_range(picked_alg,byte)
        
        # 若为0则只能+，若为255则只能-
        if(byte == 0):
            picked_alg = '+'
        elif(byte == 255):
            picked_alg = '-'
        
        if picked_alg == '+':
            mutated_byte = byte+r
        else:
            mutated_byte = byte-r
        data[x] = mutated_byte
    create_mutated(data,mutated_path)
    
# create new jpg with mutated data
def create_mutated(data,mutated_path):
    with open(mutated_path, "wb+") as f:
        f.write(data)

def delete_mutated(mutated_path):
    if os.path.exists(mutated_path):
        os.remove(mutated_path)
        
def triage(exec_out_bytes,count):
    result_path = "{}/mutated_{}".format(result_dir,count)
    tags=[]
    if b"memory leaks" in exec_out_bytes:
        tags.append("ML")
    if b"heap-buffer-overflow" in exec_out_bytes:
        tags.append("HBO")
    if b"stack-buffer-overflow" in exec_out_bytes:
        tags.append("SBO")
    if b"SEGV" in exec_out_bytes:
        if b"READ" in exec_out_bytes:
            tags.append("SEGV_READ")
        elif b"WRITE" in exec_out_bytes:
            tags.append("SEGV_WRITE")
        else:
            tags.append("SEGV_UNKNOW")
    if not tags:
        tags.append("UNKNOW")
    for tag in tags:
        result_path = "{}.{}".format(result_path,tag)
    result_path = "{}.log".format(result_path)
    
    with open(result_path,"wb+") as f:
        f.write(exec_out_bytes)
    

def evaluator(mutated_path,count):
    
    try:
        exec_out_bytes = subprocess.check_output([exif_ASan,mutated_path],stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        exec_out_bytes = e.output       # Output generated before error
     
    # 测试：多线程情况下图片竞争问题 FIX：图片名唯一
    # try:
    #     sha3 = subprocess.check_output(["shasum",file_path],stderr=subprocess.STDOUT)
    # except subprocess.CalledProcessError as e:
    #     sha3 = e.output       # Output generated before error
    # print(sha3)
    
    if b"Sanitizer" in exec_out_bytes:
        triage(exec_out_bytes,count)
    else:
        # 删除不报错的图片
        delete_mutated(mutated_path)
        
def run(count):
    mutated_path = "{}/mutated_{}.jpg".format(testcase_dir,count)
    data = get_seed(seed)
    mutator(data,mutated_path)
    evaluator(mutated_path,count)