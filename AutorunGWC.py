import time, datetime, os.path
import sys
from selenium import webdriver as wb
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

LOCATION_CHECK_TIME = 1 # wait x seconds to check locations, used in is_moving()
USER_EMAIL = "alexander.govan@samsara.com"
OBD_TRY_COUNT = 10
SAVEPATH = "/Users/alexgovan/Documents/OBD_Outputs"

def enable_super_user(page_name):
    # DropDown to enable superuser 
    toprightdropdown = page_name.find_elements(By.CSS_SELECTOR, ".dropdown-toggle")
    user_dropdown = toprightdropdown[1]
    user_dropdown.click()

    # Enable superuser mode
    enable_super = page_name.find_element(By.XPATH, "//*[contains(text(),'Enable Superuser Mode')]")
    enable_super.click()

def is_moving(page_name):
    # Get the starting location
     s_loc = page_name.find_element(By.XPATH, ".//td[text() = 'Location']//parent::tr").text
     print("Waiting for the vehicle to move")
     while True:
        time.sleep(LOCATION_CHECK_TIME) 
        current_location = page_name.find_element(By.XPATH, ".//td[text() = 'Location']//parent::tr").text
        # Check to see if vehicle is moving
        if s_loc != current_location:
            break   

def get_obd_info(page_name):
    OBD = page_name.find_element(By.XPATH, "//*[contains(text(),'connected true')]").text
    count = 0
    log = ""
    print(OBD[10:14])
    time.sleep(5)
    while OBD[10:14] != "true" and count < OBD_TRY_COUNT:
        # move back to the gateway page
        gateway_page = page_name.back()
        # wait until vehicle moves again
        is_moving(gateway_page)
        # Move to gateway commands page
        gateway_page.find_element(By.XPATH, "//*[contains(text(),'gateway commands')]").click()
        # Run the OBD gateway command
        gateway_page.find_element(By.XPATH, "//*[contains(text(),'OBD')]").click()
        
        # Grab the OBD output
        OBD = gateway_page.find_element(By.XPATH, "//*[contains(text(),'connected true')]").text
        log.append(OBD + "\n")

        time.sleep(20)

        # increment counter for number of retries
        count += 1
        print "OBD did not read correctly"

    if count >= OBD_TRY_COUNT:
        return "Could not get OBD data after retries:" + "\n" + log
    return OBD

#TODO: Move to class
#TODO: Thread this
def autorunGWC(gw_id, USER_PASSWORD):
    # This is the path to the chrome webdriver, OSX 10 disallows putting drivers in general path
    wbLoc = "/Users/alexgovan/Documents/Python_Club/support_programming/AutoRunGWC/chromedriver"
    # Force script to open up incognito window
    # chrome_options = wb.ChromeOptions()
    # chrome_options.add_argument("--incognito")
    
    browser = wb.Chrome(wbLoc) # Using chrome as the default browser
    browser.implicitly_wait(10) # Wait 10 seconds before time out error
    url = "https://cloud.samsara.com/signin"
    browser.get(url)
    email = browser.find_element(By.CLASS_NAME, "form-control") # email field
    email.send_keys(USER_EMAIL)
    browser.find_element(By.CLASS_NAME, "Button--block").click()
    
    # TODO: Figure out how to not manual advance to next step in password entry. Getting blocked with dev notes from John
    # Password Page

    browser.find_element(By.ID, "identifierNext").click()
    password = browser.find_element(By.NAME, "password")
    password.send_keys(USER_PASSWORD)
    time.sleep(1)
    browser.find_element(By.ID, "passwordNext").click()

    # Enable superuser
    enable_super_user(browser)    

    # Search for the specific gateway by ID
    browser.get("https://cloud.samsara.com/devices/" + gw_id + "/show")

    # I think you may need to pause here to allow for page to load fully
    # TODO: Write smarter conditional before moving to next line. Perhaps wait for owl icon to load, assuming that's the last 
    # thing to render on page.
    time.sleep(2)

    # Enable superuser again. Page forgets previous superuser input
    # enable_super_user(browser)        
    
    # Wait until vehicle moves
    is_moving(browser)

    # Move to gateway commands page
    browser.find_element(By.XPATH, "//*[contains(text(),'gateway commands')]").click()

    # Run the OBD gateway command
    browser.find_element(By.XPATH, "//*[contains(text(),'OBD')]").click()

    # Copy the resulting text
    # TODO: Write conditionals so that if this fails, or doesn't return expected value, it either tries again or fails
    obd_output = get_obd_info(browser)
    date = datetime.datetime.now()
    file_desc = str(gw_id)+ "_OBD_" + str(date.month) + "-" + str(date.day) + "-" + str(date.year) + "__" + str(date.hour) + ":" + str(date.minute)
    save_path = SAVEPATH
    file_name = os.path.join(save_path, file_desc+".txt")
    obd_file = open(file_name, "w")
    obd_file.write(obd_output)
    obd_file.close()

    time.sleep(300)

if __name__ == '__main__':
    # Add the gateway SN here, only accepts one currently
    # TODO: Allow array input
    autorunGWC("212014918216057", sys.argv[1])
