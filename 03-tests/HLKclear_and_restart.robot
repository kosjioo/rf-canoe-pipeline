*** Settings ***
Library    OperatingSystem

*** Test Cases ***
Clear Caches and Restart
    ${status}    Run Keyword And Return Status    Remove Files    output.xml    log.html    report.html
    Run Keyword If    '${status}' == 'False'    Log    无法删除文件，可能被占用，请手动检查。
    Remove Directory    __pycache__    recursive=True
    Log    缓存清理完成。
    # 添加重启CANoe的逻辑（如果需要）