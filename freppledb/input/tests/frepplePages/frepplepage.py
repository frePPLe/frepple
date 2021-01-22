from freppleelement import BasePageElement #in here, import the class containing all the elements from your target page 
from frepplelocators import MainPageLocators #here, we should find all the locators for your target page

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
    #locators for upper left side of table
    save = 'save'
    undo = 'undo'
    select_action = 'actions1'
    select_action_menu = 'actionsul'
    select_action_statuses = ("proposed","approved","confirmed","completed","closed")

class BasePage(object):
    NAV_MENU_LEFT = ("Sales", "Inventory", "Capacity", "Purchasing", "Manufacturing", "Admin", "My Reports", "Help")
    
    
    def __init__(self, driver):
        self.driver = driver
    
    def login(self):
        
    
    def return_home_with_breadcrumbs(self):
        
    

class PurchaseOrderPage(BasePage):
    #purchase order page action method come here
    
    #declaring variable that will contain the retrieved table
    purchase_order_table_element = PurchaseOrderTableElement()
    
    def is_title_matches(self):
        return "Purchase orders" in self.driver.title
    
    def click_save_button(self):
        
    
    def click_undo_button(self):
        
    
    def select_action(self): # method that will select an action from the select action dropdown
        
    
    def multiline_checkboxes_check(number_of_line, checkbox_column): # method that will check a certain number of checkboxes in the checkbox column
        
    
    def click_target_row_colum(target_row, target_column): # method that clicks of the table cell at the targeted row and column
