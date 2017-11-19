const puppeteer = require('puppeteer');
require('dotenv').config();

const START_PAGE = 'https://appserv6.admin.uillinois.edu/appslogin/servlet/appslogin?appName=edu.uillinois.aits.HireTouchHelper';

(async () => {
    const browser = await puppeteer.launch(); // {headless: false});
    const page = await browser.newPage();
    await page.goto(START_PAGE);

    await page.click('#netid');
    await page.keyboard.type(process.env.NETID);
    await page.click('#easpass');
    await page.keyboard.type(process.env.PASSWORD);
    await page.click('#easFormId > input');
    await page.waitForNavigation();
    console.log((await page.cookies()).map(
        (x) => x.name + '=' + x.value).reduce(
        (x,y) => x + '; ' + y)
        );

    await browser.close();
})();
