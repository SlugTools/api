# from httpx import Client
# client = Client()
# # from orjson import OPT_INDENT_2
# # print("generating test headers...", end="", flush=True)
# # test = {}
# # for i in template:
# #     if isinstance(template[i], dict):
# #         test[i] = list(template[i].keys())[0]
# #     elif isinstance(template[i], list):
# #         test[i] = template[i][0]
# #     else:
# #         test[i] = template[i]
# # with open("testing/main.json", "wb") as f:
# #     f.write(dumps(test, option=OPT_INDENT_2))
# # print("done")
# # print("converting json to form-data...", end="", flush=True)
# # s = ""
# # for i in outbound:
# #     s += f"{i}: {outbound[i]}\n"
# # with open ("testing/main.txt", "w") as f:
# #     f.write(s)
# # print("done")
