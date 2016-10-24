from bs4 import BeautifulSoup
import requests
import datetime as dt
import time
from requests import session


historys = []
courses = []
url = 'https://myportal.vtc.edu.hk/wps/myportal/!ut/p/a1/hY_NCoJAGACfpYPH9lv_yroJlQSSiYW5F_laN13bVslNfPzwAaLjwMAwwOAGTOMoazSy06hmZqvSPm72tpvQOLo6Bxra8S5I_cClJwoFFGz9S4gSHzJgwFoccSKDeI9KGCI1V59KkB5NU0r96KCwaDv0Fs3OCfUci3KFwxAaI3SFmgsyNealIP_XYt1WehdP5DVPIUc-T0D_xPsyDxdfp1LYiQ!!/'

headers = {
    'Cookie' : '',
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36'
}
def login():
    post_data = {
        'ajaxLogin': 'true',
        'userid': '150151714',
        'password': 'y5981393!@Y'
    }

    with session() as c:
        login_url = 'https://myportal.vtc.edu.hk' + get_loginURL()
        request = c.post(login_url, data=post_data)
        for cookie in request.cookies:
            headers['Cookie'] += str(cookie.name + "=" + cookie.value + ";")

def get_loginURL():
        login_pageurl ='https://myportal.vtc.edu.hk/wps/portal/'
        wb_data = requests.get(login_pageurl)
        soup = BeautifulSoup(wb_data.text,'lxml')

        return str(soup.select('div > div > form')[0].get('action'))

def calLateTime(arr_time, lesson_time, status):
    lesson_starttime = lesson_time[:5]
    if  (status == 'Present'):
        return ''
    elif (status == 'Late'):
        return ((dt.datetime(int("2016"),int('12'),int('06'),int(arr_time[:2])
                             ,int(arr_time[3:5])) - dt.datetime(int("2016"),int('12'),int('06')
                             ,int(lesson_starttime[:2]),int(lesson_starttime[3:5]))).seconds)/60
    elif (status == 'Absent'):
        return  calAbsentTime(lesson_time)

def calAbsentTime(lesson_time):
    lesson_StartTime = lesson_time[:5]
    lesson_EndTime = lesson_time[8:13]


    return ((dt.datetime(int("2016"),int('12'),int('06'),int(lesson_EndTime[:2])
                            ,int(lesson_EndTime[3:5])) - dt.datetime(int("2016"),int('12'),int('06')
                            ,int(lesson_StartTime[:2]),int(lesson_StartTime[3:5]))).seconds)/60

def check_attend(SubjectCode):
    wb_data = requests.get(url, headers=headers)
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
        'viewns_Z7_1I9E13O0LGU2F0A1LD8Q583GO5_:j_id26950906_1_18bb2b55_SUBMIT':post_Submit,
        'viewns_Z7_1I9E13O0LGU2F0A1LD8Q583GO5_:j_id26950906_1_18bb2b55:changeModuleButton':post_ChangeModuleButton,
        'viewns_Z7_1I9E13O0LGU2F0A1LD8Q583GO5_:j_id26950906_1_18bb2b55:j_id26950906_1_18bb2b07': post_SubjectCode,
        'autoScroll': post_AutoScroll,
        'javax.faces.ViewState': post_ViewState
    }

    wb_data2 = requests.post('https://myportal.vtc.edu.hk' + post_url, data=post_data, headers=headers)
    wb_data.content
    soup2 = BeautifulSoup(wb_data2.text, 'lxml')

    dates = soup2.select('tbody > tr > td:nth-of-type(1) ')
    statuss = soup2.select('tbody > tr > td:nth-of-type(2) ')
    arrive_times = soup2.select('tbody > tr > td:nth-of-type(3) ')
    class_times = soup2.select('tbody > tr > td:nth-of-type(4) ')
    class_rooms = soup2.select('tbody > tr > td:nth-of-type(5) ')



    for date, status, arrive_time, class_time, class_room in zip(dates,statuss,arrive_times,class_times,class_rooms):
        history1 = {
            'date': date.get_text(),
            'status': status.get_text(),
            'arrive_time': arrive_time.get_text(),
            'class_time': class_time.get_text(),
            'class_rooms': class_room.get_text(),
            'late_time': calLateTime(arrive_time.get_text(),class_time.get_text(),status.get_text())
        }
        historys.append(history1)
    cal_main(SubjectCode)

def cal_main (SubjectCode):
    totalLate = 0
    global historys
    for history in historys:
        if history['late_time']!="":
            totalLate+= int(history['late_time'])

    print('-----------------------------------------------------------------------------------------------')
    hours = input('Enter the total hour of course (' + SubjectCode  + ') : ')
    print("Total left hours: " + str(round(float(totalLate)/60,2)))
    print("Total left percentage " + str(round((((float(totalLate)/60)/float(hours))*100),2)) + "%")
    print("You have " + str(round(float(hours)*0.3 - float(totalLate/60),2)) + " hours to leave. ^^")
    print('-----------------------------------------------------------------------------------------------')
    historys = []

def getSubjectcode():
    global courses
    wb_data = requests.get(url, headers=headers)
    soup = BeautifulSoup(wb_data.text, 'lxml')

    _courses = soup.select('td > select > option')

    for course in _courses:
        courses.append(course.get('value'))
    courses.pop(0) #delete the first empty option

def start():
    login()
    getSubjectcode()
    for course in courses:
        check_attend(course)




start();
