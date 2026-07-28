import React from 'react';
import './Footer.css';

const Footer = () => {
    return (
        <footer className="footer">
            <p>&copy; {new Date().getFullYear()} PetroMax Química. Todos os direitos reservados.</p>
            <p>Projeto ficticio criado acompanhado o Programa One, Tecb AI Builder.</p>
        </footer>
    );
};

export default Footer;
