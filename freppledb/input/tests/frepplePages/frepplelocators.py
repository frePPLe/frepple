from selenium.webdriver.common.by import By
#common action's element locators go here
class BasePageLocators(object):
    NAVIGATOR_BREADCUMBS_HOME = (By.CSS_SELECTOR, "#breadcrumbs > li > a[href='/']")
    NAVIGATOR_BREADCUMBS_PURCHASE_ORDERS = (By.CSS_SELECTOR, "#breadcrumbs > li > a[href='/data/input/purchaseorder/']")
#table page locators go here
#Change class into Table Page Locators
class PurchaseOrderPageLocators(object):
    PURCHASE_ORDER_TABLE_DEFAULT = (By.CSS_SELECTOR, "table[id='grid']")
    PURCHASE_ORDER_TABLE_BODY = (By.CSS_SELECTOR, "tbody")
    PURCHASE_ORDER_TABLE_ROWS = (By.CSS_SELECTOR, "tr")
    #PURCHASE_ORDER_TABLE_SUPPLIER_COLUMN = (By.CSS_SELECTOR, 'td[aria-describedby="grip_supplier"]')
    PURCHASE_ORDER_TABLE_SAVE_BUTTON = (By.CSS_SELECTOR, 'input[id="save"]')
    PURCHASE_ORDER_TABLE_UNDO_BUTTON = (By.CSS_SELECTOR, 'input[id="undo"]')
    PURCHASE_ORDER_TABLE_SELECT_ACTION = (By.CSS_SELECTOR, 'button[id="actions1"]')
    PURCHASE_ORDER_TABLE_SELECT_ACTION_MENU = (By.CSS_SELECTOR, 'ul[id="actionsul"]')
    
    def actionLocator(actionTofind):
        return (By.CSS_SELECTOR, "li>a[name='"+actionTofind+"'")

class SupplierPageLocators(object):
    pass