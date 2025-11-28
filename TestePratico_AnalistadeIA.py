import requests
from datetime import datetime


# Função para limpar o CNPJ (remover pontuações, deixar em numérico, validar tamanho)
def limpar_cnpj(cnpj):
    # Remove caracteres de pontuação (pontos, barras e hifens)
    cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "")

    # Verifica se o CNPJ tem exatamente 14 dígitos após a limpeza
    if len(cnpj) != 14:
        raise ValueError("O CNPJ deve conter exatamente 14 dígitos após a remoção dos zeros iniciais.")

    # Retorna o CNPJ limpo e validado
    return cnpj


# Função para calcular anos de atividade de uma empresa
def calcular_anos(data_fundacao):
    data_atual = datetime.now().date()
    diferenca = data_atual.year - data_fundacao.year - (
            (data_atual.month, data_atual.day) < (data_fundacao.month, data_fundacao.day)
    )
    return diferenca


# Função principal para analisar o CNPJ
def analisar_cnpj(cnpj):
    # Limpa o CNPJ e monta a URL da API
    cnpj = limpar_cnpj(cnpj)
    url = f"https://open.cnpja.com/office/{cnpj}"

    try:
        # Faz a requisição para a API
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()

            # Variáveis básicas para análise
            criterios = []
            score = 0

            # === CRITÉRIOS DA ANÁLISE ===
            # 1. Status Ativo/Inativo
            status = data["status"]["text"]
            if status == "Ativa":
                criterios.append("CNPJ está ativo.")
                score += 25
            else:
                criterios.append("CNPJ está inativo ou irregular.")
                score -= 50

            # 2. Tempo de Abertura
            data_fundacao = datetime.strptime(data["founded"], "%Y-%m-%d").date()
            anos_atividade = calcular_anos(data_fundacao)
            if anos_atividade >= 3:
                criterios.append(f"Empresa com {anos_atividade} ano(s) de atividade.")
                score += 25
            else:
                criterios.append(f"Empresa com apenas {anos_atividade} ano(s) de atividade. (Alerta!)")
                score -= 25

            # 3. Capital Social
            capital_social = data["company"].get("equity")
            if capital_social is None:
                criterios.append("Capital social não informado ou ausente nos dados retornados pela API.")
                score -= 25  # Penalidade para informações incompletas
            else:
                if capital_social >= 50000:
                    criterios.append(f"Capital social adequado: R${capital_social:.2f}.")
                    score += 25
                else:
                    criterios.append(f"Capital social insuficiente: R${capital_social:.2f}.")
                    score -= 25

            # 4. Restrições Cadastrais
            restricoes = data["company"].get("suframa", [])
            if not restricoes:
                criterios.append("Sem restrições cadastrais identificadas.")
                score += 25
            else:
                criterios.append(f"Restrições identificadas: {len(restricoes)} registro(s).")
                score -= 25
            # 5. Atividade Principal Relacionada à Educação (CNAE)
            cnae_principal = data["company"].get("mainActivity", {}).get("code")  # Obtém o código CNAE principal
            cnae_educacao = [
                "8511-2/00",  # Educação infantil - creche
                "8512-1/00",  # Educação infantil - pré-escola
                "8520-1/00",  # Ensino fundamental
                "8531-7/00",  # Ensino médio
                "8541-9/00",  # Educação superior
            ]

            if cnae_principal in cnae_educacao:  # Verifica se o CNAE principal está na lista de CNAEs relacionados à educação
                criterios.append(f"CNAE principal relacionado à educação: {cnae_principal}.")
                score += 25
            else:
                criterios.append(f"CNAE principal não relacionado à educação: {cnae_principal}.")
                score -= 50  # Penalidade

            # === CLASSIFICAÇÃO FINAL ===
            if score >= 75:
                classificacao = "Aprovado"
            elif 50 <= score < 75:
                classificacao = "Atenção"
            else:
                classificacao = "Reprovado"

            # Resultado estruturado
            resultado = {
                "CNPJ analisado": cnpj,
                "Classificação": classificacao,
                "Score": score,
                "Justificativas": criterios
            }

            return resultado

        else:
            print(f"Erro ao acessar a API: Código de status {response.status_code}")
            return None

    except Exception as e:
        print(f"Erro durante a requisição: {e}")
        return None


# === EXECUÇÃO END-TO-END ===
# Solicitar o CNPJ do usuário
cnpj_input = input("Digite o CNPJ para análise: ")

# Realizar a análise
analise_resultado = analisar_cnpj(cnpj_input)

# Exibir o resultado final
if analise_resultado:
    print("\n===== RESULTADO DA ANÁLISE =====")
    print(f"CNPJ Analisado: {analise_resultado['CNPJ analisado']}")
    print(f"Classificação: {analise_resultado['Classificação']}")
    print(f"Score: {analise_resultado['Score']}")
    print("Justificativas:")
    for justificativa in analise_resultado["Justificativas"]:
        print(f"- {justificativa}")
else:
    print("\nA análise do CNPJ não pode ser concluída. Verifique o CNPJ ou tente novamente mais tarde.")
