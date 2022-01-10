# -*- coding: utf-8 -*-
import scrapy
from pyquery import PyQuery as pq
import requests
import re
from xiaoqu.items import XiaoquItem
from scrapy.http import Request


class XiaoquSpiderSpider(scrapy.Spider):
    name = 'xiaoqu_spider'
    # 获取所有城市链接
    url = 'http://sz.loupan.com/index.php/jsdata/common?_=1579245949843'
    response = requests.get(url).text
    urls = list(set(re.findall('http://\w+?.loupan.com', response)))
    url_delete = (
        'http://app.loupan.com', 'http://www.loupan.com', 'http://public.loupan.com', 'http://user.loupan.com')
    for url in urls:
        if url in url_delete:
            urls.remove(url)
    urls = ['http://dz.loupan.com','http://lc.loupan.com','http://binzhou.loupan.com','http://heze.loupan.com','http://jn.loupan.com','http://qd.loupan.com','http://wf.loupan.com','http://zb.loupan.com','http://yt.loupan.com','http://weihai.loupan.com','http://linyi.loupan.com','http://rz.loupan.com','http://jining.loupan.com','http://taian.loupan.com','http://dy.loupan.com','http://zaozhuang.loupan.com']
    def start_requests(self):
        headers = self.settings.get('headers')
        for start_urls in self.urls:
            start_url = start_urls + '/community/' 
            response = requests.get(start_url)
            doc = pq(response.text)
            page_lis = re.findall(r'/(\w+)',doc('.pageCounts').text())
            page_lis = int(page_lis[0])
            for i in range(1,page_lis):
                if i > 1:
                    start_url2 = start_url+'p'+str(i) + '/'
                else:
                    start_url2 = start_url
                response = requests.get(start_url2)
                doc = pq(response.text)
                lis = doc('.list li .text h2 a')
                li_doc = pq(lis).items()
                for li in li_doc:
                    url = li('a').attr('href')
                    yield Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        doc = pq(response.text)
        item = XiaoquItem()

        url = doc('.pos > a:nth-child(4)').attr('href')  # 小区链接
        item['url'] = url  # 小区链接

        name = doc('.top .t p').text()  # 小区名
        item['name'] = name  # 小区名

        # 根据网页获得小区模糊地址，再通过百度地图API获取经纬度
        addres = doc('.text_nr.bug2').text()  # 小区地址
        if len(addres)==0:
            addres = doc('.adr').attr('title')
            city = doc('.inner-postion box .a').text() #+ '市'
            print(city)
            #city = ''.join(re.findall('(\w+)市', addres)) + '市'
            addres = ''.join(re.findall('市(\w+)', addres))
            districts= doc('.adr >a').text()
        else:
            citys = doc('.pos > a:nth-child(2)').text()
            city = ''.join(re.findall('(\w+)小区', citys)) + '市'
            districts = doc('span.font_col_o > a').text()  # 所属区
        address = city + districts + addres + name  # 所属详细地址
        # 将地址传入api获取省市区
        location = self.location(address)
        coord = location['coord']  # 经纬度
        item['coord'] = coord
        province = location['province']  # 省
        item['province'] = province
        city = location['city']  # 市
        item['city'] = city
        district = location['district']  # 区
        item['district'] = district
        adcode =  location['adcode'] 
        item['adcode'] = adcode
        item['detail_address'] = province + city + district + addres + name  # 详细地址

        id = ''.join(re.findall('\d+', url))
        around_url = 'http://sz.loupan.com/community/around/' + id + '.html'  # 周边信息网址
        response = requests.get(around_url)
        around_doc = pq(response.text)
        traffic = around_doc('.trend > p:nth-child(7)').text()  # 交通
        item['traffic'] = traffic.replace('m', 'm,')  # 交通

        prices = doc('div.price > span.dj').text()  # 参考价格
        if prices == '暂无数据' or len(prices)==0 :
            price = None
            item['price'] = price
        else:
            price = int(prices)
            item['price'] = price

        item['property_type'] = doc('ul > li:nth-child(1) > span.text_nr').text()  # 物业类型

        property_fees = doc('ul > li:nth-child(2) > span.text_nr').text()  # 物业费
        if property_fees == '暂无数据' or len(property_fees)==0 or property_fees =='价格待定':
            property_fee = None
            item['property_fee'] = property_fee
        else:
            property_fee = float(''.join(re.findall('\d*\.\d*', property_fees)))
            item['property_fee'] = property_fee

        areas = doc('ul > li:nth-child(3) > span.text_nr').text()  # 总建面积
        if areas == '暂无数据' or len(property_fees)==0:
            area = None
            item['area'] = area
        else:
            area = int(''.join(re.findall('\d*', areas)))
            item['area'] = area

        house_counts = doc('ul > li:nth-child(4) > span.text_nr').text()  # 总户数
        if house_counts == '暂无数据' or len(house_counts)==0 or house_counts == '' :
            house_count = None
            item['house_count'] = house_count
        else:
            house_count = int(''.join(re.findall('\d*', house_counts)))
            item['house_count'] = house_count

        completion_times = doc('ul > li:nth-child(5) > span.text_nr').text()  # 竣工时间
        if completion_times in ('暂无数据', '', None):
            completion_time = None
            item['completion_time'] = completion_time
        else:
            completion_time = int(''.join(re.findall('\d*', completion_times)))
            item['completion_time'] = completion_time

        item['parking_count'] = doc('ul > li:nth-child(6) > span.text_nr').text()  # 停车位

        plot_ratios = doc('ul > li:nth-child(7) > span.text_nr').text()  # 容积率
        if plot_ratios == '暂无数据' or plot_ratios == ''  or len(plot_ratios)==0:
            plot_ratio = None
            item['plot_ratio'] = plot_ratio
        else:
            plot_ratio = float(''.join(re.findall('\d*\.\d*', plot_ratios)))
            item['plot_ratio'] = plot_ratio

        greening_rates = doc('ul > li:nth-child(8) > span.text_nr').text()  # 绿化率
        if greening_rates == '暂无数据' or len(greening_rates)==0:
            greening_rate = None
            item['greening_rate'] = greening_rate
        else:
            greening_rate = ''.join(re.findall('\d*\.\d*%', greening_rates))
            item['greening_rate'] = greening_rate

        item['property_company'] = doc('div.ps > p:nth-child(1) > span.text_nr').text()  # 物业公司
        item['developers'] = doc('div.ps > p:nth-child(2) > span.text_nr').text()  # 开发商
        yield item

        lis = doc('body > div.pages > div.main.esf_xq > div > div.main > div.tj_esf > ul > li')
        li_doc = pq(lis).items()
        for li in li_doc:
            url = li('div.text > a').attr('href')
            yield Request(url=url, callback=self.parse)

    # 调用经高德地图API，获取经纬度与详细地址
    def location(self, detail_address):
        url = "https://restapi.amap.com/v3/geocode/geo?address=" + detail_address + "&key=d89d964da70dc6769d257c929f82e4c0"
        response = requests.get(url).json()
        geocodes = response['geocodes']
        for geocode in geocodes:
            coord = geocode['location']
            province = geocode['province']
            city = geocode['city']
            district = geocode['district']
            adcode = geocode['adcode']
            local = {'coord': coord, 'province': province, 'city': city, 'district': district,'adcode': adcode}
            return local
