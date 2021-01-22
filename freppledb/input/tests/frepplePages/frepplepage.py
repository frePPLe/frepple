from freppleelement import BasePageElement #in here, import the class containing all the elements from your target page 
from frepplelocators import PurchaseOrderPageLocators #here, we should find all the locators for your target page


class SupplierEditInputElement(BasePageElement):
    locator = 'input[id=id_name]'


"""class PurchaseOrderTableSelectActionMenuElement(BasePageElement):
    select_action_statuses = ("proposed","approved","confirmed","completed","closed")"""

class BasePage(object):
    NAV_MENU_LEFT = ("Sales", "Inventory", "Capacity", "Purchasing", "Manufacturing", "Admin", "My Reports", "Help")
    
    
    def __init__(self, driver):
        self.driver = driver
    
    def login(self):
        
    
    def go_home_with_breadcrumbs(self):
        pass
    
    def go_back_to_page_with_breadcrumbs(self, targetPageName):
        
    

class PurchaseOrderPage(BasePage):
    #purchase order page action method come here
    
    #declaring variable that will contain the retrieved table
    purchase_order_table_element = PurchaseOrderTableElement()
    
    def is_title_matches(self):
        return "Purchase orders" in self.driver.title
    
    def click_save_button(self):
        save_button = self.driver.find_element(*PurchaseOrderPageLocators)
    
    def click_undo_button(self):
        
    
    def select_action(self): # method that will select an action from the select action dropdown
        
    
    def multiline_checkboxes_check(self, number_of_line, checkbox_column): # method that will check a certain number of checkboxes in the checkbox column
        
    
    def click_target_row_colum(self, target_row, target_column): # method that clicks of the table cell at the targeted row and column
        
    
class SupplierEditPage(BasePage):
    
    def is_title_matches(self):
        return "Supplier" in self.driver.title
    
    def click_save_button(self):
        
    
    def click_save_add_button(self):
        
    
    def click_save_continue_editing(self):
        
    
    def click_delete_supplier(self):
        
    
    def input_supplier_name(self, supplier_new_name):
        
    
    def input_supplier_description(self, supplier_new_description):
        
    


