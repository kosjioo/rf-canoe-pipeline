import time, os, msvcrt, pythoncom
from win32com.client import *
from win32com.client.connect import *
from robot.api.deco import keyword


def DoEvents():
    pythoncom.PumpWaitingMessages()
    time.sleep(.1)

def DoEventsUntil(cond):
    while not cond():
        DoEvents()

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
    #ConfigPath = "C:/Users/admin/Desktop/Home/24_Devops/05_RF_CANoe_v2/CANoeConfig/PythonBasic.cfg"     # 硬编码CANoe配置文件路径，避免在Robot Framework中重复定义。

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

#testModule 加载并设置 CANoe 的测试模块（.tse 文件）环境
    # def _internal_load_test_setup(self, testsetup):
    #     self.TestSetup = self.App.Configuration.TestSetup
    #     while self.TestSetup.TestEnvironments.Count > 0:
    #         try:
    #             self.TestSetup.TestEnvironments.Remove(0)
    #         except pythoncom.com_error as e:
    #             print(f"Error removing test environment: {e}")
    #             break
    #     path = os.path.abspath(testsetup)
    #     if not os.path.exists(path):
    #         raise FileNotFoundError(f"Test setup file not found: {path}")
    #     testenv = self.TestSetup.TestEnvironments.Add(path)
    #     testenv = CastTo(testenv, "ITestEnvironment2")
    #     self.TraverseTestItem(testenv, lambda tm: self.TestModules.append(CanoeTestModule(tm)))

    def _internal_load_test_setup(self, testsetup):
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





# testModule   
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


#testunits 加载一个新的并配置 CANoe 的测试单元（.vtuexe 文件）
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
#testunits 
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


    def TraverseTestItem(self, parent, testf):
        for test in parent.TestModules: 
            testf(test)
        for folder in parent.Folders: 
            self.TraverseTestItem(folder, testf)


    # ------------------------ Robot Framework Keywords ------------------------
    @keyword("reset_environment")
    def reset_environment(self):
        """重置 CANoe 测试环境（清除所有已加载的 .tse）"""
        self.TestSetup = self.App.Configuration.TestSetup
        try:
            while self.TestSetup.TestEnvironments.Count > 0:
                self.TestSetup.TestEnvironments.Remove(0)
                print("[INFO] Removed one test environment.")
            print("[INFO] All test environments removed.")
        except pythoncom.com_error as e:
            print(f"[ERROR] Failed to remove test environment: {e}")




    @keyword("load_configuration")
    def load_configuration(self, cfg_path):
        """加载 CANoe 配置文件（.cfg 文件）"""
        self._internal_load_configuration(cfg_path)  # 调用 CANoe 内部方法加载配置文件（.cfg），为测试设置基础环境
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
        os.makedirs(os.path.dirname(log_file), exist_ok=True)  # 创建日志目录（如果不存在），确保可以写入日志
        with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
            f.write(f'Opening: {cfg_path}\n')  # 记录加载的配置文件路径到日志


    @keyword("load_test_setup")  # TEST MODULES
    def load_test_setup(self, testsetup):
        """加载 CANoe 测试模块（Test Module，.tse 文件），用于配置测试环境"""
        self._internal_load_test_setup(testsetup)  # 调用 CANoe 内部方法加载测试模块（.tse 文件），设置测试环境
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
        with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
            f.write(f'Loading test setup: {testsetup}\n')  # 记录加载的测试模块路径到日志

    @keyword("load_test_configuration")
    def load_test_configuration(self, testcfgname, testunits):
        """加载 CANoe 测试配置和测试单元（Test Units，.vtuexe 文件）"""
        self._internal_load_test_configuration(testcfgname, [testunits])  # 调用 CANoe 内部方法加载测试配置和测试单元（.vtuexe 文件）
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
        with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
            f.write(f'Loading test configuration: {testcfgname} with unit {testunits}\n')  # 记录测试配置名称和测试单元路径到日志



    @keyword("start_measurement")
    def start_measurement(self):
        """启动 CANoe 测量"""
        self.Start()  # 调用 CANoe 的 Start 方法，开始测量（启动 CANoe 仿真环境）
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
        with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
            f.write('< measurement started >\n')  # 记录测量开始的信息到日志

    @keyword("run_test_configs")  # test unit --> vtuexe
    def run_test_configs(self):
        """运行已加载的测试配置（包括测试单元）"""
        self._internal_run_test_configs()  # 调用 CANoe 内部方法，执行所有已加载的测试配置（主要是测试单元 .vtuexe）
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
        with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
            f.write('Ran all test configurations\n')  # 记录测试配置（包括测试单元）运行完成到日志



    @keyword("run_test_module")#testmodule
    def run_test_modules(self):
        self._internal_run_TestModules()


    @keyword("stop_measurement")
    def stop_measurement(self):
        """停止 CANoe 测量"""
        self.Stop()  # 调用 CANoe 的 Stop 方法，停止测量（关闭 CANoe 仿真环境）
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
        with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
            f.write('< measurement stopped >\n')  # 记录测量停止的信息到日志

    @keyword("verify_test_execution")
    def verify_test_execution(self):
        """验证测试执行是否成功（包括检查日志和测试配置状态）"""
        log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_logs/test_output.log'))  # 计算日志文件的绝对路径
        if not os.path.exists(log_file):  # 检查日志文件是否存在
            raise AssertionError(f"Log file not found: {log_file}")  # 如果日志文件不存在，抛出错误
        with open(log_file, 'r', encoding='utf-8') as f:  # 以读取模式打开日志文件
            content = f.read()  # 读取日志文件全部内容
            if 'measurement started' not in content:  # 检查日志是否包含“测量开始”记录
                raise AssertionError("Measurement start not found in log")  # 如果没有“测量开始”，抛出错误
            if 'measurement stopped' not in content:  # 检查日志是否包含“测量停止”记录
                raise AssertionError("Measurement stop not found in log")  # 如果没有“测量停止”，抛出错误
            if 'Ran all test configurations' not in content:  # 检查日志是否包含“测试配置运行完成”记录
                raise AssertionError("Test configurations execution not found in log")  # 如果没有“测试配置运行完成”，抛出错误
        for tc in self.TestConfigs:  # 遍历所有测试配置
            if not tc.IsDone():  # 检查每个测试配置（包括测试单元）是否成功完成
                raise AssertionError(f"Test configuration {tc.Name} did not complete successfully")  # 如果测试配置未完成，抛出错误
        with open(log_file, 'a', encoding='utf-8') as f:  # 以追加模式打开日志文件
            f.write('Test execution verified\n')  # 记录测试执行验证完成到日志



            
# ---------------------------- Event Handlers ----------------------------

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