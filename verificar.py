content = open('src/web.py', encoding='utf-8').read()
print("def home:", content.count('def home'))
print("app.mount:", content.count('app.mount'))
print('rota raiz "/":', content.count('@app.get("/"'))