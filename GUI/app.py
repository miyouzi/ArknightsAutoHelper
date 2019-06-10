# system package import
import wx
import wx.grid
from threading import Thread
from wx.lib.pubsub import pub
import time

# GUI package import
from GUI.Frames import *

# from GUI.Index import Index
# from GUI.ScoreManageMent import ScoreManageMent
# from GUI.StudentChooseClass import StudentChooseClass
# from GUI.StudentLogin import StudentLogin
# from GUI.StudentScoreList import StudentScoreList
# from GUI.MessageDialog import MessageDialog_CANCEL, MessageDialog_OK, MessageDialog_Yes_No
# from GUI.ScoreAnalyze import ScoreAnalyze
# from GUI.ManageStudentDetail import ManageStudentDetail
# from GUI.ManageClassDetail import ManageClassDetail

# Ark package import
from Arknights.base import ArknightsHelper
from Arknights.click_location import LIZHI_CONSUME
# MISC package import
from collections import OrderedDict

# Button definitions
ID_START = wx.NewId()
ID_STOP = wx.NewId()

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()


def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)


class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data


class ArkThread(Thread):
    def __init__(self, ark, **param):
        '''
        我很少写进程处理的，有些问题还请多多包涵
        '''
        Thread.__init__(self)
        self.ark = ark
        if "func" in param:
            self.func = param['func']
        else:
            self.func = None
        if "c_id" in param:
            self.c_id = param['c_id']
        else:
            self.c_id = None
        if "set_count" in param:
            self.set_count = int(param['set_count'])
        else:
            self.set_count = None
        if "TASK_LIST" in param:
            self.TASK_LIST = param['TASK_LIST']
        else:
            self.TASK_LIST = None

        self.start()

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread. Simulation of
        # a long process (well, 10s here) as a simple loop - you will
        # need to structure your processing so that you periodically
        # peek at the abort variable
        if self.TASK_LIST is not None:
            self.ark.main_handler(self.TASK_LIST)
        else:
            self.ark.module_battle_slim(
                c_id=self.c_id, set_count=self.set_count, set_ai=False,
                self_fix=self.ark.ocr_active, sub=True
            )
        # wx.PostEvent(self._notify_window, ResultEvent(10))

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        # self._want_abort = 1
        self.ark.destroy()

class ArknightsAutoHelperGUI(wx.App):
    def __init__(self):
        self.Index = None
        self.worker = None
        wx.App.__init__(self)

        self.__current_active_frame = "Index"
        try:
            self.ark = ArknightsHelper(call_by_gui=True, out_put=1)
        except Exception as e:
            self.Index.out_put_ctrl.AppendText(e)
            self.ark = None

        # load settings
        #
        # loaded

        self.backend_buffer_push()

    def __restart_ark(self):
        if self.ark is None:
            try:
                self.ark = ArknightsHelper(call_by_gui=True, out_put=1)
            except Exception as e:
                self.Index.out_put_ctrl.AppendText(e)
        else:
            self.ark.destroy()
            try:
                self.ark = ArknightsHelper(call_by_gui=True, out_put=1)
            except Exception as e:
                self.Index.out_put_ctrl.AppendText(e)

    def backend_buffer_push(self):
        buffer = self.ark.shell_color.get_buffer()
        if buffer != "":
            self.Index.out_put_ctrl.AppendText(buffer)
        self.Index.current_lizhi.SetValue(self.ark.CURRENT_STRENGTH.__str__())
        wx.CallLater(500, self.backend_buffer_push)

    def OnInit(self):
        # Init All frames
        self.Index = Index(parent=None)
        # Init Router
        self.__bind_router()
        self.__bind_event()
        self.worker = None
        # Show Index
        self.Index.Show(show=True)
        return True

    def __bind_event(self):
        self.Index.test_ocr.Bind(wx.EVT_BUTTON, self.check_ocr_active)
        self.Index.main_start.Bind(wx.EVT_BUTTON, self.start_main)
        self.Index.slim_start.Bind(wx.EVT_BUTTON, self.start_slim)

    def check_ocr_active(self, event):
        event.Skip()

    def start_main(self, event):
        TASK_LIST = OrderedDict()
        if self.Index.task1_battle_name.GetValue() != "":
            TASK_LIST[self.Index.task1_battle_name.GetValue()] = int(self.Index.task1_battle_time.GetValue())
        if self.Index.task2_battle_name.GetValue() != "":
            TASK_LIST[self.Index.task2_battle_name.GetValue()] = int(self.Index.task2_battle_time.GetValue())
        if self.Index.task3_battle_name.GetValue() != "":
            TASK_LIST[self.Index.task3_battle_name.GetValue()] = int(self.Index.task3_battle_time.GetValue())
        if self.Index.task4_battle_name.GetValue() != "":
            TASK_LIST[self.Index.task4_battle_name.GetValue()] = int(self.Index.task4_battle_time.GetValue())
        for _ in TASK_LIST.keys():
            if _ not in LIZHI_CONSUME or "GT" in _:
                MessageDialog_OK("{} 不在支持的关卡列表中".format(_), "警告")
                return False

        if TASK_LIST.__len__() == 0:
            MessageDialog_CANCEL("未选择关卡", "提示")
            return False
        else:
            self.worker = ArkThread(ark=self.ark, TASK_LIST=TASK_LIST)

    def start_slim(self, event):
        c_id = self.Index.slim_battle_name.GetValue()
        set_count = int(self.Index.slim_battle_time.GetValue())
        self.worker = ArkThread(ark=self.ark, c_id=c_id, set_count=set_count)

    def __bind_router(self):
        pass
        # Index Router
        # Add Router Here
        # self.Index.Bind(wx.EVT_CLOSE, self.OnCloseWindow, self.Index)
        #
        # self.Bind(wx.EVT_BUTTON,
        #           lambda event: self.OnRouter_change(event, 'StudentLogin'),
        #           self.Index.m_button_Index2StudentLogin)

    def OnRouter_change(self, event, value='Index'):
        pass
        # self.__current_active_frame = value
        # if self.__current_active_frame == "Index":
        #     self.Index.Show()
        #     self.StudentLogin.Hide()
        #     self.StudentChooseClass.Hide()
        #     self.StudentScoreList.Hide()
        #     self.ScoreManageMent.Hide()
        #     self.SetTopWindow(self.Index)


def start_app():
    ArknightsAutoHelperGUI().MainLoop()
    wx.Exit()


if __name__ == '__main__':
    start_app()
