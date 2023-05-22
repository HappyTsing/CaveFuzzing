#!/usr/bin/env python3

import sys,os
import random
from pexpect import run
import configparser
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"config.ini")
config.read(config_path)
arithmetic_range = [int(i) for i in config["generation"]["arithmetic_range"].split(",")]
mutation_ratio = float(config["generation"]["mutation_ratio"])

# from pipes import quote

# read bytes from our valid JPEG and return them in a mutable bytearray 
def get_bytes(filename):

    f = open(filename, "rb").read()
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

def mutator(data):
    # 文件开头和结尾分别存在两个字节 的 SOI 和 EOI 标记，保持不动
    num_of_flips = int((len(data) - 4) * mutation_ratio)

    indexes = range(4, (len(data) - 4))

    chosen_indexes = []

    # iterate selecting indexes until we've hit our num_of_flips number
    counter = 0
    while counter < num_of_flips:
        chosen_indexes.append(random.choice(indexes))
        counter += 1
    print("Number of indexes chosen: " + str(len(chosen_indexes)))
    print("Indexes chosen: " + str(chosen_indexes))

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
    return data

# create new jpg with mutated data
def create_new(data):

    f = open("mutated.jpg", "wb+")
    f.write(data)
    f.close()

# def exif(counter,data):

#     command = "exif mutated.jpg -verbose"

#     out, returncode = run("sh -c " + quote(command), withexitstatus=1)

#     if b"Segmentation" in out:
#         f = open("crashes2/crash.{}.jpg".format(str(counter)), "ab+")
#         f.write(data)

#     if counter % 100 == 0:
#         print(counter, end="r")

if len(sys.argv) < 2:
    print("Usage: JPEGfuzz.py <valid_jpg>")

else:
    filename = sys.argv[1]
    counter = 0
    data = get_bytes(filename)
    mutated = mutator(data)
    create_new(mutated)
    
    
    # while counter < 100000:
    #     data = get_bytes(filename)
    #     functions = [0, 1]
    #     picked_function = random.choice(functions)
    #     if picked_function == 0:
    #         mutated = magic(data)
    #         create_new(mutated)
    #         exif(counter,mutated)
    #     else:
    #         mutated = bit_flip(data)
    #         create_new(mutated)
    #         exif(counter,mutated)

    #     counter += 1
