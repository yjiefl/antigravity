import importlib.util
import sys
import subprocess
import os

def check_package(package_name, import_name=None):
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        print(f"❌ 缺少 Python 依赖: {package_name}")
        return False
    return True

def check_system_lib(lib_name):
    # 目前主要检查 libmagic (针对 python-magic)
    if lib_name == "libmagic":
        try:
            import magic
            # 尝试调用一下，看底层库是否真的加载成功
            magic.from_buffer("test")
            return True
        except Exception as e:
            print(f"❌ 系统库 libmagic 加载失败。在 macOS 上请执行: brew install libmagic")
            return False
    return True

def main():
    print("🔍 正在检查运行环境...")
    
    # 1. 检查 Python 版本
    if sys.version_info < (3, 8):
        print(f"❌ Python 版本过低: {sys.version}. 请使用 3.8+")
        sys.exit(1)

    # 2. 从 requirements.txt 读取并检查
    req_file = "requirements.txt"
    all_ok = True
    
    if os.path.exists(req_file):
        with open(req_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # 处理版本号，如 flask>=2.0
                pkg = line.split(">")[0].split("=")[0].split("<")[0].strip().lower()
                
                # 某些包的导入名与安装名不同
                import_map = {
                    "python-magic": "magic",
                    "fpdf2": "fpdf"
                }
                
                if not check_package(line, import_map.get(pkg, pkg)):
                    all_ok = False
    
    # 3. 特殊系统库检查
    if not check_system_lib("libmagic"):
        all_ok = False

    if not all_ok:
        print("\n💡 建议运行: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ 环境检查通过！")

if __name__ == "__main__":
    main()
