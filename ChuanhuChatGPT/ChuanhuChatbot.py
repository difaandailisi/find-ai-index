# import markdown
# 导入csv库，用于处理CSV格式数据
# import markdown
import csv
import json
# 导入JSON库，用于处理JSON格式数据
# import openai
import os
# 导入os库，用于与操作系统交互
import sys

import gradio as gr
# 导入Gradio库，用于构建交互式UI
import requests

# 导入sys库，用于Python解释器相关的操作
# 导入requests库，用于进行网络请求

my_api_key = ""  # 在这里输入你的 API 密钥
HIDE_MY_KEY = False  # 如果你想在UI中隐藏你的 API 密钥，将此值设置为 True

initial_prompt = "You are a helpful assistant."
my_api_key = ""
# OpenAI API密钥
HIDE_MY_KEY = False
# 如果设置为True，API密钥将在UI中隐藏

initial_prompt = "You are a helpful assistant"
# 初始提示
API_URL = "https://api.openai.com/v1/chat/completions"
HISTORY_DIR = "history"
# 存储历史对话的目录
TEMPLATES_DIR = "templates"

# 存储模板的目录


# if we are running in Docker
if os.environ.get('dockerrun') == 'yes':
    dockerflag = True
else:
    dockerflag = False

# 如果在Docker中运行，从环境变量中获取API密钥
if dockerflag:
    my_api_key = os.environ.get('my_api_key')
    if my_api_key == "empty":
        print("Please give a api key!")
        sys.exit(1)
    # auth
    # 如果在Docker中运行，从环境变量中获取用户名和密码，并进行身份验证
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    if isinstance(username, type(None)) or isinstance(password, type(None)):
        authflag = False
    else:
        authflag = True


# 解析文本


# 定义一个函数 parse_text，输入参数为一个文本字符串 text


def parse_text(text):
    # 将文本字符串按照换行符分隔成多行，并存储在列表变量 lines 中
    lines = text.split("\n")
    # 使用列表推导式过滤掉空行，重新将过滤后的列表赋值给变量 lines
    lines = [line for line in lines if line != ""]
    # 定义一个计数器 count，用于记录代码块的数量，初始值为 0
    count = 0
    # 定义一个布尔变量 firstline，表示代码块的第一行
    firstline = False
    # 使用 enumerate 函数遍历 lines 列表中的每一行，同时获取其行号和行内容
    for i, line in enumerate(lines):
        # 如果行内容包含 ```（即开始或结束代码块），则计数器 count 加 1
        if "```" in line:
            count += 1
            # 将代码块的语言类型存储在 items 列表中，用 '`' 符号进行分割
            items = line.split('`')
            # 如果 count 为奇数（即开始代码块），则在该行前面添加一个 <pre><code> 标签，并设置样式
            if count % 2 == 1:
                lines[
                    i] = f'<pre><code class="{items[-1]}" style="display: block; white-space: pre; background-color: hsl(0, 0%, 32%); border-radius: 8px; padding: 0px 1em 1em; margin-top: 1em; font-size: initial;color: #FFF;">'
                firstline = True
            # 如果 count 为偶数（即结束代码块），则在该行前面添加一个 </code></pre> 标签
            else:
                lines[i] = f'</code></pre>'
        # 如果不是代码块，则进行字符替换和添加 <br> 标签的操作
        else:
            # 如果行号大于 0（即非第一行），且 count 为奇数（即处于代码块中），则进行字符替换操作
            if i > 0:
                if count % 2 == 1:
                    line = line.replace("&", "&amp;")
                    line = line.replace("\"", "`\"`")
                    line = line.replace("\'", "`\'`")
                    line = line.replace("<", "&lt;")
                    line = line.replace(">", "&gt;")
                    line = line.replace(" ", "&nbsp;")
                    line = line.replace("*", "&ast;")
                    line = line.replace("_", "&lowbar;")
                    line = line.replace("#", "&#35;")
                    line = line.replace("-", "&#45;")
                    line = line.replace(".", "&#46;")
                    line = line.replace("!", "&#33;")
                    line = line.replace("(", "&#40;")
                    line = line.replace(")", "&#41;")
                lines[i] = "<br>" + line
    text = "".join(lines)
    return text

    # 定义名为predict的函数，该函数接收inputs、top_p、temperature、openai_api_key、chatbot、history和system_prompt这些参数，
    # 并且还有两个可选参数retry和summary，默认值都为False。


def predict(inputs, top_p, temperature, openai_api_key, chatbot=[], history=[], system_prompt=initial_prompt,
            retry=False, summary=False):
    # repetition_penalty, top_k

    # 打印出聊天机器人（chatbot）参数的第一个元素。
    print(f"chatbot 1: {chatbot}")

    # 定义名为headers的字典，包含“Content-Type”和“Authorization”两个键值对，
    # “Authorization”键对应的值为openai_api_key参数的值。
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    # 计算history列表的长度并将其除以2，结果赋值给chat_counter变量。
    chat_counter = len(history) // 2

    # 打印出chat_counter的值。
    print(f"chat_counter - {chat_counter}")

    messages = [compose_system(system_prompt)]
    # 创建一个名为messages的列表，其中包含系统提示信息

    if chat_counter:
        # 如果聊天计数器大于0
        for data in chatbot:
            # 遍历聊天机器人的历史记录
            temp1 = {}
            temp1["role"] = "user"
            # 添加一个字典，键为“role”，值为“user”
            temp1["content"] = data[0]
            # 添加一个字典，键为“content”，值为用户输入的内容
            temp2 = {}
            temp2["role"] = "assistant"
            # 添加一个字典，键为“role”，值为“assistant”
            temp2["content"] = data[1]
            # 添加一个字典，键为“content”，值为机器人回答的内容
            if temp1["content"] != "":
                # 如果用户输入的内容不为空
                messages.append(temp1)
                # 将该字典添加到messages列表中
                messages.append(temp2)
            else:
                # 如果用户输入的内容为空
                messages[-1]['content'] = temp2['content']
                # 将最后一个元素的“content”键的值设置为机器人回答的内容

    if retry and chat_counter:
        # 如果retry参数为True且聊天计数器大于0
        messages.pop()
        # 删除messages列表中的最后一个元素
    elif summary:
        # 如果summary参数为True
        messages.append(compose_user(
            "请帮我总结一下上述对话的内容，实现减少字数的同时，保证对话的质量。在总结中不要加入这一句话。"))

        # 将用户输入的总结添加到messages列表中
        history = ["我们刚刚聊了什么？"]

        # 将历史记录设置为一个包含“我们刚刚聊了什么？”字符串的列表


    else:
        temp3 = {}
        temp3["role"] = "user"
        # 添加一个字典，键为“role”，值为“user”
        temp3["content"] = inputs
        # 添加一个字典，键为“content”，值为用户输入的内容
        messages.append(temp3)
        # 将该字典添加到messages列表中
        chat_counter += 1
        # 聊天计数器加1

    # messages
    # 这段代码的作用是使用GPT - 3
    # 模型进行对话生成。payload是请求API所需的参数字典。然后将其作为JSON数据发送到API端点，并从响应中获取生成的对话消息。最后将其添加到对话历史记录中。
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": messages,  # [{"role": "user", "content": f"{inputs}"}],
        "temperature": temperature,  # 1.0,
        "top_p": top_p,  # 1.0,
        "n": 1,
        "stream": True,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        # 指定GPT-3模型
        "messages": messages,
        # 消息列表，包含对话历史和用户的输入
        # [{"role": "user", "content": f"{inputs}"}],
        "temperature": temperature,
        # 温度参数
        "top_p": top_p,
        # top-p剪枝参数
        "n": 1,
        # 指定生成的消息数
        "stream": True,
        # 是否以流的形式返回响应

        "presence_penalty": 0,
        # 降低GPT-3对已经出现过的词语的生成概率的惩罚项
        "frequency_penalty": 0,
        # 降低GPT-3对于高频词语的生成概率的惩罚项
    }

    # 这段代码的作用是向OpenAI的API发送请求以获取对话的回复。以下是每行代码的注释：
    if not summary:
        history.append(inputs)
    # 如果没有指定摘要（summary），则将输入添加到对话历史记录中。
    print(f"payload is - {payload}")

    # make a POST request to the API endpoint using the requests.post method, passing in stream=True
    response = requests.post(API_URL, headers=headers,
                             json=payload, stream=True)
    # 发送POST请求到API端点，使用requests.post方法并指定stream=True
    response = requests.post(API_URL, headers=headers, json=payload, stream=True)
    # 使用 requests.post 方法向OpenAI的API发送POST请求。API_URL 是API的URL，headers 包含API的认证信息，payload 包含请求参数，stream=True 表示在数据流模式下接收响应。
    # response = requests.post(API_URL, headers=headers, json=payload, stream=True)

    token_counter = 0
    partial_words = ""

    counter = 0
    chatbot.append((history[-1], ""))

    # 重置token_counter、partial_words、counter的值，将最新的历史记录添加到chatbot中，其中空字符串表示尚未收到回复。

    # 使用迭代器处理API的响应
    for chunk in response.iter_lines():
        if counter == 0:
            counter += 1
            continue
        counter += 1
        # check whether each line is non-empty
        # 检查每行是否为空
        if chunk:
            # decode each line as response data is in bytes
            # 将每行数据解码，因为API的响应数据是以字节形式返回的
            try:
                # 检查返回的数据是否包含了 delta content 字段，如果没有则中止迭代
                if len(json.loads(chunk.decode()[6:])['choices'][0]["delta"]) == 0:
                    break
            except Exception as e:
                # 在出现异常的情况下，更新 chatbot 和 history 并终止迭代
                chatbot.pop()
                chatbot.append((history[-1], f"☹️发生了错误<br>返回值：{response.text}<br>异常：{e}"))
                history.pop()
                yield chatbot, history
                break
            # print(json.loads(chunk.decode()[6:])['choices'][0]["delta"]    ["content"])

            partial_words = partial_words + \
                            json.loads(chunk.decode()[6:])[
                                'choices'][0]["delta"]["content"]
            # 将 delta content 字段添加到 partial_words 变量中
            partial_words = partial_words + json.loads(chunk.decode()[6:])['choices'][0]["delta"]["content"]
            if token_counter == 0:
                history.append(" " + partial_words)
            else:
                history[-1] = parse_text(partial_words)
            chatbot[-1] = (history[-2], history[-1])
            #   chat = [(history[i], history[i + 1]) for i in range(0, len(history)     - 1, 2) ]  # convert to tuples of list
            token_counter += 1
            # resembles {chatbot: chat,     state: history}
            yield chatbot, history


# 这段代码使用 response.iter_lines() 迭代处理API响应，chunk 变量包含了响应的每一行数据。
# 代码使用 if chunk: 来检查每行是否为空，如果不为空则尝试解码并检查 delta 字段是否存在。
# 如果存在，则将 delta 字段中的 content 添加到 partial_words 变量中。如果 token_counter 为 0，
# 则将 partial_words 添加到 history 中，否则解析 partial_words 并更新 history。
# 最后，将 chatbot 中的最后一个条目更新为更新后的 history，增加 token_counter 的值并返回更新后的 chatbot 和 history。

def delete_last_conversation(chatbot, history):
    chatbot.pop()
    # 从chatbot中移除最后一项
    history.pop()
    history.pop()
    return chatbot, history
    # 返回chatbot和history


def save_chat_history(filename, system, history, chatbot):
    if filename == "":
        # 如果文件名为空字符串，返回None
        return
    if not filename.endswith(".json"):
        # 如果文件名不以.json结尾，添加.json
        filename += ".json"
    os.makedirs(HISTORY_DIR, exist_ok=True)

    # 创建目录HISTORY_DIR，如果已存在则忽略
    json_s = {"system": system, "history": history, "chatbot": chatbot}

    # 构建JSON对象
    with open(os.path.join(HISTORY_DIR, filename), "w") as f:

        # 打开文件，将JSON对象写入文件
        json.dump(json_s, f)


def load_chat_history(filename):
    with open(os.path.join(HISTORY_DIR, filename), "r") as f:
        # 打开指定的JSON文件
        json_s = json.load(f)
        # 加载JSON数据
    return filename, json_s["system"], json_s["history"], json_s["chatbot"]
    # 返回文件名、系统、历史和聊天机器人对象


def get_file_names(dir, plain=False, filetype=".json"):
    # find all json files in the current directory and return their names
    try:
        files = [f for f in os.listdir(dir) if f.endswith(filetype)]
    except FileNotFoundError:
        files = []
    if plain:
        return files
    else:
        return gr.Dropdown.update(choices=files)


# 定义了一个函数get_file_names，用于获取指定目录下所有以.json结尾的文件名。dir参数表示指定目录，filetype参数表示指定文件类型，默认为.json。plain参数表示是否以简单列表的形式返回文件名列表，若为True则返回简单列表，否则返回下拉菜单对象。该函数利用os.listdir函数获取指定目录下所有文件名，然后通过列表解析式筛选出以.json结尾的文件名，最后返回一个包含所有文件名的列表。如果出现FileNotFoundError异常，则将文件名列表设置为空列表。

def get_history_names(plain=False):
    return get_file_names(HISTORY_DIR, plain)


# 定义了一个函数get_history_names，用于获取历史记录目录下的所有历史记录文件名。该函数调用了get_file_names函数，将历史记录目录和plain参数传递给它，然后返回获取到的历史记录文件名列表。
def load_template(filename):
    lines = []
    with open(os.path.join(TEMPLATES_DIR, filename), "r", encoding="utf8") as csvfile:
        reader = csv.reader(csvfile)
        lines = list(reader)
    lines = lines[1:]
    return {row[0]: row[1] for row in lines}, gr.Dropdown.update(choices=[row[0] for row in lines])


# 定义了一个函数load_template，用于从指定的模板文件中读取模板。filename参数表示指定的模板文件名。该函数先打开指定的模板文件，然后利用csv.reader函数读取文件内容，将每行作为一个列表，将所有列表作为一个列表。接着，通过列表切片的方式去除第一行标题行，然后将剩余的行转换为字典形式，其中第一列作为键，第二列作为值。最后，该函数返回读取到的模板字典和下拉菜单对象，其中下拉菜单的选项为所有模板的文件名。


def get_template_names(plain=False):
    return get_file_names(TEMPLATES_DIR, plain, filetype=".csv")


def reset_state():
    return [], []


def compose_system(system_prompt):
    return {"role": "system", "content": system_prompt}


def compose_user(user_input):
    return {"role": "user", "content": user_input}


def reset_textbox():
    return gr.update(value='')


title = """<h1 align="center">川虎ChatGPT 🚀</h1>"""
description = """<div align=center>

由Bilibili [土川虎虎虎](https://space.bilibili.com/29125536) 开发

访问川虎ChatGPT的 [GitHub项目](https://github.com/GaiZhenbiao/ChuanhuChatGPT) 下载最新版脚本

此App使用 `gpt-3.5-turbo` 大语言模型
</div>
"""
# 以上是两个变量，存储了HTML代码，用于页面的显示。其中title存储了一个居中的标题，description存储了一个居中的描述文本和两个超链接。


with gr.Blocks() as demo:
    # 使用 Graphter 库的 Blocks() 方法创建一个新的块。

    gr.HTML(title)
    # 在块中添加一个 HTML 标题。

    keyTxt = gr.Textbox(show_label=True, placeholder=f"在这里输入你的OpenAI API-key...",
                        value=my_api_key, label="API Key", type="password", visible=not HIDE_MY_KEY).style(
        container=True)
    # 在块中添加一个文本框，让用户输入 OpenAI 的 API key。

    chatbot = gr.Chatbot()  # .style(color_map=("#1D51EE", "#585A5B"))
    # 在块中添加一个聊天机器人组件。

    history = gr.State([])
    # 创建一个空列表，用于存储对话历史记录。

    promptTemplates = gr.State({})
    # 创建一个空字典，用于存储系统提示的模板。

    TRUECOMSTANT = gr.State(True)
    # 创建一个布尔常量 True。

    FALSECONSTANT = gr.State(False)
    # 创建一个布尔常量 False。

    topic = gr.State("未命名对话历史记录")
    # 创建一个字符串常量，表示对话主题的名称。

    with gr.Row():
        # 在块中创建一个新的行。

        with gr.Column(scale=12):
            # 在行中创建一个占据 12 格的列。

            txt = gr.Textbox(show_label=False, placeholder="在这里输入").style(
                container=False)
            # 在列中添加一个文本框，让用户输入对话的内容。

        with gr.Column(min_width=50, scale=1):
            # 在行中创建一个占据 1 格的列，最小宽度为 50px。

            submitBtn = gr.Button("🚀", variant="primary")
            # 在列中添加一个提交按钮，用于发送对话内容。

    with gr.Row():
        # 在块中创建一个新的行。

        emptyBtn = gr.Button("🧹 新的对话")
        # 在行中添加一个按钮，用于清空对话历史记录。

        retryBtn = gr.Button("🔄 重新生成")
        # 在行中添加一个按钮，用于重新生成系统提示。

        delLastBtn = gr.Button("🗑️ 删除上条对话")
        # 在行中添加一个按钮，用于删除上一条对话。

        reduceTokenBtn = gr.Button("♻️ 总结对话")
        # 在行中添加一个按钮，用于总结对话内容。

    systemPromptTxt = gr.Textbox(show_label=True, placeholder=f"在这里输入System Prompt...",
                                 label="System prompt", value=initial_prompt).style(container=True)
    # 在块中添加一个文本框，让用户输入系统提示的内容。

    # 导入OPENAI库，这个库是用于OEPNAI的API接口 实现了功能。

    with gr.Accordion(label="加载Prompt模板", open=False):
        # 创建一个可以展开和收缩的Accordion组件，标签为“加载Prompt模板”，默认不展开。
        with gr.Column():
            # 在Accordion组件中创建一个Column组件。
            with gr.Row():
                # 在Column组件中创建一个Row组件。
                with gr.Column(scale=6):
                    # 在Row组件中创建一个Column组件，宽度为6个网格。
                    # 创建一个Dropdown组件，标签为“选择Prompt模板集合文件（.csv）”，选项为get_template_names(plain=True)返回的值，
                    # 并设置为单选模式。
                    templateFileSelectDropdown = gr.Dropdown(label="选择Prompt模板集合文件（.csv）",
                                                             choices=get_template_names(plain=True), multiselect=False)
                with gr.Column(scale=1):
                    # 在Row组件中创建一个Column组件，宽度为1个网格。
                    # 创建一个Button组件，标签为“🔄 刷新”。
                    templateRefreshBtn = gr.Button("🔄 刷新")
                    templaeFileReadBtn = gr.Button("📂 读入模板")
            with gr.Row():
                # 在Column组件中创建一个Row组件。
                with gr.Column(scale=6):
                    # 在Row组件中创建一个Column组件，宽度为6个网格。
                    # 创建一个Dropdown组件，标签为“从Prompt模板中加载”，选项为空，单选模式。
                    templateSelectDropdown = gr.Dropdown(label="从Prompt模板中加载", choices=[], multiselect=False)
                with gr.Column(scale=1):
                    # 在Row组件中创建一个Column组件，宽度为1个网格。
                    # 创建一个Button组件，标签为“⬇️ 应用”。
                    templateApplyBtn = gr.Button("⬇️ 应用")

    # 导入 OPENAI 库，用于实现 OPENAI 的 API 接口

    with gr.Accordion(
            label="保存/加载对话历史记录(在文本框中输入文件名，点击“保存对话”按钮，历史记录文件会被存储到Python文件旁边)",
            open=False):
        # 创建一个可展开的容器，用于保存/加载对话历史记录

        with gr.Column():
            with gr.Row():
                with gr.Column(scale=6):
                    saveFileName = gr.Textbox(
                        show_label=True, placeholder=f"在这里输入保存的文件名...", label="设置保存文件名",
                        value="对话历史记录").style(container=True)
                with gr.Column(scale=1):
                    saveBtn = gr.Button("💾 保存对话")
            # 创建一个文本框，用于输入保存的文件名，并创建一个“保存对话”按钮

            with gr.Row():
                with gr.Column(scale=6):
                    historyFileSelectDropdown = gr.Dropdown(label="从列表中加载对话",
                                                            choices=get_history_names(plain=True), multiselect=False)
                with gr.Column(scale=1):
                    historyRefreshBtn = gr.Button("🔄 刷新")
                    historyReadBtn = gr.Button("📂 读入对话")
            # 创建一个下拉菜单，用于选择历史记录，并创建一个“刷新”按钮和一个“读入对话”按钮
    # 这段代码主要是创建了一个包含了三个组件的容器，用于保存和加载对话历史记录。第一个组件是一个文本框和一个“保存对话”按钮，用于设置和保存对话历史记录的文件名；第二个组件是一个下拉菜单和一个“刷新”按钮，用于选择历史记录文件；第三个组件是一个“读入对话”按钮，用于将选定的历史记录文件读入到 GUI 中。
    # inputs, top_p, temperature, top_k, repetition_penalty
    with gr.Accordion("参数", open=False):
        top_p = gr.Slider(minimum=-0, maximum=1.0, value=1.0, step=0.05,
                          interactive=True, label="Top-p (nucleus sampling)", )
        temperature = gr.Slider(minimum=-0, maximum=5.0, value=1.0,
                                step=0.1, interactive=True, label="Temperature", )
        # top_k = gr.Slider( minimum=1, maximum=50, value=4, step=1, interactive=True, label="Top-k",)
        # repetition_penalty = gr.Slider( minimum=0.1, maximum=3.0, value=1.03, step=0.01, interactive=True, label="Repetition Penalty", )
    gr.Markdown(description)
    # 创建一个 Markdown 部件，用于显示聊天机器人的描述信息。

    txt.submit(predict, [txt, top_p, temperature, keyTxt,
                         chatbot, history, systemPromptTxt], [chatbot, history])
    # 将 predict 函数与 txt 部件关联，并设置 predict 函数的参数。

    txt.submit(reset_textbox, [], [txt])
    submitBtn.click(predict, [txt, top_p, temperature, keyTxt, chatbot,
                              history, systemPromptTxt], [chatbot, history], show_progress=True)
    # 将 reset_textbox 函数与 txt 部件关联，并设置参数为空。

    submitBtn.click(predict, [txt, top_p, temperature, keyTxt, chatbot, history, systemPromptTxt], [chatbot, history],
                    show_progress=True)
    # 将 predict 函数与 submitBtn 按钮关联，并设置 predict 函数的参数和输出。

    submitBtn.click(reset_textbox, [], [txt])
    emptyBtn.click(reset_state, outputs=[chatbot, history])
    retryBtn.click(predict, [txt, top_p, temperature, keyTxt, chatbot, history,
                             systemPromptTxt, TRUECOMSTANT], [chatbot, history], show_progress=True)
    delLastBtn.click(delete_last_conversation, [chatbot, history], [
        chatbot, history], show_progress=True)
    reduceTokenBtn.click(predict, [txt, top_p, temperature, keyTxt, chatbot, history,
                                   systemPromptTxt, FALSECONSTANT, TRUECOMSTANT], [chatbot, history],
                         show_progress=True)
    saveBtn.click(save_chat_history, [
        saveFileName, systemPromptTxt, history, chatbot], None, show_progress=True)
    # 将 reset_state 函数与 emptyBtn 按钮关联，并设置输出为 chatbot 和 history 部件。

    retryBtn.click(predict, [txt, top_p, temperature, keyTxt, chatbot, history, systemPromptTxt, TRUECOMSTANT],
                   [chatbot, history], show_progress=True)
    # 将 predict 函数与 retryBtn 按钮关联，并设置 predict 函数的参数和输出。

    delLastBtn.click(delete_last_conversation, [chatbot, history], [chatbot, history], show_progress=True)
    # 将 delete_last_conversation 函数与 delLastBtn 按钮关联，并设置参数和输出为 chatbot 和 history 部件。

    reduceTokenBtn.click(predict, [txt, top_p, temperature, keyTxt, chatbot, history, systemPromptTxt, FALSECONSTANT,
                                   TRUECOMSTANT], [chatbot, history], show_progress=True)
    # 将 predict 函数与 reduceTokenBtn 按钮关联，并设置 predict 函数的参数和输出。

    saveBtn.click(save_chat_history, [saveFileName, systemPromptTxt, history, chatbot], None, show_progress=True)
    # 将 save_chat_history 函数与 saveBtn 按钮关联，并设置参数和输出。

    saveBtn.click(get_history_names, None, [historyFileSelectDropdown])
    # 将 get_history_names 函数与 saveBtn 按钮关联，并设置输出为 historyFileSelectDropdown
    historyRefreshBtn.click(get_history_names, None, [historyFileSelectDropdown])
    # 当点击historyRefreshBtn按钮时，会调用名为get_history_names的函数，它将获取历史记录文件的名称，并更新historyFileSelectDropdown下拉菜单的选项。

    historyReadBtn.click(load_chat_history, [historyFileSelectDropdown],
                         [saveFileName, systemPromptTxt, history, chatbot], show_progress=True)
    # 当点击historyReadBtn按钮时，会调用名为load_chat_history的函数，它将加载所选的聊天历史记录文件，并将历史记录更新到history和chatbot变量中。还会将历史记录中的最后一个对话作为系统提示更新到systemPromptTxt中。

    templateRefreshBtn.click(get_template_names, None, [templateFileSelectDropdown])
    # 当点击templateRefreshBtn按钮时，会调用名为get_template_names的函数，它将获取模板文件的名称，并更新templateFileSelectDropdown下拉菜单的选项。

    templaeFileReadBtn.click(load_template, [templateFileSelectDropdown], [promptTemplates, templateSelectDropdown],
                             show_progress=True)
    # 当点击templaeFileReadBtn按钮时，会调用名为load_template的函数，它将加载所选的模板文件，并将模板更新到promptTemplates变量中。还会将模板的名称更新到templateSelectDropdown下拉菜单的选项中。

    templateApplyBtn.click(lambda x, y: x[y], [promptTemplates, templateSelectDropdown], [systemPromptTxt],
                           show_progress=True)

print("川虎的温馨提示：访问 http://localhost:7860 查看界面")
# 默认开启本地服务器，默认可以直接从IP访问，默认不创建公开分享链接
demo.title = "川虎ChatGPT 🚀"

# if running in Docker
if dockerflag:
    if authflag:
        demo.queue().launch(server_name="0.0.0.0", server_port=7860, auth=(username, password))
    else:
        demo.queue().launch(server_name="0.0.0.0", server_port=7860, share=False)
# if not running in Docker
else:
    demo.queue().launch(share=False)  # 改为 share=True 可以创建公开分享链接
    # demo.queue().launch(server_name="0.0.0.0", server_port=7860, share=False) # 可自定义端口
    # demo.queue().launch(server_name="0.0.0.0", server_port=7860,auth=("在这里填写用户名", "在这里填写密码")) # 可设置用户名与密码
