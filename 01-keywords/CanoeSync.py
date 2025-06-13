import time, os, msvcrt, pythoncom
from win32com.client import *
from win32com.client.connect import *
from robot.api.deco import keyword
from datetime import datetime


#保持 GUI 响应或处理 COM 事件的 Python 脚本
def DoEvents():
    pythoncom.PumpWaitingMessages()
    time.sleep(.1)

#等待某个事件或状态（如 COM 对象就绪）时，保持 GUI 或进程不被阻塞
def DoEventsUntil(cond):
    while not cond():
        DoEvents()

#与 DoEvents 类似，但允许自定义总等待时间，用于需要处理消息循环并延迟的场景，如 COM 交互或 GUI 程序中
def waitsleep(sleeptime):
    t = 0
    while t < sleeptime:
        pythoncom.PumpWaitingMessages()
        time.sleep(1)
        t += 1

class CanoeSync(object):
    """Wrapper class for CANoe Application object"""
    ROBOT_LIBRARY_SCOPE = 'GLOBAL' #Robot Framework
    Started = False
    Stopped = False
    ConfigPath = ""
    #ConfigPath = "C:/Users/admin/Desktop/Home/24_Devops/05_RF_CANoe_v2/CANoeConfig/PythonBasic.cfg"     
    #硬编码CANoe配置文件路径，避免在Robot Framework中重复定义。

    def __init__(self):
        app = DispatchEx('CANoe.Application')    
        ver = app.Version
        print('Loaded CANoe version ', 
            ver.major, '.', 
            ver.minor, '.', 
            ver.Build, '...', sep='')
        self.App = app
        self.Measurement = app.Measurement
        WithEvents(self.App, CanoeApplicationEvents)
        WithEvents(self.App.Measurement, CanoeMeasurementEvents)

    def Running(self):
        return self.Measurement.Running

    def WaitForStart(self):
        return DoEventsUntil(lambda: CanoeSync.Started)

    def WaitForStop(self):
        return DoEventsUntil(lambda: CanoeSync.Stopped)

#_internal_load_configuration方法加载指定 CANoe 配置文件，验证路径，打开配置，并初始化相关属性。
    def _internal_load_configuration(self, cfgPath):
        self.App.Configuration.Modified = False
        cfg = os.path.abspath(cfgPath)
        if not os.path.exists(cfg):
            raise FileNotFoundError(f"Configuration file not found: {cfg}")
        print('Opening: ', cfg)
        self.ConfigPath = os.path.dirname(cfg)
        self.App.Open(cfg)
        self.Configuration = self.App.Configuration
        self.TestConfigs = []
        self.TestModules = [] 


#testModule-->加载tse文件
    def _internal_load_test_setup(self, testsetup):
        """Loads and sets up a CANoe test environment from a .tse file."""
        try:
            self.TestSetup = self.App.Configuration.TestSetup
            if not self.TestSetup:
                raise RuntimeError("Failed to access CANoe TestSetup")
            print(f"TestSetup acquired: {self.TestSetup}")
            while self.TestSetup.TestEnvironments.Count > 0:
                try:
                    self.TestSetup.TestEnvironments.Remove(0)
                    print("Removed existing test environment")
                except pythoncom.com_error as e:
                    print(f"Error removing test environment: {e}")
                    break
            path = os.path.abspath(testsetup)
            print(f"Loading test environment from: {path}")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Test setup file not found: {path}")
            testenv = self.TestSetup.TestEnvironments.Add(path)
            testenv = CastTo(testenv, "ITestEnvironment2")
            self.TraverseTestItem(testenv, lambda tm: self.TestModules.append(CanoeTestModule(tm)))
            print("Test environment loaded successfully")
        except pythoncom.com_error as e:
            print(f"COM Error in _internal_load_test_setup: {e.excepinfo[2]}")
            raise
# testModule-->运行tse/testcase，直到结束
    def _internal_run_TestModules(self):
        """ starts all test modules and waits for all of them to finish"""
        try:
            for tm in self.TestModules:
                if hasattr(tm.tm, 'Enabled') and tm.tm.Enabled:
                    tm.tm.Start()
            while not all([not hasattr(tm.tm, 'Enabled') or not tm.tm.Enabled or tm.IsDone() for tm in self.TestModules]):
                DoEvents()
        except pythoncom.com_error as e:
            print(f"COM Error in TestModules: {e}")
# testModule-->
# TraverseTestItem --> 用于递归处理模块和文件夹的树状结构 
    def TraverseTestItem(self, parent, testf):
        for test in parent.TestModules: 
            testf(test)
        for folder in parent.Folders: 
            self.TraverseTestItem(folder, testf)



#testunits-->加载并配置 CANoe 的测试单元（.vtuexe 文件）。
    def _internal_load_test_configuration(self, testcfgname, testunits):
        tc = self.App.Configuration.TestConfigurations.Add()
        tc.Name = testcfgname
        tus = CastTo(tc.TestUnits, "ITestUnits2")
        for tu in testunits:
            tu_path = os.path.abspath(tu)
            if not os.path.exists(tu_path):
                raise FileNotFoundError(f"Test unit file not found: {tu_path}")
            tus.Add(tu_path)
        self.TestConfigs.append(CanoeTestConfiguration(tc))
#testunits-->运行.vtuexe/testcase，直到结束
    def _internal_run_test_configs(self):
        for tc in self.TestConfigs:
            tc.Start()
        while not all([not tc.Enabled or tc.IsDone() for tc in self.TestConfigs]):
            DoEvents()


    def Start(self): 
        if not self.Running():
            self.Measurement.Start()
            self.WaitForStart()

    def Stop(self):
        if self.Running():
            self.Measurement.Stop()
            self.WaitForStop()


    # --------------------------------------------------------------------------
    # ------------------------ Robot Framework Keywords ------------------------
    # --------------------------------------------------------------------------  
    
    # @keyword("load_configuration")
    # def load_configuration(self, cfg_path):
    #     """加载 CANoe 配置文件（.cfg 文件）"""
    #     self._internal_load_configuration(cfg_path)  
    #     log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
    #     os.makedirs(os.path.dirname(log_file), exist_ok=True)  # 创建日志目录（如果不存在），确保可以写入日志
    #     with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
    #         f.write(f'Opening: {cfg_path}\n')  # 记录加载的配置文件路径到日志
    @keyword("load_configuration")
    def load_configuration(self, cfg_path):
        """Load a CANoe configuration file (.cfg file)"""
        self._internal_load_configuration(cfg_path)
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f'--------------------------------------------------------------------------\n')
            f.write(f'--------------------python as LLK for Robotframework----------------------\n')
            f.write(f'--------------------------------------------------------------------------\n')
            f.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Opening: {cfg_path}\n')
            #f.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Configuration loaded successfully\n')


   
    # @keyword("reset_environment")
    # def reset_environment(self):
    #     """Reset CANoe test environment (clear all loaded .tse files)"""
    #     self.TestSetup = self.App.Configuration.TestSetup
    #     try:
    #         while self.TestSetup.TestEnvironments.Count > 0:
    #             self.TestSetup.TestEnvironments.Remove(0)
    #             print("[INFO] Removed one test environment.")
    #         print("[INFO] All test environments removed.")
    #     except pythoncom.com_error as e:
    #         print(f"[ERROR] Failed to remove test environment: {e}")
    @keyword("reset_environment")
    def reset_environment(self):
        """Reset CANoe test environment (clear all loaded .tse files)"""
        self.TestSetup = self.App.Configuration.TestSetup
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                while self.TestSetup.TestEnvironments.Count > 0:
                    self.TestSetup.TestEnvironments.Remove(0)
                    f.write("[INFO] Removed one test environment.\n")
                f.write("[INFO] All test environments removed.\n")
        except pythoncom.com_error as e:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[ERROR] Failed to remove test environment: {e}\n")
            raise RuntimeError(f"COM Error in reset_environment: {e.excepinfo[2]}")




# TEST MODULES .tse
    @keyword("load_test_setup")  
    def load_test_setup(self, testsetup):
        """Load a CANoe test module (.tse file) to configure the test environment"""
        self._internal_load_test_setup(testsetup) 
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  
        with open(log_file, 'a', encoding='utf-8') as f:  
            f.write(f'Loading test setup: {testsetup}\n')  
#testmodule
    @keyword("run_test_module")
    def run_test_modules(self):
        """Run all loaded CANoe test modules (.tse files)"""
        self._internal_run_TestModules()
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write('Test modules started\n')




# Test Units .vtuexe
#.vtuexe的代码，后面具体用的时候，可能还需要优化，所哟这里的中文注释没有删除；
# 20250613
    @keyword("load_test_configuration")
    def load_test_configuration(self, testcfgname, testunits):
        """Load a CANoe test configuration and test units (.vtuexe files)"""
        self._internal_load_test_configuration(testcfgname, [testunits])  # 调用 CANoe 内部方法加载测试配置和测试单元（.vtuexe 文件）
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
        with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
            f.write(f'Loading test configuration: {testcfgname} with unit {testunits}\n')  # 记录测试配置名称和测试单元路径到日志
# test unit --> vtuexe
    @keyword("run_test_configs")  
    def run_test_configs(self):
        """Run all loaded CANoe test configurations (including test units)"""
        self._internal_run_test_configs()  # 调用 CANoe 内部方法，执行所有已加载的测试配置（主要是测试单元 .vtuexe）
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
        with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
            f.write('Test configurations started\n')  # 记录测试配置（包括测试单元）运行完成到日志




    @keyword("start_measurement")
    def start_measurement(self):
        """Start CANoe measurement"""
        self.Start()
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  
        with open(log_file, 'a', encoding='utf-8') as f: 
            f.write('< measurement started >\n')  


    @keyword("stop_measurement")
    def stop_measurement(self):
        """Stop CANoe measurement"""
        self.Stop() 
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log')) 
        with open(log_file, 'a', encoding='utf-8') as f: 
            f.write('< measurement stopped >\n')  

# 
    @keyword("close_canoe")
    def close_canoe(self):
        """Close the CANoe application"""
        self.App.Quit()
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write('CANoe application closed\n')



    # @keyword("verify_test_execution")
    # def verify_test_execution(self):
    #     """验证测试执行是否成功（包括检查日志和测试配置状态）"""
    #     log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
    #     if not os.path.exists(log_file):  # 检查日志文件是否存在
    #         raise AssertionError(f"Log file not found: {log_file}")  # 如果日志文件不存在，抛出错误
    #     with open(log_file, 'r', encoding='utf-8') as f:  # 以读取模式打开日志文件
    #         content = f.read()  # 读取日志文件全部内容
    #         if 'measurement started' not in content:  # 检查日志是否包含“测量开始”记录
    #             raise AssertionError("Measurement start not found in log")  # 如果没有“测量开始”，抛出错误
    #         if 'measurement stopped' not in content:  # 检查日志是否包含“测量停止”记录
    #             raise AssertionError("Measurement stop not found in log")  # 如果没有“测量停止”，抛出错误
    #         if 'Ran all test configurations' not in content:  # 检查日志是否包含“测试配置运行完成”记录
    #             raise AssertionError("Test configurations execution not found in log")  # 如果没有“测试配置运行完成”，抛出错误
    #     for tc in self.TestConfigs:  # 遍历所有测试配置
    #         if not tc.IsDone():  # 检查每个测试配置（包括测试单元）是否成功完成
    #             raise AssertionError(f"Test configuration {tc.Name} did not complete successfully")  # 如果测试配置未完成，抛出错误
    #     with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
    #         f.write('Test execution verified\n')  # 记录测试执行验证完成到日志
    @keyword("verify_test_execution")
    def verify_test_execution(self):
        """Verify successful execution of CANoe tests (including log and test configuration status)"""
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))
        if not os.path.exists(log_file):
            raise AssertionError(f"Log file not found: {log_file}")
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'Measurement started' not in content:
                raise AssertionError("Measurement start not found in log")
            if 'Measurement stopped' not in content:
                raise AssertionError("Measurement stop not found in log")
            if 'Test configurations started' not in content:
                raise AssertionError("Test configurations execution not found in log")
        for tc in self.TestConfigs:
            if not tc.IsDone():
                raise AssertionError(f"Test configuration {tc.Name} did not complete successfully")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write('Test execution verified\n')


# ------------------------------------------------------------------------
# ---------------------------- Event Handlers ----------------------------
# ------------------------------------------------------------------------

class CanoeApplicationEvents(object):
    def OnOpen(self, FullName):
        print("Configuration: "+FullName+" is opened")
    def OnQuit(self):
        print("CANoe is quit")

class CanoeMeasurementEvents(object):
    def OnInit(self):
        print("< measurement init >")
    def OnStart(self): 
        CanoeSync.Started = True
        CanoeSync.Stopped = False
        print("< measurement started >")
    def OnStop(self): 
        CanoeSync.Started = False
        CanoeSync.Stopped = True
        print("< measurement stopped >")
    def OnExit(self):
        print("< measurement exit >")

class CanoeTestModule:
    def __init__(self, tm):
        self.tm = tm
        self.Events = DispatchWithEvents(tm, CanoeTestEvents)
        self.Name = tm.Name
        self.IsDone = lambda: self.Events.stopped
        self.Enabled = tm.Enabled
    def Start(self):
        if self.tm.Enabled:
            self.tm.Start()
            self.Events.WaitForStart()

class CanoeTestConfiguration:
    def __init__(self, tc):        
        self.tc = tc
        self.Name = tc.Name
        self.Events = DispatchWithEvents(tc, CanoeTestEvents)
        self.IsDone = lambda: self.Events.stopped
        self.Enabled = tc.Enabled
    def Start(self):
        if self.tc.Enabled:
            self.tc.Start()
            self.Events.WaitForStart()

class CanoeTestEvents:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.WaitForStart = lambda: DoEventsUntil(lambda: self.started)
        self.WaitForStop = lambda: DoEventsUntil(lambda: self.stopped)
    def OnStart(self):
        self.started = True
        self.stopped = False        
        print("<", self.Name, " started >")
    def OnStop(self, reason):
        self.started = False
        self.stopped = True 
        print("<", self.Name, " stopped >")



# -----------------------------------------------------------------------------
# main
# # -----------------------------------------------------------------------------
# app = CanoeSync()

# # load the sample configuration
# #app.Load('CANoeConfig\PythonBasicEmpty.cfg')

# # # add test modules to the configuration
# # app.LoadTestSetup('TestEnvironments\Test Environment.tse')

# # # add a test configuration and a list of test units
# # app.LoadTestConfiguration('TestConfiguration', ['TestConfiguration\EasyTest\EasyTest.vtuexe'])

# # # start the measurement
# # app.Start()    

# # run the test modules
# app.RunTestModules()

# # run the test configurations
# app.RunTestConfigs()

# # wait for a keypress to stop the measurement
# print("Press any key to stop the measurement ...")
# while not msvcrt.kbhit():
#     DoEvents()

# # stop the measurement
# app.Stop()
# waitsleep(2)