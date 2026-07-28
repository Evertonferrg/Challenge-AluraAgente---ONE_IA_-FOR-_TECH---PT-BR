import React from 'react';
import './Hero.css';
import imgPlanta from '../assets/planta.png';

const Hero = () => {
    return (
        <section id="home" className="hero">
            <div className="hero-top">
                <div className="hero-content">
                    <span className="hero-eyebrow">Desde 1998 movendo a indústria química brasileira</span>
                    <h1 className="hero-title">
                        Química de precisão para quem não pode parar
                    </h1>
                    <p className="hero-text">
                        A PetroMax fornece solventes, ácidos, bases e reagentes para
                        petroquímica, agricultura e tratamento de água — com a
                        consistência de lote a lote que sua linha de produção exige.
                    </p>
                    <div className="hero-actions">
                        <a href="#produtos" className="btn-primary">Ver produtos</a>
                        <a href="#contato" className="btn-secondary">Falar com um especialista</a>
                    </div>
                </div>

                <div className="hero-media">
                    <img src={imgPlanta} alt="Planta industrial PetroMax" className="hero-image" />
                </div>
            </div>

            <div className="hero-stats">
                <div className="stat">
                    <span className="stat-number">25+</span>
                    <span className="stat-label">anos de operação</span>
                </div>
                <div className="stat">
                    <span className="stat-number">1.200+</span>
                    <span className="stat-label">clientes atendidos</span>
                </div>
                <div className="stat">
                    <span className="stat-number">100%</span>
                    <span className="stat-label">cobertura nacional</span>
                </div>
            </div>
        </section>
    );
};

export default Hero;
