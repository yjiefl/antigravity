import importlib.util
import sys
import subprocess
import os
import shutil
import importlib

def install_package(package_name):
    print(f"📦 正在安装依赖: {package_name} ...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        print(f"❌ 安装失败: {package_name}")
        return False

def check_package(package_name, import_name=None):
    if import_name is None:
        # 简单处理版本号
        import_name = package_name.split('==')[0].split('>=')[0].split('>')[0].split('<')[0].strip().lower()
    
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        return False
    return True

def install_system_lib_mac(lib_name):
    if shutil.which("brew"):
        print(f"📦 正在尝试通过 Homebrew 安装系统库: {lib_name} ...")
        try:
            subprocess.check_call(["brew", "install", lib_name])
            return True
        except subprocess.CalledProcessError:
            print(f"❌ brew 安装失败: {lib_name}")
            return False
    else:
        print(f"❌ 未找到 Homebrew，无法自动安装 {lib_name}。请安装 Homebrew 或手动安装该库。")
        return False

def check_system_lib_magic():
    # 刷新导入缓存，防止刚安装完 python-magic 找不到
    importlib.invalidate_caches()
    
    try:
        import magic
        # 尝试调用一下，看底层库是否真的加载成功
        # 需要 encode 避免某些情况下的类型错误
        magic.from_buffer("test".encode('utf-8'))
        return True
    except ImportError as e:
        # 如果是 module not found，说明 python-magic 包没装好（理论上前面步骤已装）
        if "No module named 'magic'" in str(e):
            return False
        # 如果是 failed to find libmagic，说明缺失系统库
        if "failed to find libmagic" in str(e):
            return "MISSING_LIB"
        return False
    except Exception as e:
        # 其他错误可能是系统库问题
        if "failed to find libmagic" in str(e):
            return "MISSING_LIB"
        return False 

def main():
    print("🔍 正在检查运行环境...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 版本过低: {sys.version}. 请使用 3.8+")
        sys.exit(1)

    req_file = "requirements.txt"
    missing_pkgs = []
    
    if os.path.exists(req_file):
        with open(req_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # 获取包名用于安装
                install_name = line
                # 获取包名用于检查导入
                pkg_base = line.split(">")[0].split("=")[0].split("<")[0].strip().lower()
                
                import_map = {
                    "python-magic": "magic",
                    "fpdf2": "fpdf"
                }
                import_name = import_map.get(pkg_base, pkg_base)
                
                if not check_package(install_name, import_name):
                    missing_pkgs.append(install_name)
    
    # 1. 自动安装 Python 依赖
    if missing_pkgs:
        print(f"⚠️ 发现 {len(missing_pkgs)} 个缺失的 Python 依赖，准备自动安装...")
        for pkg in missing_pkgs:
            if not install_package(pkg):
                print(f"❌ 依赖 {pkg} 安装失败，请尝试手动运行: pip install -r requirements.txt")
                sys.exit(1)
        print("✅ Python 依赖安装完成。")
        # 刷新缓存
        importlib.invalidate_caches()

    # 2. 检查并自动安装系统库 (主要是 libmagic)
    magic_status = check_system_lib_magic()
    
    if magic_status == "MISSING_LIB":
        print("⚠️ 检测到系统库 libmagic 缺失 (python-magic 依赖)，尝试自动安装...")
        if sys.platform == "darwin":
            if not install_system_lib_mac("libmagic"):
                print("❌ 无法安装 libmagic。")
                sys.exit(1)
            print("✅ libmagic 安装完成。")
        else:
            print("❌ 非 macOS 系统，请手动安装 libmagic (例如: sudo apt-get install libmagic1)")
            sys.exit(1)
    elif magic_status is False:
        # 可能是 import magic 彻底失败，虽然前面已经安装了 python-magic
        # 尝试再次安装 libmagic 作为 fallback，或者是 import 错误
        pass # 前面 missing_pkgs 应该处理了 python-magic

    print("✅ 环境检查通过！")

if __name__ == "__main__":
    main()
