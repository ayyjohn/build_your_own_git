import requests

# curl -X GET -o - https://github.com/git/git.git/info/refs?service=git-upload-pack | head -n 5
url = "https://github.com/git/git.git/info/refs?service=git-upload-pack"
# url = "https://github.com/ayyjohn/build_your_own_git.git/info/refs?service=git-receive-pack"
response = requests.get(url)
# print(response.content.decode("utf-8"))
# print(response.content)
for line in response.content.decode("utf-8").split("\n"):
    print(line)

# url = "https://github.com/ayyjohn/build_your_own_git.git/objects/00/3da8278d32b91b7485daef3346d5e0d009e1a9da0a"
# response = requests.get(url)
# print(respons.content)
