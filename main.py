import copy
import json
import os
import time

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
storage_dir = list()
storage_file = dict()
namespaces = dict()


# app.config['JSON_AS_ASCII'] = False
# app.config['JSONIFY_MIMETYPE'] = "application/json;charset=utf-8"

def load_namespace():
    global namespaces
    with open("namespaces.json", "r") as f:
        namespaces = json.load(f)


def get_dir_list(dir_name):
    """目录结构转dict"""
    result = list()
    for name in sorted(os.listdir(dir_name), reverse=True):
        # print(name)
        fullname = dir_name + "/" + name
        if os.path.isdir(fullname):
            # print("dir", name)
            result.append({"name": name, "label": name, "children": get_dir_list(fullname)})
        elif os.path.isfile(fullname):
            # print("file", name)
            if name.endswith(".json"):
                result.append({"value": fullname, "label": name.split(".json")[0]})
            elif name.endswith(".py"):
                result.append({"value": fullname, "label": name.split(".py")[0]})
    # print(result)
    return result


def load_storage():
    """加载存储"""
    global storage_dir, storage_file
    storage_dir = get_dir_list("storage")
    # print(storage_dir)

    for root, dirs, files in os.walk("storage"):
        for name in files:
            filename = os.path.join(root, name)
            if filename.endswith(".json"):
                # print(filename)
                with open(filename) as f:
                    storage_file[filename] = json.load(f)
            elif filename.endswith(".py"):
                # print(filename)
                with open(filename) as f:
                    res = eval(f.read())
                    storage_file[filename] = res
    # print(storage_file.keys())


def exec_request(method, url, params=None, headers=None, data=None, cookies=None):
    # 执行请求
    try:
        req = requests.request(method=method, url=url, params=params, headers=headers, data=data, cookies=cookies)
        # 构造结果
        result = {
            "error_code": 0,
            "status_code": req.status_code,
            "text": req.text,
            "headers": dict(req.headers),
            "cookies": dict(req.cookies)
        }
    except Exception as e:
        # 构造结果
        result = {
            "error_code": 1,
            "text": str(e)
        }
    return result


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route('/api/proxy', methods=["POST"])
def api_proxy():
    """url,method,headers,params,body"""

    # 获取参数
    datas = json.loads(request.get_data(as_text=True))
    url = datas['url']
    method = datas['method']
    headers_list = datas['headers']
    params_list = datas['params']
    data = datas['data']
    cookies_list = datas['cookies']

    # 处理参数
    headers = {}
    for kv in headers_list:
        if kv["key"]:
            headers[kv["key"]] = kv["value"]

    params = {}
    for kv in params_list:
        if kv["key"]:
            params[kv["key"]] = kv["value"]

    cookies = {}
    for kv in cookies_list:
        if kv["key"]:
            cookies[kv["key"]] = kv["value"]

    # 执行请求
    result = exec_request(method=method, url=url, params=params, headers=headers, data=data, cookies=cookies)

    # 保存请求
    name = time.strftime("%Y%m%d_%H%M%S", time.localtime()) + "_" + url.split("/")[-1]
    with open("storage/_history/" + name + ".json", "w")as f:
        json.dump({
            "name": name,
            "url": url,
            "method": method,
            "headers": headers,
            "params": params,
            "data": data,
            "cookies": cookies,
            "result": result
        }, f)
    load_storage()

    # 返回结果

    if "headers" in result:
        headers_tmp = result["headers"]
        result["headers"] = []
        for key, value in headers_tmp.items():
            result["headers"].append({
                "key": key,
                "value": value
            })
    else:
        result["headers"] = []

    if "cookies" in result:
        cookies_tmp = result["cookies"]
        result["cookies"] = []
        for key, value in cookies_tmp.items():
            result["cookies"].append({
                "key": key,
                "value": value
            })
    else:
        result["cookies"] = []

    return jsonify(result)


@app.route('/api/dir', methods=['GET'])
def api_dir():
    """返回存储列表"""
    global storage_dir
    return jsonify(storage_dir)


@app.route('/api/ns', methods=['GET'])
def api_as():
    """返回namespace列表"""
    global namespaces
    return jsonify(sorted(list(namespaces.keys())))


@app.route('/api/file', methods=['GET'])
def api_file():
    """返回文件"""
    global storage_file, namespaces
    filename = request.args.get("filename")
    ns = request.args.get("namespace")
    # print(filename)
    if filename in storage_file:
        data = copy.deepcopy(storage_file[filename])

        if ns:
            data["url"] = data["url"].format(**namespaces[ns])

        headers_tmp = data["headers"]
        data["headers"] = []
        for key, value in headers_tmp.items():
            if ns:
                value = value.format(**namespaces[ns])
            data["headers"].append({
                "key": key,
                "value": value
            })

        params_tmp = data["params"]
        data["params"] = []
        for key, value in params_tmp.items():
            if ns:
                value = value.format(**namespaces[ns])
            data["params"].append({
                "key": key,
                "value": value
            })

        # cookies_tmp = data["cookies"]
        # data["cookies"] = []
        # for key, value in cookies_tmp.items():
        #     data["cookies"].append({
        #         "key": key,
        #         "value": value
        #     })

        if "result" in data:

            headers_tmp = data["result"]["headers"]
            data["result"]["headers"] = []
            for key, value in headers_tmp.items():
                data["result"]["headers"].append({
                    "key": key,
                    "value": value
                })

            cookies_tmp = data["result"]["cookies"]
            data["result"]["cookies"] = []
            for key, value in cookies_tmp.items():
                data["result"]["cookies"].append({
                    "key": key,
                    "value": value
                })

        else:

            data["result"] = {
                "error_code": 0,
                "status_code": "",
                "text": "",
                "headers": [],
                "cookies": []
            }

        return jsonify(data)
    return "File not found!", 404


if __name__ == "__main__":
    load_namespace()
    load_storage()
    app.run(port=8080, host="0.0.0.0")
