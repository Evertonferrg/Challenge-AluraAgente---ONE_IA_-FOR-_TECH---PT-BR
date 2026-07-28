import React from 'react';
import './Header.css';

const Header = ({ aoNavegar }) => {
    const irParaSecao = (hash) => (e) => {
        e.preventDefault();
        aoNavegar('home');
        setTimeout(() => {
            document.getElementById(hash)?.scrollIntoView({ behavior: 'smooth' });
        }, 50);
    };

    const irParaChat = (e) => {
        e.preventDefault();
        aoNavegar('chat');
    };

    return (
        <header className="header">
            <div className="logo-container">
                <a href="#home" onClick={irParaSecao('home')} className="logo-link">
                    <span className="logo-text">PetroMax <span className="logo-sub">QUÍMICA</span></span>
                </a>
            </div>
            <nav className="nav-links">
                <a href="#home" onClick={irParaSecao('home')}>Home</a>
                <a href="#sobre" onClick={irParaSecao('sobre')}>Sobre Nós</a>
                <a href="#produtos" onClick={irParaSecao('produtos')}>Produtos</a>
                <a href="#assistente" onClick={irParaChat} className="nav-cta">Assistente</a>
                <a href="#contato" onClick={irParaSecao('contato')}>Contato</a>
            </nav>
        </header>
    );
};

export default Header;