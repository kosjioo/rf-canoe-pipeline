from win32com.client import DispatchEx
app = DispatchEx('CANoe.Application')
print(app.Version)



# 应该输出为：
# PS C:\Users\admin\Desktop\Home\24_Devops\05_RF_CANoe_v2> & C:/Users/admin/AppData/Local/Programs/Python/Python313/python.exe c:/Users/admin/Desktop/Home/24_Devops/05_RF_CANoe_v2/01-keywords/CanoeLibrary.py
# CANoe 17 SP5