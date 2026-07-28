import React, { useState } from 'react';
import './Contact.css';

const Contact = () => {
    const [form, setForm] = useState({ nome: '', email: '', mensagem: '' });
    const [enviado, setEnviado] = useState(false);

    const aoMudar = (campo) => (e) => {
        setForm((atual) => ({ ...atual, [campo]: e.target.value }));
    };

    const aoEnviar = (e) => {
        e.preventDefault();
        // Ainda sem back-end conectado para este formulário — apenas confirmação visual.
        setEnviado(true);
        setForm({ nome: '', email: '', mensagem: '' });
    };

    return (
        <section id="contato" className="contact">
            <div className="contact-info">
                <span className="section-eyebrow">Fale com a gente</span>
                <h2 className="section-title">Um especialista responde em até 1 dia útil</h2>
                <p className="section-subtitle">
                    Dúvidas sobre pedidos, crédito ou especificações técnicas? Nosso
                    assistente virtual já resolve boa parte na hora — para o resto,
                    preencha o formulário ao lado.
                </p>

                <ul className="contact-details">
                    <li><strong>Comercial:</strong> comercial@petromax.com.br</li>
                    <li><strong>Telefone:</strong> (11) 4000-0000</li>
                    <li><strong>Endereço:</strong> Distrito Industrial, Campinas – SP</li>
                </ul>
            </div>

            <form className="contact-form" onSubmit={aoEnviar}>
                <label>
                    Nome
                    <input
                        type="text"
                        value={form.nome}
                        onChange={aoMudar('nome')}
                        required
                    />
                </label>
                <label>
                    E-mail
                    <input
                        type="email"
                        value={form.email}
                        onChange={aoMudar('email')}
                        required
                    />
                </label>
                <label>
                    Mensagem
                    <textarea
                        rows={4}
                        value={form.mensagem}
                        onChange={aoMudar('mensagem')}
                        required
                    />
                </label>
                <button type="submit" className="btn-primary">Enviar mensagem</button>
                {enviado && <p className="contact-confirmacao">Recebemos sua mensagem — em breve entraremos em contato.</p>}
            </form>
        </section>
    );
};

export default Contact;
