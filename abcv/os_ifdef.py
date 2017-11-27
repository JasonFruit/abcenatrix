import os, platform

# 'posix', 'nt', 'os2', 'ce', 'java', 'riscos'

def os_name():
    if os.name == "posix":
        pf = platform.system().lower()
        if "bsd" in pf:
            return "BSD"
        elif "darwin" in pf:
            return "OS X"
        elif "linux" in pf:
            return "Linux"
        else:
            return "Other posix"
    elif os.name == "nt":
        return "Windows"

def is_linux():
    return os_name == "Linux"
