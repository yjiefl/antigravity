#!/usr/bin/env python3
import argparse
import sys

TEMPLATES = {
    "通知": """关于[事项]的通知

[主送机关]：

为了[目的/背景]，根据[依据]，现将有关事项通知如下：

一、[事项一]
[具体内容]

二、[事项二]
[具体内容]

三、[要求]
[具体要求]

特此通知。

[发文机关]
[日期]""",

    "通报": """关于[事项]的通报

[主送机关]：

[时间]，[地点/单位]发生了[事件]。[事件经过简述]。

经查，[原因/性质]。[处理决定]。

[教训/要求]。

特此通报。

[发文机关]
[日期]""",

    "请示": """关于[事项]的请示

[上级机关]：

[缘由/背景]。

[请示事项]。

妥否，请批示。

[发文机关]
[日期]""",

    "报告": """关于[事项]的报告

[上级机关]：

[导语/背景]。

一、[工作进展/成绩]
[具体内容]

二、[存在问题]
[具体内容]

三、[下一步计划]
[具体内容]

特此报告。

[发文机关]
[日期]""",

    "函": """关于[事项]的函

[受文机关]：

[缘由]。

[事项/请求]。

特此函达。

[发文机关]
[日期]""",

    "纪要": """[会议名称]会议纪要

时间：[时间]
地点：[地点]
主持人：[主持人]
参会人员：[名单]

会议听取了[内容]。会议研究了[事项]。

会议认为，[观点]。

会议决定：
一、[决定事项一]。
二、[决定事项二]。

[发文机关]
[日期]""",
    
    "批复": """关于[事项]的批复

[请示单位]：

你单位《关于[事项]的请示》（[文号]）收悉。经研究，批复如下：

一、同意[事项]。

二、[具体要求]。

此复。

[发文机关]
[日期]"""
}

def list_templates():
    print("可用公文模板类型：")
    for key in TEMPLATES.keys():
        print(f"- {key}")

def get_template(doc_type):
    return TEMPLATES.get(doc_type)

def main():
    parser = argparse.ArgumentParser(description="生成标准公文模板")
    parser.add_argument("type", nargs="?", help="公文类型 (例如: 通知, 请示, 报告)")
    parser.add_argument("--list", action="store_true", help="列出所有可用模板")
    
    args = parser.parse_args()

    if args.list:
        list_templates()
        return

    if not args.type:
        parser.print_help()
        return

    template = get_template(args.type)
    if template:
        print(template)
    else:
        print(f"错误: 找不到类型为 '{args.type}' 的模板。")
        list_templates()
        sys.exit(1)

if __name__ == "__main__":
    main()
