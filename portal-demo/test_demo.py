from playwright.sync_api import sync_playwright
import os
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1200,'height':900}); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e))); pg.on('console',lambda m:m.type=='error' and errs.append(m.text))
    pg.goto('file://'+os.path.abspath('Customized-Order-Portal-Demo.html'))
    pg.select_option('#who','Thariq Safraz'); 
    pg.fill('#q','12oz coffee manor'); pg.wait_for_selector('#ql div[data-k]')
    print('suggestions',pg.locator('#ql div[data-k]').all_inner_texts()[:3])
    pg.click('#ql div[data-k]'); pg.focus('#cq'); pg.wait_for_selector('#cl div[data-k]'); print(pg.locator('#cl div').all_inner_texts()[:2])
    pg.click('#cl div[data-k]'); 
    print('qty',pg.input_value('#qty'),'price',pg.input_value('#price'),'nat',pg.input_value('#nat'),'chips',pg.locator('#chips').inner_text(),'variants',pg.locator('#variants').is_visible())
    pg.screenshot(path='shot-sales.png',full_page=True)
    pg.click('#addl'); pg.click('#send'); pg.click('#nMgr'); pg.click('#queue [data-o]'); pg.screenshot(path='shot-mgr.png',full_page=True)
    pg.click('#mk'); print(pg.locator('#mgrDetail .badge').last.inner_text()); pg.screenshot(path='shot-mgr2.png',full_page=True)
    print('errors',errs); b.close()
