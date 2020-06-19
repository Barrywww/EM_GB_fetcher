import json
import requests


# 获取股票列表
def get_code_list():
    code_list = list()
    # 备注: f12表示股票代码, f14表示股票名称
    http_url = "http://48.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=8000&fs=m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23&fields=f12,f14";
    with requests.get(http_url, data=None, timeout=20) as http:
        result = json.loads(http.content.decode("utf-8"))
        data = result["data"]
        item_count = data["total"]
        item_array = data["diff"]
        for i in range(0, item_count):
            item = item_array[str(i)]
            code_list.append(item["f12"])
        code_list.sort()
    return code_list


if __name__ == "__main__":
    code_list = get_code_list()
    print(code_list)
