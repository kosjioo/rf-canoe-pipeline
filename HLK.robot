# *** Settings ***
# #Library    C:\Users\admin\Desktop\Home\24_Devops\07_CANoeRF_Frozen\01-keywords\CanoeSync.py
# Library    ${BASE_DIR}/01-keywords/CanoeSync.py
# Library    OperatingSystem
# # Suite Setup    Initialize Suite
# Documentation    HLK Test Suite
# Suite Setup     Log    Starting CANoe test suite
# Suite Teardown  HLK Stop Measurement
# Test Timeout    5 minutes

# *** Variables ***
# ${BASE_DIR}       ${CURDIR}/..                                                                                 # 项目根目录，基于当前目录的上级目录
# ${CONFIG_PATH}    ${BASE_DIR}/02_canoe_tc/PythonBasic.cfg                                                      # CANoe 配置文件路径
# ${TEST_MODULE_PATH}  ${BASE_DIR}/02_canoe_tc/TestEnvironments/Test Environment.tse                         # xxx TEST MODULES 路径 xxx  
# # ${TEST_CONFIG_NAME}    PythonBasicTest                                                                         # 测试配置名称
# # ${TEST_UNIT_PATH}      ${BASE_DIR}/CANoeConfig/TestConfiguration/EasyTest/EasyTest.vtuexe                      # TEST UNITS 测试单元文件路径
# #${LOG_FILE}       ${BASE_DIR}/04_logs/test_output.log                                                          # 日志文件路径

# *** Test Cases ***
# Execute CANoe Tests
#     [Documentation]    运行 CANoe 测试单元（.vtuexe 文件）并验证结果
#     HLK Load Configuration          ${CONFIG_PATH}
#     Sleep    3s  

#     HLK Reset CANoe Environment    # 新增重置步骤
#     Sleep    2s  

#     # HLK Stop Measurement    # 确保测量已停止
#     # Sleep    1s

#     HLK Load Test Modules       ${TEST_MODULE_PATH}  
#     Sleep    1s  
#    # HLK Load Test Configuration     ${TEST_CONFIG_NAME}    ${TEST_UNIT_PATH}  # 使用变量传递位
#     HLK Start Measurement
#     Sleep    5s  
#    # HLK Run Test Configurations
#     HLK Run Test Modules 
#     Sleep    15s  
#     HLK Verify Test Execution
#     #HLK Stop Measurement

# *** Keywords ***
# HLK Reset CANoe Environment
#     [Documentation]    Reset CANoe test environment
#     CanoeSync.reset_environment    # 假设有 reset_environment 方法
#     Log    CANoe environment reset

# HLK Load Configuration 
#     [Arguments]    ${cfg_path}     #定义了一个参数 ${cfg_path}
#     [Documentation]    打开CANoe工程     #Load CANoe configuration file
#     CanoeSync.load_configuration    ${cfg_path}
#     Log    Loaded configuration:${cfg_path}

# HLK Load Test Modules 
#     [Documentation]    test module set up
#     [Arguments]    ${tse_path}    
#     CanoeSync.load_test_setup     ${tse_path}
#     Log    Loaded Test modules via CANoe 

# HLK Load Test Setup
#     [Arguments]    ${path}
#     [Documentation]    Load test environment setup
#     load_test_setup   ${path}
#     Log    Loaded test setup: ${path}

# HLK Load Test Configuration
#     [Arguments]    ${name}    ${unit}
#     [Documentation]    Load test configuration with test unit
#     load_test_configuration    ${name}    ${unit}
#     Log    Loaded test configuration: ${name}

# HLK Start Measurement
#     [Documentation]    Start CANoe measurement
#     start_measurement
#     Log    Measurement started

# HLK Run Test Modules
#     [Documentation]    Run all test modules
#     run_test_module
#     Log    Executed test modules

# HLK Run Test Configurations
#     [Documentation]    Run all test configurations
#     run_test_configs
#     Log    Executed test configurations

# HLK Verify Test Execution
#     [Documentation]    Verify test execution via log file
#     verify_test_execution      
    
#     ${output}=    Get File    ${LOG_FILE}
#     Should Contain    ${output}    measurement started
#     Should Contain    ${output}    measurement stopped
#     Log    Test execution verified

# HLK Stop Measurement
#     [Documentation]    Stop CANoe measurement
#     Stop Measurement
#     Log    Measurement stopped


# HLK Load load_configuration
#     [Arguments]    ${arg1}
#     # TODO: implement keyword "Load load_configuration".
#     Fail    Not Implemented



# # Clear Caches and Restart
# #     ${status}    Run Keyword And Return Status    Remove Files    output.xml    log.html    report.html
# #     Run Keyword If    '${status}' == 'False'    Log    无法删除文件，可能被占用，请手动检查。
# #     Remove Directory    __pycache__    recursive=True
# #     Log    缓存清理完成。

# # Initialize Suite
# #     Clear Caches and Restart
# #     Log    Starting CANoe test suite
# #     Sleep    2s




*** Settings ***
Library    ${CURDIR}${/}01-keywords${/}CanoeSync.py
Library    OperatingSystem
Documentation    HLK Test Suite - CANoe Automated Tests
Suite Setup       Log    Starting CANoe Test Suite
Suite Teardown    Run Keywords    HLK Stop Measurement
...               AND              Log    Test Suite Completed
Test Timeout      5 minutes

*** Variables ***
${BASE_DIR}           ${CURDIR}
${CONFIG_PATH}        ${BASE_DIR}${/}02_canoe_tc${/}PythonBasic.cfg
${TEST_MODULE_PATH}   ${BASE_DIR}${/}02_canoe_tc${/}TestEnvironments${/}Test Environment.tse
${LOG_FILE}           ${BASE_DIR}${/}04_logs${/}test_output.log
${TEST_TIMEOUT}       5 minutes

*** Test Cases ***
Execute CANoe Tests
    [Documentation]    Main test case for CANoe automation
    HLK Load Configuration    ${CONFIG_PATH}
    Sleep    3s
    HLK Reset CANoe Environment
    Sleep    2s
    HLK Load Test Modules     ${TEST_MODULE_PATH}
    Sleep    1s
    HLK Start Measurement
    Sleep    5s
    HLK Run Test Modules
    Sleep    15s
    HLK Verify Test Execution

*** Keywords ***
HLK Reset CANoe Environment
    [Documentation]    Resets CANoe test environment
    CanoeSync.reset_environment
    Log    CANoe environment reset completed

HLK Load Configuration
    [Arguments]    ${cfg_path}
    [Documentation]    Loads CANoe configuration file
    CanoeSync.load_configuration    ${cfg_path}
    Log    Loaded configuration: ${cfg_path}

HLK Load Test Modules
    [Arguments]    ${tse_path}
    [Documentation]    Loads test modules into CANoe
    CanoeSync.load_test_setup    ${tse_path}
    Log    Test modules loaded: ${tse_path}

HLK Start Measurement
    [Documentation]    Starts CANoe measurement
    CanoeSync.start_measurement
    Log    Measurement started

HLK Run Test Modules
    [Documentation]    Executes all loaded test modules
    CanoeSync.run_test_module
    Log    Test modules execution started

HLK Verify Test Execution
    [Documentation]    Verifies test results
    ${output}=    Get File    ${LOG_FILE}
    Should Contain    ${output}    measurement started
    Should Contain    ${output}    measurement stopped
    Log    Test execution verified

HLK Stop Measurement
    [Documentation]    Stops CANoe measurement
    CanoeSync.stop_measurement
    Log    Measurement stopped