from pathlib import Path
import os

# 获取当前工作目录
current_dir = Path.cwd()
print(f"当前工作目录 (pathlib): {current_dir}")

# 测试各种路径
test_paths = [
    "/a/b/c/test.txt",
    "test.txt",
    "./test.txt",
    "../test.txt",
    "subfolder/test.txt",
]

for path_str in test_paths:
    path = Path(path_str)
    print(f"\n原始路径: '{path_str}'")

    # 如果是相对路径，Python会基于当前目录解析
    if path.is_absolute():
        print(f"  这是一个绝对路径")
        print(f"  Python会直接查找: {path}")
    else:
        print(f"  这是一个相对路径")
        print(f"  Python会基于 '{current_dir}' 查找")
        print(f"  实际查找路径: {current_dir / path}")

    # 转换为绝对路径
    abs_path = path.absolute()
    print(f"  绝对路径: {abs_path}")