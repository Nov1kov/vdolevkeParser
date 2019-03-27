# coding utf-8
import logging
import base64
import csv
import re

from lxml import etree
from grab.spider import Spider, Task


class VdolevkeSpider(Spider):
    initial_urls = ['http://www.vdolevke.ru/cities/1/company/']

    rootPath = 'http://www.vdolevke.ru'
    companyPath = 'http://www.vdolevke.ru/cities/1/company/'

    def prepare(self):
        self.result_file = csv.writer(open('result.txt', 'w'))

    def task_initial(self, grab, task):
        for elem in grab.doc.select('//li[@class="clearfix item"]/a/@href'):
            yield Task('company', url=VdolevkeSpider.rootPath + str(elem.node()))

        nextLinkSelector = grab.doc.select('//div[@class="cell"]/div/a[@class="next"]/@href')
        if len(nextLinkSelector) > 0:
            yield Task('initial', url=VdolevkeSpider.companyPath +
                                      str(nextLinkSelector[0].node()))
        else:
            logging.warning('конец списка!')

    def task_company(self, grab, task):

        current_field = ''
        # ФИРМЕННОЕ НАИМЕНОВАНИЕ
        company_name = grab.doc.select('//h1')[0].text()

        year_begin = ''
        adress = ''
        company_line = ''
        new_building = ''
        city = 'Санкт - Петербург'  # TODO город известен с самого начало
        email = ''
        tel_number = ''
        website = ''
        ex_tel_number = ''
        house_number = ''
        office = ''

        for elem in grab.doc.select('//div[@class="info-params"]/dl/dt | //div[@class="info-params"]/dl/dd'):

            if elem.node().tag == 'dt':
                current_field = elem.text()

            elif elem.node().tag == 'dd':
                # Улица
                # Дом/корпус
                if current_field == 'Адрес':
                    adress = elem.node().text

                    # город / регион
                elif current_field == 'Регион':
                    city = elem.node().text

                    # ГОД ОСНОВАНИЯ
                elif current_field == 'Год основания':
                    year_begin = elem.text()

                    # РОД ДЕЯТЕЛЬНОСТИ
                elif current_field == 'Профиль':
                    company_line = elem.text()

                    # Кол-во новостроек
                elif current_field == 'Новостроек':
                    new_building = elem.text()

                    # Коммерческие телефоны
                elif current_field == 'Телефон':
                    tree = etree.fromstring(elem.html())
                    s = base64.b64decode(tree.xpath('/dd/noindex/a/@data-code')[0]).decode("utf-8")
                    list_numbers = s.replace('&nbsp;', ' ').split(',')
                    tel_number = list_numbers[0]
                    if len(list_numbers) > 1:
                        ex_tel_number = list_numbers[1]

                        # Эл. почта
                elif current_field == 'Email':
                    email = decodeAndParse(elem, r'href=[\'"]mailto:?([^\'" >]+)')
                    # сайт
                elif current_field == 'Сайт':
                    website = decodeAndParse(elem, r'href=[\'"]?([^\'" >]+)')

                    # офис
                elif current_field == 'Доп. адреса':
                    office = elem.node().text

                    # игнорируемые поля
                elif current_field == 'Обсуждений' or current_field == 'Жителей' or current_field == 'Типы объектов' or current_field == 'Класс жилья':
                    pass
                elif current_field != '':
                    logging.warning('не учтенное поле: ' + current_field)

        result_list = [company_name,
                       year_begin,
                       company_line,
                       new_building,
                       tel_number,
                       ex_tel_number,
                       email,
                       website,
                       city,
                       adress,
                       house_number,
                       office
                       ]
        logging.info('add ' + ", ".join(result_list))
        self.result_file.writerow(result_list)


def decodeAndParse(elem, regStr):  # parse href attribute value
    tree = etree.fromstring(elem.html())
    hrefData = base64.b64decode(tree.xpath('/dd/noindex/a/@data-code')[0]).decode("utf-8")
    match = re.search(regStr, hrefData)
    if match:
        return match.group(1)
    return ''


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(message)s',
                        datefmt='%H:%M:%S')

    bot = VdolevkeSpider()  # thread_number=2
    bot.run()
