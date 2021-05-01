import random

def get_username(mobile):
    profix = ['haha','heihei','hehe','xixi','huhu','huahua','hihi']
    return random.choice(profix) + '_' + mobile[2:8]