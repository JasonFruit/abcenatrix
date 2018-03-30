import os
import subprocess

commands = {"abcm2ps": "",
            "abc2midi": "",
            "abc2abc": "",
            "gs": ""}

def default_tool_path(command):
    """Try to find the tool in the PATH"""
    if os.name == "nt":
        sh_cmd = command
    elif os.name == "posix":
        sh_cmd = "which %s" % command
        
    child = subprocess.Popen(sh_cmd, shell=True, stdout=subprocess.PIPE)
    output, _ = child.communicate()
    
    if command in output.decode("utf-8"):
        return (command == sh_cmd) and command or output
    
    return None
