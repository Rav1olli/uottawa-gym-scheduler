import requests
from bs4 import BeautifulSoup
from pandas import DataFrame
import sys
import time
import schedule
import threading
from datetime import datetime

convert_time = {'6:30AM': '6:30AM-7:15AM', '7:30AM': '7:30AM-9:00AM', '8:00AM': '8:00AM-9:15AM',
                '9:30AM': '9:30AM-11:00AM', '10:00AM': '10:00AM-11:15AM', '11:30AM': '11:30AM-1:00PM',
                '12:00PM': '12:00PM-1:15PM', '1:30PM': '1:30PM-3:00PM', '2:00PM': '2:00PM-3:15PM',
                '3:30PM': '3:30PM-5:00PM', '4:00PM': '4:00PM-5:15PM', '5:30PM': '5:30PM-7:00PM',
                '6:00PM': '6:00PM-7:15PM', '7:30PM': '7:30PM-9:00PM', '8:00PM': '8:00PM-9:15PM'}

weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']


def auto_request(s, df, name, request_day, request_time, baseline_link):
    converted_time = convert_time[request_time]
    count = 0
    request_session = df.loc[(df['days'] == request_day) & (df['times'] == converted_time)]
    while list(request_session.to_dict().get('links').values())[0] == 0:
        if count > 30:
            return
        df = refresh_data(s,df)
        request_session = df.loc[(df['days'] == request_day) & (df['times'] == converted_time)]
        time.sleep(10)
        count += 1
        print("\rRequesting for {0}...".format(name))
    add_to_cart_request = s.post(
        baseline_link + list(request_session.to_dict().get('links').values())[0][2:])
    checkout_request = s.post("{}/MyBasket/MyBasketCheckout.asp?URLAddress=//MyBasket/MyBasketCheckout.asp"
                              "&PayAuthorizeWait=Yes".format(baseline_link))
    checkout_again = s.post("{}/MyBasket/MyBasketCheckout.asp?ApplyPayment=true".format(baseline_link))
    waiver = s.post("{}/MyBasket/MyBasketProgramLiabilityWaiver.asp".format(baseline_link))
    final_checkout = s.post("{}/MyBasket/MyBasketCheckout.asp".format(baseline_link))
    print("Successfully scheduled {0} for {1} {2}.".format(name, request_day, request_time), flush=True)

def refresh_data(s, df):
    
    course_names = []
    available_slots = []
    dates = []
    times = []
    barcodes = []
    links = []
    link_type = []
    days = []

    for i in range(6):  # TODO: fix magic number, 6 represents the number of pages that the school usually puts up
        r4 = s.get(
            'https://geegeereg.uottawa.ca/geegeereg/Activities/ActivitiesDetails.asp?GetPagingData=true&aid=316&sEcho=4&iColumns=9&sColumns=&iDisplayStart=' + str(
                (i * 10)) + '&iDisplayLength=10&ajax=true')
        
        soup = BeautifulSoup(r4.text, 'lxml')
        for row in soup.find_all(headers="BasketLink"):
            try:
                links.append(row.a['href'])
                link_type.append(row.a.text.split()[0])
            except:
                links.append(0)
                link_type.append(0)
        for row in soup.find_all(headers='Course'):
            course_names.append(row.div.text)
        for row in soup.find_all(headers="Times"):
            times.append(row.text.split()[0] + "-" + row.text.split()[2])
        for row in soup.find_all(headers="Dates"):
            dates.append(row.text.split()[0])
        for row in soup.find_all(headers="Available"):
            available_slots.append(row.text.split()[0])
        for row in soup.find_all(headers="Barcode"):
            barcodes.append(row.text.split()[0])
        for row in soup.find_all(headers="Day"):
            days.append(row.text.split()[0])

    # print(len(links))
    # print(len(link_type))
    # print(len(course_names))
    # print(len(times))
    # print(len(dates))
    # print(len(available_slots))
    # print(len(barcodes))
    # print(len(days))

    df['course_names'] = course_names
    df['days'] = days
    df['times'] = times
    df['dates'] = dates
    df['available'] = available_slots
    df['barcode'] = barcodes
    df['links'] = links
    df['link_type'] = link_type
    

    df.to_csv("./uottawa_gym_info.csv")
    return df

def login(barcode, pin):
    baseline_link = "https://geegeereg.uottawa.ca/geegeereg"

    # Create a session
    s = requests.Session()
    # Landing request
    r = s.get('{}/Activities/ActivitiesDetails.asp?aid=316'.format(baseline_link)).content
    while r == b"<BR><BR><strong>L'acc\xc3\xa8s au site est pr\xc3\xa9sentement indisponible. Si vous souhaitez vous inscrire \xc3\xa0 une activit\xc3\xa9, veuillez, s'il vous pla\xc3\xaet, r\xc3\xa9essayer apr\xc3\xa8s 3 h.\r\n<br><br>\r\nAccess to the site is currently unavailable. To register for activities, please try again after 3 am. </strong><BR><BR>Nous \xc3\xa9prouvons pr\xc3\xa9sentement des probl\xc3\xa8mes techniques avec le programme d'inscription en ligne. Nous faisons tout en notre pouvoir pour r\xc3\xa9gler la situation. Veuillez revenir plus tard aujourd'hui pour terminer votre inscription en ligne aux programmes intra-muros et aux activit\xc3\xa9s r\xc3\xa9cr\xc3\xa9atives.\r\n<br><br>":
        time.sleep(10)
        # creating a new session to avoid cookies getting blocked
        s = requests.Session()
        r = s.get('{}/Activities/ActivitiesDetails.asp?aid=316'.format(baseline_link)).content
        print("Page Issues", flush=True)

    # Login Request
    s.post("https://geegeereg.uottawa.ca/geegeereg/MyAccount/MyAccountUserLogin.asp",
           data={'ClientBarcode': barcode, 'AccountPin': pin, 'Enter': 'Login', 'FullPage': 'false'})

    return s

def user_thread(name, barcode, pin, times):
    print(name+" thread started.\n")
    s = login(barcode, pin)
    
    df = DataFrame()
    updated_df = refresh_data(s, df)

    today = datetime.today().strftime('%w')
    # today = '0'
    day_to_schedule = weekdays[(int(today) + 2) % 7]
    
    baseline_link = "https://geegeereg.uottawa.ca/geegeereg"
    request_day = ""
    request_time = ""
    found = False
    for time in times:
        if time[0] == day_to_schedule:
            found = True
            request_day = time[0]
            request_time = time[1]
            auto_request(s, updated_df, name, request_day, request_time, baseline_link)

    if found == False:
        print("No required reservation found for "+name)
            
    print(name+" thread ended.")
    return

def main():
    print("Scheduling started.")

    data = open('gym.txt', 'r')
    data_lines = data.readlines()
    
    users = []

    next_user = False
    read_barcode = False
    read_pin = False
    read_time = False
    current_user = ""
    current_barcode = ""
    current_pin = ""
    current_times = []
    for line in data_lines:
        if current_user == "":
            current_user = line[:-1]
            read_barcode = True
        elif read_barcode:
            read_barcode = False
            current_barcode = line[:-1]
            read_pin = True
        elif read_pin:
            read_pin = False
            current_pin = line[:-1]
            read_time = True
        elif line == '\n':
            read_time = False
            users.append(
                {'name': current_user, 'barcode': current_barcode,
                 'pin': current_pin,  'times': current_times})
            current_user = ""
            current_barcode = ""
            current_pin = ""
            current_times = []
        elif read_time:
            current_times.append((line[:-1].split()[0], line[:-1].split()[1]))
    print(users)
    threads = []
    
    for user in users:
        try:
            new_thread = threading.Thread(target=user_thread, args=(user['name'], user['barcode'],
                                                   user['pin'], user['times'],))
            threads.append(new_thread)
            new_thread.start()
        except:
            raise

    for thread in threads:
        thread.join()
    
    print("Program finished.")
          
schedule.every().day.at("20:59:50").do(main)

while True:
    schedule.run_pending()
    current_time = datetime.now().strftime("%H:%M:%S")
    print("Scheduler is sleeping. Current time is "+ current_time)
    time.sleep(15)
