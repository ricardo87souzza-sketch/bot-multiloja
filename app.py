from flask import Flask, request, render_template_string, jsonify
from lxml import html
import requests
import logging
import json
import os

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sua_chave_secreta_aqui_producao')

# 🔗 CONFIGURAÇÕES
MULTILOJA_URL = "https://souzaricardo.pythonanywhere.com"
BOT_TOKEN = os.environ.get('BOT_TOKEN', "6505896381:AAE2KoF7tDyYd04TjnOJRmEuVVAGNHgy_kM")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 🏪 TEMPLATES COMPLETOS
SITE_TEMPLATES = {
    "mercadolivre.com.br": {
        "name": "Mercado Livre",
        "logo": "https://i.imgur.com/gVAFRSX.png",
        "multiloja_loja": "MERCADOLIVRE",
        "link_referencia": "https://produto.mercadolivre.com.br/MLB-123456789",
        "xpaths": {
            "Sku": "",
            "Nome": "",
            "Descrição": "",
            "Preço Original": "",
            "Promo": "",
            "Link": "",
            "Imagem site": "",
            "Imagem grupo": "",
            "Categoria": "65",
            "Parcelas": "",
            "Porcentagem": "",
            "Frete": "",
            "Cupom": ""
        }
    },
    "amazon.com.br": {
        "name": "Amazon Brasil",
        "logo": "https://i.imgur.com/nQk2dGb.png",
        "multiloja_loja": "AMAZON", 
        "link_referencia": "https://www.amazon.com.br/dp/B0812461KZ",
        "xpaths": {
            "Sku": "",
            "Nome": "",
            "Preço": "",
            "Promo": "",
            "Imagem site": "",
            "Imagem grupo": "",
            "Link": "",
            "Porcentagem": "",
            "Descrição": "",
            "Categoria": "21"
        }
    },
    "shopee.com.br": {
        "name": "Shopee",
        "logo": "https://i.imgur.com/1S3dPrK.png",
        "multiloja_loja": "SHOPEE",
        "link_referencia": "https://shopee.com.br/produto/123456789",
        "xpaths": {
            "SKU": "",
            "title": "",
            "price": "",
            "Promo": "",
            "Porcentagem": "",
            "Descrição": "",
            "Imagem": "",
            "product_link": "",
            "Categoria": "68"
        }
    },
    "magazineluiza.com.br": {
        "name": "Magazine Luiza",
        "logo": "https://i.imgur.com/foTzfTy.png",
        "multiloja_loja": "MAGAZINELUIZA",
        "link_referencia": "https://www.magazineluiza.com.br/produto/123456789",
        "xpaths": {
            "Sku": "",
            "Nome": "",
            "Descrição": "",
            "Preço": "",
            "Promo": "",
            "Link": "",
            "Imagem site": "",
            "Imagem grupo": "",
            "Categoria": "32",
            "Parcelas": "",
            "Porcentagem": "",
            "Cupom": "",
            "Frete": ""
        }
    },
    "netshoes.com.br": {
        "name": "Netshoes",
        "logo": "https://i.imgur.com/99Ma9FI.png",
        "multiloja_loja": "NETSHOES",
        "link_referencia": "https://www.netshoes.com.br/produto/123456789",
        "xpaths": {
            "SKU": "//p[@class='product-reference']/text()[normalize-space() and not(contains(., 'Ref.:'))]",
            "Nome": "//h1[@data-v-24f7660e='' and @class='product-name']/text()",
            "Preço": "//span[@class='listInCents-value']/text()",
            "Promo": "//span[@class='saleInCents-value']//text()",
            "Foto site": "//img[@class='carousel-item-figure__image']/@src",
            "Porcentagem": "//div[@class='image-discount-badge__value']/text()[normalize-space() and contains(., '%')]",
            "Descrição": "//p[@class='features--description']/text()",
            "Link": "",
            "Foto grupo": "//img[@class='carousel-item-figure__image']/@src",
            "Cupom": "",
            "Categoria": "33"
        }
    }
}

# Arquivo para salvar templates
TEMPLATES_FILE = "site_templates.json"

def load_templates():
    """Carrega templates do arquivo"""
    try:
        if os.path.exists(TEMPLATES_FILE):
            with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar templates: {e}")
    return SITE_TEMPLATES

def save_templates():
    """Salva templates no arquivo"""
    try:
        with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(SITE_TEMPLATES, f, indent=2, ensure_ascii=False)
        logger.info("✅ Templates salvos com sucesso!")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao salvar templates: {e}")
        return False

# Carregar templates ao iniciar
SITE_TEMPLATES.update(load_templates())

# 🤖 FUNÇÕES DO BOT TELEGRAM 
def send_telegram_message(chat_id, text, parse_mode='HTML'):
    """Envia mensagem para o usuário no Telegram"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        logger.info(f"📤 Mensagem enviada para Telegram - Chat: {chat_id}")
        return response.json()
    except Exception as e:
        logger.error(f"❌ Erro ao enviar mensagem Telegram: {e}")
        return None

def download_html(url):
    """Versão otimizada para Railway - sem bloqueios!"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        logger.info(f"✅ HTML baixado com sucesso: {url}")
        return response.text
        
    except Exception as e:
        logger.error(f"❌ Erro ao baixar HTML: {e}")
        return None

def identify_site(url):
    """Identifica o site pelo URL"""
    for domain in SITE_TEMPLATES.keys():
        if domain in url:
            logger.info(f"🔍 Site identificado: {domain}")
            return domain
    logger.warning(f"❌ Site não identificado: {url}")
    return None

def extract_product_data(html_content, template, original_url=None):
    """Extrai dados do produto usando os XPaths do template"""
    try:
        tree = html.fromstring(html_content)
        result = {}
        
        for field, xpath in template['xpaths'].items():
            # Campos fixos (não usam XPath)
            if field == "Categoria" and xpath.isdigit():
                result[field] = xpath
                continue
            elif field == "Link" and original_url:
                result[field] = original_url
                continue
            elif field == "product_link" and original_url:
                result[field] = original_url
                continue
            elif field in ["Imagem grupo", "Foto grupo"] and template['xpaths'].get('Imagem site'):
                xpath = template['xpaths'].get('Imagem site')
            elif field in ["Imagem grupo", "Foto grupo"] and template['xpaths'].get('Foto site'):
                xpath = template['xpaths'].get('Foto site')
            
            if xpath and xpath.strip():
                try:
                    elements = tree.xpath(xpath)
                    result[field] = ' '.join([str(elem).strip() for elem in elements if str(elem).strip()]) if elements else ""
                    if result[field]:
                        logger.info(f"📊 Campo {field}: {result[field][:50]}...")
                    else:
                        logger.warning(f"⚠️ Campo {field}: Não encontrado")
                except Exception as e:
                    result[field] = f"Erro XPath: {str(e)}"
                    logger.error(f"❌ Erro XPath {field}: {e}")
            else:
                result[field] = ""
        
        return result
    except Exception as e:
        logger.error(f"❌ Erro na extração: {str(e)}")
        return {"error": f"Erro na extração: {str(e)}"}

def send_to_multiloja(loja, product_data):
    """Envia dados extraídos para o Sistema Multiloja"""
    try:
        dados_multiloja = {"loja": loja}
        
        for campo, valor in product_data.items():
            if campo in ['Sku', 'Nome', 'Descrição', 'Preço', 'Preço Original', 'Promo', 'Link', 
                        'Imagem site', 'Imagem grupo', 'Categoria', 'Parcelas', 'Porcentagem', 
                        'Frete', 'Cupom', 'SKU', 'title', 'price', 'product_link', 'Foto site', 
                        'Foto grupo']:
                dados_multiloja[campo] = valor
        
        # Garantir campos mínimos
        if not dados_multiloja.get('Nome') and not dados_multiloja.get('title'):
            dados_multiloja['Nome'] = "Produto do Telegram"
        if not dados_multiloja.get('Sku') and not dados_multiloja.get('SKU'):
            import hashlib
            sku_hash = hashlib.md5(str(dados_multiloja.get('Link', '')).encode()).hexdigest()[:8]
            dados_multiloja['Sku'] = f"TG{sku_hash}"
        
        logger.info(f"🚀 Enviando para Multiloja: {loja}")
        response = requests.post(f"{MULTILOJA_URL}/produtos", json=dados_multiloja, timeout=30)
        
        if response.status_code == 200:
            logger.info("✅ Produto enviado com sucesso para Multiloja")
            return {"success": True, "message": response.json().get('message', 'Produto adicionado com sucesso!')}
        else:
            error_msg = response.json().get('error', 'Erro desconhecido')
            logger.error(f"❌ Erro Multiloja {response.status_code}: {error_msg}")
            return {"success": False, "error": f"Erro {response.status_code}: {error_msg}"}
            
    except Exception as e:
        logger.error(f"❌ Erro de conexão com Multiloja: {str(e)}")
        return {"success": False, "error": f"Erro de conexão com Multiloja: {str(e)}"}

def process_telegram_message(message_data):
    """Processa mensagens recebidas do Telegram"""
    try:
        message = message_data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '').strip()
        
        logger.info(f"📨 Mensagem recebida - Chat: {chat_id}, Texto: {text}")
        
        if not chat_id or not text:
            logger.warning("❌ Mensagem sem chat_id ou texto")
            return
        
        # Comando /start
        if text == '/start':
            logger.info("🔄 Processando comando /start")
            welcome_msg = """
🤖 <b>BOT MULTILOJA 24/7 - HOSPEDADO NO RAILWAY</b>

🚀 <b>Agora funcionando perfeitamente!</b>

Envie o <b>link de um produto</b> das lojas abaixo:

🏪 <b>Lojas suportadas:</b>
• Mercado Livre
• Amazon Brasil  
• Shopee
• Magazine Luiza
• Netshoes

🔗 <b>Como usar:</b>
1. Copie o link do produto
2. Cole aqui no chat
3. Aguarde o processamento

⚡ <b>Pronto! O produto será adicionado automaticamente.</b>
            """
            send_telegram_message(chat_id, welcome_msg)
            return
        
        # Verificar se é uma URL
        if text.startswith('http'):
            logger.info(f"🔗 Processando URL: {text}")
            send_telegram_message(chat_id, "🔄 <b>Processando produto...</b>")
            
            # Baixar HTML
            html_content = download_html(text)
            if not html_content:
                send_telegram_message(chat_id, "❌ <b>Erro:</b> Não foi possível acessar a página")
                return
            
            # Identificar site
            domain = identify_site(text)
            if not domain:
                send_telegram_message(chat_id, "❌ <b>Site não suportado:</b> Envie links das lojas cadastradas")
                return
            
            template = SITE_TEMPLATES.get(domain)
            if not template:
                send_telegram_message(chat_id, f"❌ <b>Template não encontrado para:</b> {domain}")
                return
            
            # Extrair dados (passa o link original para campos Link)
            product_data = extract_product_data(html_content, template, text)
            if "error" in product_data:
                send_telegram_message(chat_id, f"❌ <b>Erro na extração:</b> {product_data['error']}")
                return
            
            # Enviar para Multiloja
            multiloja_result = send_to_multiloja(template['multiloja_loja'], product_data)
            
            if multiloja_result["success"]:
                success_msg = f"""
✅ <b>PRODUTO ADICIONADO!</b>

🏪 <b>Loja:</b> {template['name']}
📦 <b>Status:</b> {multiloja_result['message']}

📝 <b>Dados extraídos:</b>
• Nome: {product_data.get('Nome', product_data.get('title', 'Não encontrado'))}
• Preço: {product_data.get('Preço', product_data.get('Preço Original', product_data.get('price', 'Não encontrado')))}
• SKU: {product_data.get('Sku', product_data.get('SKU', 'Não encontrado'))}

🔗 <b>Link processado:</b> {text}
                """
            else:
                success_msg = f"""
❌ <b>ERRO NO ENVIO</b>

🔗 <b>Link:</b> {text}
⚠️ <b>Erro:</b> {multiloja_result['error']}

📝 <b>Dados extraídos:</b>
• Nome: {product_data.get('Nome', product_data.get('title', 'Não encontrado'))}
• Preço: {product_data.get('Preço', product_data.get('Preço Original', product_data.get('price', 'Não encontrado')))}
                """
            
            send_telegram_message(chat_id, success_msg)
            
        else:
            logger.info("❌ Mensagem não é uma URL")
            send_telegram_message(chat_id, "❌ <b>Envie apenas links de produtos</b>\n\nExemplo: https://www.netshoes.com.br/...")
            
    except Exception as e:
        logger.error(f"❌ ERRO NO PROCESSAMENTO: {str(e)}", exc_info=True)
        send_telegram_message(chat_id, f"❌ <b>Erro interno:</b> {str(e)}")

# 🌐 ROTAS PRINCIPAIS
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>🔗 Gerenciador XPath - Multiloja</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial; margin: 0; padding: 20px; background: #f5f5f5; line-height: 1.6; }
        .container { background: white; padding: 20px; border-radius: 10px; max-width: 1200px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        textarea, input, select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        button { background: #28a745; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; font-size: 16px; transition: background 0.3s; }
        button:hover { background: #218838; }
        .btn-save { background: #007bff; }
        .btn-save:hover { background: #0056b3; }
        .result { background: #e9f7ef; padding: 20px; margin-top: 20px; border-radius: 5px; }
        .error { background: #f8d7da; color: #721c24; }
        .success { background: #d4edda; color: #155724; }
        
        /* Sistema de Abas */
        .tabs { display: flex; margin-bottom: 20px; border-bottom: 1px solid #ddd; flex-wrap: wrap; }
        .tab { padding: 12px 20px; cursor: pointer; border: 1px solid #ddd; margin-right: 5px; border-radius: 5px 5px 0 0; background: #f8f9fa; margin-bottom: 5px; }
        .tab.active { background: #007bff; color: white; border-color: #007bff; }
        .tab-content { display: none; padding: 20px; border: 1px solid #ddd; border-radius: 0 5px 5px 5px; }
        .tab-content.active { display: block; }
        
        .xpath-field { margin-bottom: 15px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        .field-name { font-weight: bold; color: #495057; margin-bottom: 5px; }
        .field-info { font-size: 12px; color: #6c757d; margin-top: 2px; }
        
        .store-header { display: flex; align-items: center; margin-bottom: 20px; padding: 15px; background: #007bff; color: white; border-radius: 8px; }
        .store-logo { width: 50px; height: 50px; margin-right: 15px; border-radius: 5px; }
        .store-info { flex: 1; }
        
        .grid-2 { display: grid; grid-template-columns: 1fr; gap: 15px; }
        
        @media (min-width: 768px) {
            .grid-2 { grid-template-columns: 1fr 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Gerenciador XPath - Multiloja 24/7</h1>
        
        <div class="success">
            <h3>✅ SISTEMA PRONTO PARA MIGRAÇÃO!</h3>
            <p><strong>Status:</strong> 🚀 Preparado para Railway</p>
        </div>

        <!-- ABAS DAS LOJAS -->
        <div class="tabs">
            {% for domain, template in templates.items() %}
            <div class="tab {% if domain == active_tab %}active{% endif %}" 
                 onclick="openTab('{{ domain }}')">
                {% if template.logo %}
                <img src="{{ template.logo }}" alt="{{ template.name }}" style="width: 20px; height: 20px; vertical-align: middle; margin-right: 8px;">
                {% endif %}
                {{ template.name }}
            </div>
            {% endfor %}
        </div>

        <!-- CONTEÚDO DAS ABAS -->
        {% for domain, template in templates.items() %}
        <div id="{{ domain }}" class="tab-content {% if domain == active_tab %}active{% endif %}">
            <div class="store-header">
                {% if template.logo %}
                <img src="{{ template.logo }}" alt="{{ template.name }}" class="store-logo">
                {% endif %}
                <div class="store-info">
                    <h2 style="margin: 0;">{{ template.name }}</h2>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Código: {{ template.multiloja_loja }}</p>
                </div>
            </div>
            
            <form method="POST">
                <input type="hidden" name="action" value="update_template">
                <input type="hidden" name="site_domain" value="{{ domain }}">
                
                <div class="grid-2">
                    <div>
                        <label><strong>Nome da Loja:</strong></label>
                        <input type="text" name="site_name" value="{{ template.name }}">
                    </div>
                    <div>
                        <label><strong>Código Multiloja:</strong></label>
                        <input type="text" name="multiloja_loja" value="{{ template.multiloja_loja }}">
                    </div>
                </div>
                
                <label><strong>Link de Referência:</strong></label>
                <input type="text" name="link_referencia" value="{{ template.link_referencia }}">
                
                <h3>🔧 XPaths da {{ template.name }}:</h3>
                <div class="grid-2">
                    {% for field, xpath in template.xpaths.items() %}
                    <div class="xpath-field">
                        <div class="field-name">{{ field }}</div>
                        {% if field in ['Categoria'] and xpath and xpath.isdigit() %}
                        <div class="field-info">🔒 Valor fixo: {{ xpath }}</div>
                        <input type="text" name="xpath_{{ field }}" value="{{ xpath }}" readonly style="background: #e9ecef;">
                        {% elif field in ['Link', 'product_link'] %}
                        <div class="field-info">🔗 Usará link do Telegram</div>
                        <input type="text" name="xpath_{{ field }}" value="{{ xpath }}" placeholder="Deixe vazio para usar link do Telegram">
                        {% elif field in ['Imagem grupo', 'Foto grupo'] %}
                        <div class="field-info">🖼️ Usará mesmo XPath da imagem principal</div>
                        <input type="text" name="xpath_{{ field }}" value="{{ xpath }}" placeholder="Deixe vazio para usar imagem principal">
                        {% else %}
                        <input type="text" name="xpath_{{ field }}" value="{{ xpath }}" placeholder="XPath para {{ field }}">
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                
                <div style="margin-top: 20px; text-align: center;">
                    <button type="submit" class="btn-save">💾 Salvar Configurações - {{ template.name }}</button>
                </div>
            </form>
        </div>
        {% endfor %}
        
        {% if result %}
        <div class="result {% if result.error %}error{% else %}success{% endif %}">
            <h3>📊 Resultado:</h3>
            {% if result.error %}
                <p><strong>Erro:</strong> {{ result.error }}</p>
            {% else %}
                <p><strong>Sucesso!</strong> {{ result.message }}</p>
            {% endif %}
        </div>
        {% endif %}
        
        <div style="margin-top: 30px; padding: 15px; background: #e2e3e5; border-radius: 5px;">
            <h4>🚀 MIGRAÇÃO PARA RAILWAY</h4>
            <p><strong>Status:</strong> ✅ Código preparado</p>
            <p><strong>Próximo passo:</strong> Fazer deploy no Railway</p>
        </div>
    </div>

    <script>
        function openTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.currentTarget.classList.add('active');
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def home():
    logger.info("=== INICIANDO REQUISIÇÃO ===")
    result = None
    templates_saved = os.path.exists(TEMPLATES_FILE)
    active_tab = "netshoes.com.br"
    
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            site_domain = request.form.get('site_domain')
            active_tab = site_domain
            
            logger.info(f"Ação: {action} | Loja: {site_domain}")
            
            if action == 'update_template' and site_domain in SITE_TEMPLATES:
                template = SITE_TEMPLATES[site_domain]
                
                template['name'] = request.form.get('site_name', '')
                template['multiloja_loja'] = request.form.get('multiloja_loja', '')
                template['link_referencia'] = request.form.get('link_referencia', '')
                
                for field in template['xpaths'].keys():
                    form_field = f'xpath_{field}'
                    new_value = request.form.get(form_field, '')
                    logger.info(f"Campo {field}: '{new_value}'")
                    template['xpaths'][field] = new_value
                
                if save_templates():
                    result = {"success": True, "message": f"Configurações da {template['name']} salvas com sucesso!"}
                    templates_saved = True
                else:
                    result = {"error": "Falha ao salvar no arquivo"}
                    
        except Exception as e:
            logger.error(f"❌ ERRO: {str(e)}", exc_info=True)
            result = {"error": f"Erro interno: {str(e)}"}
    
    logger.info("=== FINALIZANDO REQUISIÇÃO ===")
    return render_template_string(HTML_TEMPLATE, 
                                templates=SITE_TEMPLATES,
                                active_tab=active_tab,
                                result=result,
                                templates_saved=templates_saved)

# 🤖 ROTAS DO TELEGRAM
@app.route('/webhook/' + BOT_TOKEN, methods=['POST'])
def telegram_webhook():
    """Webhook para receber mensagens do Telegram"""
    try:
        data = request.get_json()
        logger.info("=== MENSAGEM TELEGRAM RECEBIDA ===")
        
        # Processar a mensagem
        process_telegram_message(data)
        
        logger.info("=== MENSAGEM PROCESSADA ===")
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ ERRO NO WEBHOOK: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/setup_webhook', methods=['GET'])
def setup_webhook():
    """Configura o webhook automaticamente"""
    webhook_url = f"https://{request.host}/webhook/{BOT_TOKEN}"
    
    url = f"{TELEGRAM_API_URL}/setWebhook"
    payload = {
        'url': webhook_url,
        'drop_pending_updates': True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            return f"<h2>✅ Webhook Configurado!</h2><p>URL: {webhook_url}</p><a href='/'>Voltar</a>"
        else:
            return f"<h2>❌ Erro Webhook</h2><p>{result.get('description')}</p><a href='/'>Voltar</a>"
            
    except Exception as e:
        return f"<h2>❌ Erro de Conexão</h2><p>{str(e)}</p><a href='/'>Voltar</a>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
