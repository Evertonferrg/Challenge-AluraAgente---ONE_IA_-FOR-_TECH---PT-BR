from src.tools import alterar_data_vencimento, _carregar_boletos

# BOL-00002 estava Vencido — vamos dar um novo prazo
resultado = alterar_data_vencimento("BOL-00002", "2026-09-15")
print(resultado)

# confirma no CSV
df = _carregar_boletos()
linha = df[df["id_boleto"] == "BOL-00002"]
print(linha[["id_boleto", "data_vencimento", "status"]])

# testa também uma data mal formatada, pra ver o tratamento de erro
resultado_invalido = alterar_data_vencimento("BOL-00003", "15/09/2026")
print(resultado_invalido)