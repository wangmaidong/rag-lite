# 模拟装饰器
from time import sleep


def decorator1(func):
    sleep(10)
    print("执行 decorator1")  # 立即执行
    def wrapper1():
        print("调用 wrapper1")  # 调用时执行
        return func()
    return wrapper1

def decorator2(func):
    print("执行 decorator2")  # 立即执行
    def wrapper2():
        print("调用 wrapper2")  # 调用时执行
        return func()
    return wrapper2

def decorator3(func):
    print("执行 decorator3")  # 立即执行
    def wrapper3():
        print("调用 wrapper3")  # 调用时执行
        return func()
    return wrapper3

# 原始函数
def my_func():
    print("原始函数执行")

print("=== 开始应用装饰器 ===")
decorated = decorator1(decorator2(decorator3(my_func)))
print("=== 装饰器应用完成 ===")

print("\n=== 调用装饰后的函数 ===")
decorated()