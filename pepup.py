###ログインログオフのみ#＃＃
import datetime
import time
import boto3
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

#pepup関連の変数
URL="https://pepup.life/users/sign_in"
username = os.environ['ID']
password = os.environ['PW']
TODAY = datetime.date.today()
SLEEPTIME = 9

#デフォルトのメール関連の変数
_from = 'tsae360@gmail.com' # fromは予約語で使えない
_to = ['kinkoman2014@outlook.jp'] #配列
_subject = 'PEPUP日次処理成功のお知らせ'
_body = '本日のPEPUP日次処理は成功しました。'

def ses_send_email(_from, _to, _subject, _body):
    _ses = boto3.client('ses', region_name='us-west-2')
    _response = _ses.send_email(
        Source=_from,
        Destination={'ToAddresses': _to},
        Message={
            'Subject':{
                'Data': _subject,
            },
            'Body': {
                'Text': {
                    'Data': _body,
                },
            }
        }
    )

    return _response

def lambda_handler(event,context):
        
        try:  
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument("--disable-application-cache")
            options.add_argument("--disable-infobars")
            options.add_argument("--no-sandbox")
            options.add_argument("--hide-scrollbars")
            options.add_argument("--enable-logging")
            options.add_argument("--log-level=0")
            options.add_argument("--v=99")
            options.add_argument("--single-process")
            options.add_argument("--ignore-certificate-errors")
            # Headless Chromeを起動
            options.binary_location = "./bin/headless-chromium"
            driver = webdriver.Chrome(executable_path="./bin/chromedriver", chrome_options=options)
            
            driver.get(URL)

            userNameField = driver.find_element_by_id('sender-email')
            userNameField.send_keys(username) 

            passwordField = driver.find_element_by_id('user-pass')
            passwordField.send_keys(password)

            submitButton = driver.find_element_by_name('commit')
            submitButton.click()

            ToDailyInput = driver.find_element_by_class_name('SideMenu_MyFitnessDataIcon')
            ToDailyInput.click()

            tmp = driver.find_elements_by_xpath('//*[@id="app"]/div/div[2]/div/div[2]/div/div[4]/div[2]/div[*]/label/div[2]')
            for ch in tmp:
                ch.click()

            time.sleep(5)

            FILENAME = 'result' + str(TODAY) + '.png'
            # スクリーンショットを撮る。
            driver.save_screenshot('/tmp/' + FILENAME)
            
            #睡眠時間の入力
            #driver.find_element_by_xpath('//*[@id="app"]/div/div/div[2]/div/div[2]/div/div[3]/div[2]/div[5]/div/div/div[2]/div[2]/a').click()
            driver.find_element_by_xpath('//*[@id="app"]/div/div[2]/div/div[2]/div/div[3]/div[2]/div[5]/div/div/div[2]/div[2]/a').click()
            driver.find_element_by_xpath('//*[@id="open_edit_sleeping"]').click()
            driver.find_element_by_xpath('//*[@id="measurement_value"]').send_keys(SLEEPTIME)
            driver.find_element_by_xpath('//*[@id="edit_measurement_submit"]').click()
            FILENAME2 = 'result' + str(TODAY) + '_SLEEPTIME.png'
            # スクリーンショットを撮る。
            driver.save_screenshot('/tmp/' + FILENAME2)
            driver.back()

            #ログオフ
            #TOHOME = driver.find_element_by_xpath('//*[@id="app"]/div/div/div[1]/div/div[1]/a/img')
            driver.back()
            LogoffMenuButton = driver.find_element_by_class_name('Header_DropdownLink') 
            LogoffMenuButton.click()
            LogoffButton = driver.find_element_by_class_name('Header_DropdownLogOutIcon') 
            LogoffButton.click()

            driver.quit() 

            #upload to s3
            s3 = boto3.resource('s3')
            backet = s3.Bucket('kinkoman13')
            backet.upload_file('/tmp/'+FILENAME,'pepup/'+FILENAME)
            backet.upload_file('/tmp/'+FILENAME2,'pepup/'+FILENAME2)
            #send mail
            ses_send_email(_from, _to, _subject, _body)
        
        except Exception as e:

            _subject = 'PEPUP日次処理失敗のお知らせ'
            _body = '本日のPEPUP日次処理は失敗しました。恐れ入りますが手動にて本日分の入力をお長居いたします。'
            _body += e
            _body += traceback.print_exc()   
            #send mail
            ses_send_email(_from, _to, _subject, _body)
