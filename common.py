import os
import time

from job import *
from selenium import webdriver
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.support.select import Select
from selenium.common import NoSuchElementException

from dotenv import load_dotenv

driver = webdriver.Chrome()
actions = ActionChains(driver)

jobs = JobManager()


load_dotenv()

email = os.getenv("EMAIL")
