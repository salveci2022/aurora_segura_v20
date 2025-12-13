# Aurora Mulher Segura — V20 (Ultra-Estável)

## Rodar no Windows (CMD)
1) Extraia o ZIP.
2) Abra o CMD dentro da pasta `aurora_segura_v20_ULTRA_ESTAVEL`
3) Instale:
   pip install -r requirements.txt
4) Rode:
   python app.py

## Links
- Mulher (Botão de Pânico): http://127.0.0.1:5000/panic
- Admin (cadastrar confiança): http://127.0.0.1:5000/panel/login
  - usuário: admin
  - senha: admin123
- Pessoa de Confiança (login): http://127.0.0.1:5000/trusted/login
- Recuperar senha (confiança): http://127.0.0.1:5000/trusted/recover
- Diagnóstico (CSS/MP3/templates/arquivos): http://127.0.0.1:5000/health

## Blindagens do V20
- /panic NÃO trava (localização opcional com timeout e fallback)
- API de alertas com ID incremental e retorno do último alerta em JSON
- Painel da confiança toca sirene apenas quando chega alerta NOVO
- Botão “Ativar som” (Chrome bloqueia autoplay)
