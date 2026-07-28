import React, { useState, useRef, useEffect } from 'react';
import './ChatPage.css';

// Troque pela URL do seu back-end quando for para produção
const API_URL = 'http://127.0.0.1:8000/perguntar';

// Gera um session_id simples e único por aba do navegador
const gerarSessionId = () => 'sess_' + Math.random().toString(36).slice(2, 11);

const ChatPage = () => {
    const [sessionId] = useState(gerarSessionId);
    const [mensagens, setMensagens] = useState([
        { autor: 'ai', texto: 'Olá! Sou o assistente da PetroMax Química. Como posso ajudar?' }
    ]);
    const [input, setInput] = useState('');
    const [carregando, setCarregando] = useState(false);
    const [erro, setErro] = useState(null);
    const fimDaListaRef = useRef(null);

    useEffect(() => {
        fimDaListaRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [mensagens]);

    const enviarMensagem = async () => {
        const texto = input.trim();
        if (!texto || carregando) return;

        setMensagens((atuais) => [...atuais, { autor: 'human', texto }]);
        setInput('');
        setErro(null);
        setCarregando(true);

        try {
            const resposta = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, mensagem: texto }),
            });

            if (!resposta.ok) {
                throw new Error(`Erro do servidor (status ${resposta.status})`);
            }

            const dados = await resposta.json();
            setMensagens((atuais) => [...atuais, { autor: 'ai', texto: dados.resposta }]);
        } catch (e) {
            setErro('Não foi possível falar com o assistente. Verifique se o servidor está rodando.');
        } finally {
            setCarregando(false);
        }
    };

    const aoPressionarTecla = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            enviarMensagem();
        }
    };

    return (
        <div className="page-container">
            <main className="main-content">
                <div className="chat-container">
                    <h1 className="chat-title">Assistente PetroMax</h1>
                    <p className="chat-subtitle">Tire suas dúvidas sobre pedidos, crédito e produtos.</p>

                    <div className="chat-window">
                        <div className="chat-messages">
                            {mensagens.map((m, i) => (
                                <div key={i} className={`chat-bubble-row ${m.autor === 'human' ? 'right' : 'left'}`}>
                                    <div className={`chat-bubble ${m.autor === 'human' ? 'chat-bubble-human' : 'chat-bubble-ai'}`}>
                                        {m.texto}
                                    </div>
                                </div>
                            ))}

                            {carregando && (
                                <div className="chat-bubble-row left">
                                    <div className="chat-bubble chat-bubble-ai chat-bubble-loading">
                                        Digitando...
                                    </div>
                                </div>
                            )}

                            <div ref={fimDaListaRef} />
                        </div>

                        {erro && <p className="chat-erro">{erro}</p>}

                        <div className="chat-input-bar">
                            <textarea
                                className="chat-input"
                                placeholder="Digite sua pergunta..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={aoPressionarTecla}
                                rows={1}
                            />
                            <button
                                className="chat-send-btn"
                                onClick={enviarMensagem}
                                disabled={carregando || !input.trim()}
                            >
                                Enviar
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default ChatPage;