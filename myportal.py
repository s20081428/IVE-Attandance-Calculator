import datetime as dt
import logging
import time

import requests
import telegram
from bs4 import BeautifulSoup
from emoji import emojize
from requests import session
from telegram.ext import MessageHandler, Updater, CommandHandler, Filters
from telegram.ext.dispatcher import run_async


class Action:
    text = ''
    historys = []
    courses = []
    username = ''
    url = 'https://myportal.vtc.edu.hk/wps/myportal/!ut/p/a1/hY_NCoJAGACfpYPH9lv_yroJlQSSiYW5F_laN13bVslNfPzwAaLjwMAwwOAGTOMoazSy06hmZqvSPm72tpvQOLo6Bxra8S5I_cClJwoFFGz9S4gSHzJgwFoccSKDeI9KGCI1V59KkB5NU0r96KCwaDv0Fs3OCfUci3KFwxAaI3SFmgsyNealIP_XYt1WehdP5DVPIUc-T0D_xPsyDxdfp1LYiQ!!/'

    headers = {
        'Cookie': '',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
    }

    def __init__(self, username, password, update, bot):
        self.username = username
        self.password = password
        self.update = update
        self.bot = bot

    def login(self, username, password):
        post_data = {
            'ajaxLogin': 'true',
            'userid': username,
            'password': password
        }

        with session() as c:
            login_url = 'https://myportal.vtc.edu.hk' + self.get_loginURL()
            request = c.post(login_url, data=post_data)
            for cookie in request.cookies:
                self.headers['Cookie'] += str(cookie.name + "=" + cookie.value + ";")

    def get_loginURL(self):
        login_pageurl = 'https://myportal.vtc.edu.hk/wps/portal/'
        wb_data = requests.get(login_pageurl)
        soup = BeautifulSoup(wb_data.text, 'lxml')

        return str(soup.select('div > div > form')[0].get('action'))

    def calLateTime(self, arr_time, lesson_time, status):
        lesson_starttime = lesson_time[:5]
        if (status == 'Present'):
            return ''
        elif (status == 'Late'):
            return ((dt.datetime(int("2016"), int('12'), int('06'), int(arr_time[:2])
                                 , int(arr_time[3:5])) - dt.datetime(int("2016"), int('12'), int('06')
                                                                     , int(lesson_starttime[:2]),
                                                                     int(lesson_starttime[3:5]))).seconds) / 60
        elif (status == 'Absent'):
            return self.calAbsentTime(lesson_time)

    def calAbsentTime(self, lesson_time):
        lesson_StartTime = lesson_time[:5]
        lesson_EndTime = lesson_time[8:13]

        return ((dt.datetime(int("2016"), int('12'), int('06'), int(lesson_EndTime[:2])
                             , int(lesson_EndTime[3:5])) - dt.datetime(int("2016"), int('12'), int('06')
                                                                       , int(lesson_StartTime[:2]),
                                                                       int(lesson_StartTime[3:5]))).seconds) / 60

    def check_attend(self, SubjectCode):
        self.historys = []
        wb_data = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(wb_data.text, 'lxml')

        post_url = soup.select('div.hkvtcsp_content_box3 > form')[0].get('action')
        post_ViewState = soup.select('#javax.faces.ViewState')[0].get('value')
        post_EncodedURL = soup.select('div.hkvtcsp_content_box3 > div > div > form > input')
        post_AutoScroll = ''
        post_ChangeModuleButton = ''
        post_Submit = soup.select('div.hkvtcsp_content_box3 > form > input[type="hidden"]')[1].get('value')
        post_SubjectCode = SubjectCode

        post_data = {
            'javax.faces.encodedURL': post_EncodedURL,
            'viewns_Z7_1I9E13O0LGU2F0A1LD8Q583GO5_:j_id26950906_1_18bb2b55_SUBMIT': post_Submit,
            'viewns_Z7_1I9E13O0LGU2F0A1LD8Q583GO5_:j_id26950906_1_18bb2b55:changeModuleButton': post_ChangeModuleButton,
            'viewns_Z7_1I9E13O0LGU2F0A1LD8Q583GO5_:j_id26950906_1_18bb2b55:j_id26950906_1_18bb2b07': post_SubjectCode,
            'autoScroll': post_AutoScroll,
            'javax.faces.ViewState': post_ViewState
        }

        wb_data2 = requests.post('https://myportal.vtc.edu.hk' + post_url, data=post_data, headers=self.headers)
        wb_data.content
        soup2 = BeautifulSoup(wb_data2.text, 'lxml')

        isWrongCourse = soup2.select('table.hkvtcsp_wording')
        if len(isWrongCourse) > 0:
            dates = soup2.select('tbody > tr > td:nth-of-type(1) ')
            statuss = soup2.select('tbody > tr > td:nth-of-type(2) ')
            arrive_times = soup2.select('tbody > tr > td:nth-of-type(3) ')
            class_times = soup2.select('tbody > tr > td:nth-of-type(4) ')
            class_rooms = soup2.select('tbody > tr > td:nth-of-type(5) ')
            subjectTitle = soup2.select('.hkvtcsp_textInput > option[selected="selected"]')[0].text

            for date, status, arrive_time, class_time, class_room in zip(dates, statuss, arrive_times, class_times,
                                                                         class_rooms):
                history1 = {
                    'date': date.get_text(),
                    'status': status.get_text(),
                    'arrive_time': arrive_time.get_text(),
                    'class_time': class_time.get_text(),
                    'class_rooms': class_room.get_text(),
                    'late_time': self.calLateTime(arrive_time.get_text(), class_time.get_text(), status.get_text())
                }
                self.historys.append(history1)

            self.cal_main(SubjectCode, subjectTitle)
        else:
            pass

    def cal_main(self, SubjectCode, subjectTitle):
        totalLate = 0
        for history in self.historys:
            if history['late_time'] != "":
                totalLate += int(history['late_time'])

        total_study_hours = {
            'ITP4509': 52,
            'ITP4512': 52,
            'ITE3902': 26,
            'LAN4003': 26,
            'LAN4101': 39,
            'SDD4002': 14
        }
        if SubjectCode in total_study_hours:
            hours = total_study_hours[SubjectCode]
            self.bot.sendMessage(chat_id=self.update.message.chat_id, text='課程名稱： <b>' + subjectTitle
                                     + "</b>\n你已缺席了： <b>" + str(round(float(totalLate) / 60, 2)) + " 小時</b>"
                                     + "\n已缺席百分比： <b>" + str(round((((float(totalLate) / 60) / float(hours)) * 100), 2)) + "%</b>"
                                     + "\n你還可缺席： <b>" + str(round(float(hours) * 0.3 - float(totalLate / 60), 2)) + " 小時</b>", parse_mode=telegram.ParseMode.HTML)
            


    def getSubjectcode(self):
        wb_data = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(wb_data.text, 'lxml')

        _courses = soup.select('td > select > option')

        for course in _courses:
            self.courses.append(course.get('value'))
        self.courses.pop(0)  # delete the first empty option

    def process(self):
        self.headers['Cookie'] = ""
        self.courses = []
        self.login(str(self.username), str(self.password))

        try:
            self.getSubjectcode()
            self.bot.sendMessage(chat_id=self.update.message.chat_id,
                                 text='登入成功，正在收集數據並進行分析....')
        except Exception:
            print("ERROR: Login Fail(Wrong account)")
            self.bot.sendMessage(chat_id=self.update.message.chat_id,
                                 text='<b>**登入錯誤(原因如下)**</b>\n1. 你輸入了錯誤的用戶名／密碼 或\n2. 你的帳號已被鎖定',
                                 parse_mode=telegram.ParseMode.HTML)
            return False

        for course in self.courses:
            time.sleep(0.5)
            self.check_attend(course)
        return True


def start(bot, update):
    update.message.reply_text('請按照格式輸入MyPortal的帳戶密碼\nInput Format: username,password')


@run_async
def process(bot, update):
    user_input = update.message.text.split(",")

    if (len(user_input) == 2):
        username = user_input[0].strip()
        password = user_input[1].strip()
    else:
        print("ERROR: Login Fail(Wrong Format)")
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="<b>**登入錯誤(原因如下)**</b>\n1. 請按照格式輸入用戶名／密碼",
                        parse_mode=telegram.ParseMode.HTML)
        return

    newAction = Action(username, password, update, bot)
    if (newAction.process() == True):
        update.message.reply_text("查詢完畢，歡迎再次使用！" + emojize(":blush:", use_aliases=True))


updater = Updater(token=‘<Enter the Telegram API token>’)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(MessageHandler(Filters.text, process))
updater.start_polling()
updater.idle()
