import requests
import re
from threading import Thread
import time
from queue import Queue

# 登录URL
login_url = "https://oj.socoding.cn/site/login"

# re正则表达式
csrf_pattern = r'name="_csrf" value="(.+?)"'
error_pattern = r'<div class="invalid-feedback">([^<]+)</div>'

# 请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

# 用户名和密码，替换为实际的值
username = "test"
password = "test"

# 设置线程数和每个线程的请求次数 (10*40 模拟AK杯最多400人同时登陆)
threads_count = 10  # 线程数
requests_per_thread = 40  # 每个线程的请求次数

# 创建一个队列用于线程间通信
print_queue = Queue()


# 登录函数
def login():
    try:
        # 发送GET请求
        response = requests.get(login_url, headers=headers)
        # 从响应内容中提取_csrf
        csrf = re.search(csrf_pattern, response.text).group(1)
        # 获取cookie
        cookie = response.cookies
        # 表单数据
        form_data = {
            "_csrf": csrf,
            "LoginForm[username]": username,
            "LoginForm[password]": password,
            "LoginForm[rememberMe]": "0",
            "login-button": "",
        }
        # 发送POST请求
        response = requests.post(
            login_url, headers=headers, data=form_data, cookies=cookie
        )
        # 判断登录是否成功，并将结果放入队列
        if response.url == "https://oj.socoding.cn/":
            print_queue.put("登录成功")
        else:
            error = re.search(error_pattern, response.text)
            print_queue.put(f"登录失败 {error.group(1)}")
    except Exception as e:
        print_queue.put(f"登录过程中发生异常: {e}")


# 写线程函数，用于从队列中获取消息并打印（主要解决多线程打印不同步的问题）
def print_worker():
    while True:
        message = print_queue.get()
        if message == "quit":
            break
        print(message)
        print_queue.task_done()


# 压力测试函数
def stress_test(num_threads, num_requests):
    # 创建并启动写线程
    print_thread = Thread(target=print_worker)
    print_thread.start()

    # 创建线程列表
    threads = []
    # 启动线程
    for i in range(num_requests):
        for j in range(num_threads):
            thread = Thread(target=login)
            threads.append(thread)
            thread.start()
        # 等待所有线程完成
        for thread in threads:
            thread.join()

    # 告诉写线程退出
    print_queue.put("quit")
    # 等待写线程完成
    print_thread.join()


if __name__ == "__main__":
    # 开始压力测试
    start_time = time.time()
    stress_test(threads_count, requests_per_thread)
    end_time = time.time()
    # 打印测试结果
    print(f"压力测试完成，耗时：{end_time - start_time}秒")
