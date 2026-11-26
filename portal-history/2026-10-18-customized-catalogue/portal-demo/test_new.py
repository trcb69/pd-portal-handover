from playwright.sync_api import sync_playwright
import os
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1200,'height':900}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('file://'+os.path.abspath('Customized-Order-Portal-Demo.html'))
    pg.select_option('#who','Thariq Safraz')
    # new customer
    pg.click('#lnC'); pg.fill('#ncName','Coffee Manor Nawala'); print('dup:',pg.inner_text('#ncDup')[:160])
    pg.fill('#ncBill','manor'); print('bill hits',pg.locator('#ncBl div').count()); pg.locator('#ncBl div[data-new]').dispatch_event('mousedown'); print('newbill visible',pg.is_visible('#ncNewBill'))
    pg.fill('#ncName','Cafe Ora Hikkaduwa 2'); pg.fill('#nbName','Cafe Ora Hikkaduwa (Pvt) Ltd'); pg.click('#ncSave'); print('msg',pg.inner_text('#ncMsg'),'|',pg.inner_text('#sendmsg')[:90])
    # new item (copy)
    pg.fill('#q','12oz coffee manor'); pg.wait_for_selector('#ql div[data-k]'); pg.click('#ql div[data-k]')
    pg.click('#lnI'); pg.fill('#niTag','Brew House'); print('name',pg.input_value('#niName'),'| dup',pg.inner_text('#niDup')); print('bom rows',pg.locator('#niBom tr').count())
    pg.fill('#niQty','2000'); pg.click('#niSave'); print('cart rows',pg.locator('#cart tr').count(),'|',pg.inner_text('#sendmsg')[:100])
    pg.click('#send'); pg.click('#nMgr'); pg.click('#queue [data-o]'); print('SO btn disabled:',pg.is_disabled('#mk'))
    pg.screenshot(path='shot-req.png',full_page=True)
    pg.locator('[data-ic]').first.click(); print('after item created disabled:',pg.is_disabled('#mk')); pg.click('#mk'); print(pg.locator('#mgrDetail .badge').last.inner_text())
    # duplicate item
    pg.click('#nSales'); pg.click('#lnI'); pg.fill('#niBase','12oz coffee manor'); pg.locator('#niBl div[data-k]').first.dispatch_event('mousedown'); pg.fill('#niTag','The Coffee Manor'); print('dup item msg:',pg.inner_text('#niDup')[:100])
    print('errors',errs); b.close()
