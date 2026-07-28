import React from 'react';
import './About.css';
import imgTestes from '../assets/testes.png';

const valores = [
    {
        titulo: 'Segurança em primeiro lugar',
        texto: 'Todo produto sai da PetroMax com FISPQ completa e rastreabilidade de lote, do reator até a entrega.'
    },
    {
        titulo: 'Constância técnica',
        texto: 'Nossos clientes não compram apenas um insumo — compram a certeza de que o próximo lote se comporta como o anterior.'
    },
    {
        titulo: 'Compromisso ambiental',
        texto: 'Certificação ISO 14001 e investimento contínuo em tratamento de efluentes e redução de resíduos industriais.'
    }
];

const About = () => {
    return (
        <section id="sobre" className="about">
            <div className="about-intro">
                <span className="section-eyebrow">Nossa história</span>
                <h2 className="section-title">De uma planta piloto a referência nacional</h2>
                <div className="about-grid">
                    <div className="about-image-wrap">
                        <img src={imgTestes} alt="Laboratório de controle de qualidade" className="about-image" />
                    </div>
                    <div className="about-text">
                        <p>
                            A PetroMax nasceu em 1998, numa planta piloto no interior de
                            São Paulo, com uma missão simples: produzir insumos químicos
                            industriais com a mesma qualidade dos importados, a um custo
                            que a indústria brasileira pudesse sustentar.
                        </p>
                        <p>
                            Hoje, mais de duas décadas depois, atendemos petroquímicas,
                            produtores agrícolas e estações de tratamento de água em todo
                            o país, sem nunca abrir mão do que nos trouxe até aqui: rigor
                            técnico, segurança operacional e logística que chega no prazo
                            combinado.
                        </p>
                    </div>
                </div>
            </div>

            <div className="values-grid">
                {valores.map((v, i) => (
                    <div className="value-card" key={i}>
                        <h3>{v.titulo}</h3>
                        <p>{v.texto}</p>
                    </div>
                ))}
            </div>

            <div className="certifications">
                <span className="cert-badge">ISO 9001</span>
                <span className="cert-badge">ISO 14001</span>
                <span className="cert-badge">FISPQ em todos os produtos</span>
            </div>
        </section>
    );
};

export default About;
