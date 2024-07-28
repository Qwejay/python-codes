from flask import Flask, jsonify, request, render_template, send_file
import random
import requests
from lxml import html
from collections import Counter

app = Flask(__name__)

# 实时获取区间比、奇偶的概率
def ssq_interval_parity_data():
    # 请求网页
    url = "https://m.cz89.com/zst/ssq?pagesize=120"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # 确保请求成功

    # 解析HTML
    tree = html.fromstring(response.text)

    # 定义XPath表达式
    interval_xpath = "/html/body/div[2]/div/div/div[2]/div[2]/table/tbody[1]/tr[{}]/td[60]"
    parity_xpath = "/html/body/div[2]/div/div/div[2]/div[2]/table/tbody[1]/tr[{}]/td[61]"

    # 提取所有需要的数据
    data = []
    second_data = []
    for i in range(1, 121):  # tr[1] 到 tr[120]
        path = interval_xpath.format(i)
        second_path = parity_xpath.format(i)
        value = tree.xpath(path)
        second_value = tree.xpath(second_path)
        if value and second_value:  # 如果找到元素
            data.append(value[0].text_content().strip())
            second_data.append(second_value[0].text_content().strip())

    # 使用Counter统计元素出现次数
    counter = Counter(data)
    second_counter = Counter(second_data)

    # 计算总数量
    total = sum(counter.values())
    second_total = sum(second_counter.values())

    # 创建列表来存储结果
    items_str = []
    percentages = []
    second_items_str = []
    second_percentages = []

    # 计算每个元素及其出现的次数和百分比
    for item, count in counter.items():
        items_str.append(item)
        percentage = (count / total) * 1
        percentages.append(percentage)

    for second_item, second_count in second_counter.items():
        second_items_str.append(second_item)
        second_percentage = (second_count / second_total) * 1
        second_percentages.append(second_percentage)

    # 将items_str中的每个元素转换为整数列表
    items_int = [list(map(int, item.split(':'))) for item in items_str]
    second_items_int = [list(map(int, item.split(':'))) for item in second_items_str]

    # 对items_int和percentages进行排序
    sorted_results = sorted(zip(items_int, percentages), key=lambda x: x[0])
    items_sorted, percentages_sorted = zip(*sorted_results)

    # 对second_items_int和second_percentages进行排序
    second_sorted_results = sorted(zip(second_items_int, second_percentages), key=lambda x: x[0])
    second_items_sorted, second_percentages_sorted = zip(*second_sorted_results)

    # 将items_sorted和percentages_sorted转换为列表
    items_sorted = list(items_sorted)
    percentages_sorted = list(percentages_sorted)
    second_items_sorted = list(second_items_sorted)
    second_percentages_sorted = list(second_percentages_sorted)

    return [items_sorted, percentages_sorted], [second_items_sorted, second_percentages_sorted]


def fetch_red_balls():
    url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount=&issueStart=&issueEnd=&dayStart=&dayEnd=&pageNo=1&pageSize=30&week=&systemType=PC"

    # 发送GET请求
    response = requests.get(url)

    # 检查响应状态码是否为200（成功）
    if response.status_code == 200:
        # 解析JSON响应
        data = response.json()

        # 获取最新的开奖结果
        latest_result = data['result'][0]
        red_balls_str = latest_result['red']

        # 将字符串转换为列表
        red_balls_list = [int(ball) for ball in red_balls_str.split(',')]

        return red_balls_list
    else:
        return None


def generate_numbers(items_sorted, percentages_sorted, second_items_sorted, second_percentages_sorted):
    sections = [(1, 11), (12, 22), (23, 33)]
    # 区间比例定义
    ratios = random.choices(items_sorted, weights=percentages_sorted, k=1)[0]

    picked_numbers = []
    total_sum = 0

    odd_even_ratio = random.choices(second_items_sorted, weights=second_percentages_sorted, k=1)[0]
    required_odds, required_evens = odd_even_ratio
    total_sum_list = [(40, 49), (50, 59),
                      (60, 69), (70, 79), (80, 89),
                      (90, 99), (100, 109), (110, 119),
                      (120, 129), (130, 139), (140, 149)]
    total_sum_weights = [0.01, 0.01, 0.06, 0.10, 0.11, 0.20, 0.14, 0.21, 0.11, 0.02, 0.03]
    total_sum_result = random.choices(total_sum_list, weights=total_sum_weights, k=1)[0]
    start, end = total_sum_result
    attempt = 0  # 记录循环次数
    while not start <= total_sum <= end or len([num for num in picked_numbers if num % 2 != 0]) != required_odds or len(
            [num for num in picked_numbers if num % 2 == 0]) != required_evens:
        picked_numbers.clear()
        total_sum = 0
        if attempt == 500:  # 如果循环500次没有符合的数据就跳出
            break
        for ratio, section in zip(ratios, sections):
            for _ in range(ratio):
                # 选择奇数或偶数
                if len([num for num in picked_numbers if num % 2 != 0]) < required_odds and random.choice(
                        [True, False]):
                    # 选择奇数
                    num = random.choice([n for n in range(section[0], section[1] + 1) if n % 2 != 0])
                else:
                    # 选择偶数
                    num = random.choice([n for n in range(section[0], section[1] + 1) if n % 2 == 0])

                # 确保不重复
                while num in picked_numbers:
                    num = random.choice([n for n in range(section[0], section[1] + 1) if
                                         n % 2 != 0]) if num % 2 != 0 else random.choice(
                        [n for n in range(section[0], section[1] + 1) if n % 2 == 0])

                picked_numbers.append(num)
                total_sum += num
        attempt += 1  # 新增：循环次数加1

    return picked_numbers, total_sum, ratios, odd_even_ratio


def ssq_blue_data():
    # 请求网页
    url = "https://m.cz89.com/zst/ssq/lqzs.htm?pagesize=120"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # 确保请求成功

    # 解析HTML
    tree = html.fromstring(response.text)

    # 定义XPath表达式
    interval_xpath = "/html/body/div[2]/div/div/div[2]/div[2]/table/tbody[1]/tr[{}]/td[11]"

    # 提取所有需要的数据
    data = []
    for i in range(1, 121):  # tr[1] 到 tr[120]
        path = interval_xpath.format(i)
        value = tree.xpath(path)
        if value:  # 如果找到元素
            data.append(value[0].text_content().strip())

    # 使用Counter统计元素出现次数
    counter = Counter(data)

    # 计算总数量
    total = sum(counter.values())

    # 创建列表来存储结果
    items_str = []  # 使用字符串列表收集原始数据
    percentages = []

    # 计算每个元素及其出现的次数和百分比
    for item, count in counter.items():
        items_str.append(item)  # 收集原始字符串
        percentage = (count / total) * 1
        percentages.append(percentage)

    # 将items_str中的每个元素转换为整数列表
    items_int = [list(map(int, item.split(':'))) for item in items_str]

    # 对items_int和percentages进行排序
    sorted_results = sorted(zip(items_int, percentages), key=lambda x: x[0])
    items_sorted, percentages_sorted = zip(*sorted_results)

    # 将items_sorted和percentages_sorted转换为列表
    items_sorted = list(items_sorted)
    percentages_sorted = list(percentages_sorted)

    return [items_sorted, percentages_sorted]


def back_random_nums(blue_proportion, interval_weights):
    nums = random.choices(blue_proportion, weights=interval_weights, k=1)[0]
    return nums


def has_consecutive_numbers(numbers):
    numbers.sort()  # 对列表进行排序
    for i in range(len(numbers) - 1):
        if numbers[i] + 1 == numbers[i + 1]:
            return True
    return False


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['GET'])
def generate():
    blue_proportion, interval_weights = ssq_blue_data()
    interval_data, parity_data = ssq_interval_parity_data()
    items_sorted, percentages_sorted = interval_data
    second_items_sorted, second_percentages_sorted = parity_data

    results = []
    count = 0
    while count < 10:
        try:
            back = back_random_nums(blue_proportion, interval_weights)
            numbers, total_sum, ratios, odd_even_ratio = generate_numbers(items_sorted, percentages_sorted,
                                                                          second_items_sorted, second_percentages_sorted)
            has_numbers = has_consecutive_numbers(numbers)
            max_value = max(numbers)
            min_value = min(numbers)
            span = max_value - min_value
            period = fetch_red_balls()
            set1 = set(period)
            set2 = set(numbers)
            common_elements = set1.intersection(set2)
            if len(common_elements) == 1:
                if not has_numbers:
                    result = {
                        "red_balls": sorted(numbers),
                        "blue_ball": sorted(back),
                        "span": span,
                        "total_sum": total_sum,
                        "ratios": ratios,
                        "odd_even_ratio": odd_even_ratio,
                        "common_elements": list(common_elements)  # 将 set 转换为 list
                    }
                    results.append(result)
                    count += 1
        except Exception as e:
            pass

    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)
