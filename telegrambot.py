# import boto3
import logging
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from selenium import webdriver
from tempfile import mkdtemp
from selenium.webdriver.common.by import By
import io
import base64
import time
import requests

AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
S3_BUCKET_NAME = ''

telegram_token = ''
apiURL = f'https://api.telegram.org/bot{telegram_token}/sendMessage'

CHROME_PATH = "C:/Users/Administrator/AppData/Local/Google/Chrome/User Data"


class OneMotoring():
    def __init__(self):
        # print("just init")
        self.options = webdriver.ChromeOptions()
        # self.service = webdriver.ChromeService("/opt/chromedriver")

        # self.options.binary_location = '/opt/chrome/chrome'
        # fake_user_agent = Faker()
        # print(fake_user_agent.user_agent())

        self.options.add_experimental_option("excludeSwitches", ['enable-automation'])
        self.options.add_argument('--disable-infobars')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--no-first-run')
        self.options.add_argument('--ignore-certificate-errors')
        self.options.add_argument('--disable-client-side-phishing-detection')
        self.options.add_argument('--allow-running-insecure-content')
        self.options.add_argument('--disable-web-security')
        # self.options.add_argument('--lang=' + random.choice(language_list))
        # self.options.add_argument('--user-agent=Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 10.0; Trident/3.1)')
        # self.options.add_argument('--headless=new')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1280x1696")
        self.options.add_argument("--single-process")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-dev-tools")
        self.options.add_argument("--no-zygote")
        # self.options.add_argument(f"--user-data-dir={mkdtemp()}")
        self.options.add_argument(f"--user-data-dir={CHROME_PATH}")
        self.options.add_argument(f"--data-path={mkdtemp()}")
        self.options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        self.options.add_argument("--remote-debugging-port=9222")

        self.driver = webdriver.Chrome(options=self.options)

        # print("is good at init")

    def open_onemotoring(self):
        # print("try to get webpage")
        self.driver.get('https://vrl.lta.gov.sg/lta/vrl/action/pubfunc?ID=EnquireRoadTaxExpDtProxy')
        # print("is good at webpage")

    def vehicle_search(self, vehicle_plate):
        try:
            veh_no = self.driver.find_element('xpath', '//*[@id="vehNoField"]')
            veh_no.send_keys(vehicle_plate)

            tc_checkbox = self.driver.find_element('xpath', '// *[ @ id = "agreeTCbox"]')
            tc_checkbox.click()

            next_button = self.driver.find_element('xpath', '//*[@id="btnNext"]')
            next_button.click()

            # print("good")
            time.sleep(2)
            # print(self.driver.page_source)

            veh_model = self.driver.find_element(by=By.XPATH,
                                                 value='/ html / body / section / div[3] / div[4] / div[2] / div[2] / form / div[1] / div[3] / div / div[2] / div[2] / p').text
            print(veh_model)

            road_tax = self.driver.find_element('xpath',
                                                "/html/body/section/div[3]/div[4]/div[2]/div[2]/form/div[1]/div[4]/div/div/p[2]").text

            self.driver.close()

            return veh_model, road_tax

        except Exception as e:
            error = self.driver.find_element(by=By.XPATH,
                                                 value='// *[ @ id = "backend-error"] / table / tbody / tr / td / ul / li').text
            raise Exception(error)



        # veh_model = self.driver.find_element_by_xpath(
        #     '//*[@id="main-content"]/div[2]/div[2]/form/div[1]/div[3]/div/div[2]/div[2]/p')
        # print(veh_model.text)


def send_to_telegram(chat_id, message):
    try:
        response = requests.post(apiURL, json={'chat_id': chat_id, 'text': message})
        print(response.text)
    except Exception as e:
        print(e)


def chromium_onemotoring(ven, chat_id):
    try:
        bot = OneMotoring()
        # bot.browser_login()
        bot.open_onemotoring()
        veh_model, road_tax = bot.vehicle_search(ven)

        send_to_telegram(chat_id, f"The vehicle model is {veh_model}\nRoad Tax Expiry Date : {road_tax}")

    except Exception as e:
        # print(e)
        send_to_telegram(chat_id, "Exception encounter - {}".format(e))


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


async def check_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    check_text = update.message.text
    check_text = check_text.replace("/check", "").strip()
    print(check_text)

    # print(update.effective_chat.id)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Please wait. Checking for {check_text}")

    # Do chromium here
    chromium_onemotoring(check_text, update.effective_chat.id)

    # # Send to SQS
    # sqs = boto3.client('sqs',
    #                    region_name='ap-southeast-1',
    #                    aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    # response = sqs.send_message(
    #     QueueUrl='https://sqs.ap-southeast-1.amazonaws.com/851725521016/queue_for_image_bytes',
    #     MessageBody=json.dumps({"check_text": check_text, "chat_id": update.effective_chat.id})
    # )

    # print(response)
    print("check model ended")


# async def downloader(update, context):
#     logging.info(update.message)
#
#     file_id = update.message.photo[-1]
#     new_file = await context.bot.get_file(file_id)
#
#     with io.BytesIO() as out:
#         await new_file.download_to_memory(out)
#         photo_data = out.getvalue()
#
#     # Initialize S3 client
#     s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
#
#     # Upload to S3
#     s3_key = "fileName.jpg"  # Adjust as needed
#     s3.upload_fileobj(io.BytesIO(photo_data), S3_BUCKET_NAME, s3_key)
#
#     # Acknowledge file received
#     await update.message.reply_text("{fileName} saved successfully to S3")


# async def downloader_bytes(update, context):
#     logging.info(update.message)
#
#     file_id = update.message.photo[-1]
#     new_file = await context.bot.get_file(file_id)
#
#     image_bytes = await new_file.download_as_bytearray()
#
#     # Send to SQS
#     sqs = boto3.client('sqs',
#                        region_name='ap-southeast-1',
#                        aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
#     response = sqs.send_message(
#         QueueUrl='',
#         MessageBody=base64.b64encode(image_bytes).decode('utf-8')
#     )
#
#     print(response)
#     print("successfully sent to sqs")


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    application = ApplicationBuilder().token(telegram_token).build()

    start_handler = CommandHandler('start', start)
    check_handler = CommandHandler('check', check_model)
    # photo_handler = MessageHandler(filters.PHOTO, downloader_bytes)

    application.add_handler(start_handler)
    application.add_handler(check_handler)

    # application.add_handler(photo_handler)

    application.run_polling()
