from element import BasePageElement #in here, import the class containing all the elements from your target page 
from locators import MainPageLocators #here, we should find all the locators for your target page

class PurchaseOrderTableElement(BasePageElement):
    #This class gets the table from the specified locator
    
    #locator for table
    table = 'grid'
    #locator for table body
    body = 'tbody'
    #locator for rows
    rows = 'tr'
    supplier_column = 'grip_supplier'
    supplier_input = 'id_name'

class BasePage(object):
    def __init__(self, driver):
        self.driver = driver
    

class PurchaseOrderPage(BasePage):
    #purchase order page action method come here
    
    #declaring variable that will contain the retrieved table
    purchase_order_table_element = PurchaseOrderTableElement()
    
    def is_title_matches(self):
        return "Purchase orders" in self.driver.title
